from copy import deepcopy
import ipyvuetify as v
import pandas as pd
from threading import Thread
import time
import traitlets

from seeq import spy, sdk
from seeq.sdk.rest import ApiException


def threaded(fn):
    def wrapper(*args, **kwargs):
        thread = Thread(target=fn, args=args, kwargs=kwargs)
        thread.start()
        return thread

    return wrapper


class JobsTable(v.VuetifyTemplate):
    """
    A jobs table which represents the spy jobs associated with a datalab notebook url.

    Arguments
    ----------
    realtime_notebook_url : str
        A valid url for the notebook on which spy jobs are to be pushed and pulled.  This notebook
        should contain the code which will execute with the parameters in the spy.jobs.push dataframe.
    displayed_columns : dict
        A dictionary of key, value pairs representing the column header names (key) vs the
        data binding value (value) to be represented within the table.  For example, if the provided
        notebook has a parameter 'my_parameter', and this is to be represented in the table under a header
        title of 'My Parameters', then the key value pair would be {'My Parameters': 'my_parameter'}.
    """

    selected = traitlets.List(default=[]).tag(sync=True)
    headers = traitlets.List(default=[]).tag(sync=True)
    items = traitlets.List(default=[]).tag(sync=True)
    only_my_jobs = traitlets.Bool().tag(sync=True)
    search = traitlets.Unicode('').tag(sync=True)

    def __init__(self, realtime_notebook_url, displayed_columns=None):
        super().__init__()


        try:
            spy.jobs.pull(realtime_notebook_url, all=True)
            self.url = realtime_notebook_url
        except Exception:
            raise IOError("The provided realtime notebook url is not valid.")

        if displayed_columns is None:
            self.displayed_columns = {'Job Name': 'job_name', 'User': 'user'}
        else:
            self.displayed_columns = displayed_columns

        self.status_update_frequency = 15
        self.active_jobs = pd.DataFrame()
        self.displayed_df = pd.DataFrame()
        self.only_my_jobs = True

        self.retrieve_jobs_from_spy()
        self.update_status_indicators = True
        self.online_updates()

    @traitlets.default('template')
    def _template(self):

        return '''
        <template>
            <div>
                <v-card-title>
                  Manage
                  <v-spacer/><v-spacer/><v-spacer/>
                  <v-text-field v-model="search" append-icon="mdi-magnify" label="Search" 
                                color='green' single-line hide-details/> 
                </v-card-title>
                <div>
                    <v-data-table :v-model="selected" :show-select="false" :single-select="true" 
                    :headers="headers" :items="items" :status="status" item-key="job_name" dense="true" 
                    :search="search" hide-default-header :items-per-page="5" 
                    no-data-text="No Jobs are currently scheduled">

                       <template v-slot:header="{props:{headers}}">
                         <thead>
                           <tr>
                             <th v-for="header in headers">
                               <span>{{header.text}}</span>
                             </th>
                           </tr>
                         </thead>
                       </template>

                       <template #item.workbook="item">
                         <a :href="item.item.worksheet_url "target="_blank">
                           {{item.item.workbook_name}}
                         </a>
                       </template>

                       <template #item.action="item">
                            <span style="white-space:nowrap;">
                              <v-btn v-if="item.item.edit_permissions" icon @click="remove_job(item.item)">
                                <v-icon>delete<v-icon>
                              </v-btn>
                              <v-btn v-if="item.item.paused" icon @click="start_job(item.item)">
                                <v-icon>mdi-play-circle-outline<v-icon>
                              </v-btn>
                              <v-btn v-else icon @click="pause_job(item.item)">
                                <v-icon>mdi-pause-circle-outline<v-icon>
                              </v-btn>
                              <v-tooltip right v-if="item.item.execution_status == 'green'">
                                <template v-slot:activator="{ on }">
                                  <v-icon color='green' v-on="on">small mdi-circle</v-icon>
                                </template>
                                <span>{{item.item.execution_description}}<br/>
                                </span>
                              </v-tooltip>  

                              <v-tooltip right v-if="item.item.execution_status == 'red'">
                                <template v-slot:activator="{ on }">
                                  <v-icon color='red' v-on="on">small mdi-circle</v-icon>
                                </template>
                                <span>{{item.item.execution_description}}<br/>
                                </span>
                              </v-tooltip>

                              <v-tooltip right v-if="item.item.execution_status == 'orange'">
                                <template v-slot:activator="{ on }">
                                  <v-icon color='orange' v-on="on">small mdi-circle</v-icon>
                                </template>
                                <span>{{item.item.execution_description}}<br/>
                                </span>
                              </v-tooltip>
                            </span>
                        </template>
                        <template v-slot:footer.page-text>
                          <v-switch color = 'green' v-model='only_my_jobs' label="Only My Jobs">
                          </v-switch>
                        </template>
                </div>
            </div>
        </template>'''

    def retrieve_jobs_from_spy(self):
        self.active_jobs = spy.jobs.pull(self.url, all=True)
        items = []
        if isinstance(self.active_jobs, pd.DataFrame) and not self.active_jobs.empty:
            self.displayed_df = self.active_jobs[self.displayed_columns.values()]
            items = self.active_jobs.to_dict('records')

        if self.only_my_jobs:
            items = [item for item in items if item['user'] == f'{spy.user.first_name} {spy.user.last_name}']

        # for headers, we use only our included columns, plus the Management column for actions
        headers = list()
        for key, val in self.displayed_columns.items():
            headers.append({'text': key, 'value': val})

        headers.append({'text': 'Workbook', 'value': 'workbook'})
        headers.append({'text': 'Job Management', 'value': 'action'})

        self.headers = headers
        self.items = items
        self.update_items()

    @threaded
    def online_updates(self):
        while self.update_status_indicators:
            self.update_items()
            time.sleep(self.status_update_frequency)

    @traitlets.observe("only_my_jobs")
    def filter_update(self, _):
        self.retrieve_jobs_from_spy()

    def update_items(self):
        items = deepcopy(self.items)
        for item in items:
            job_name = item['job_name']
            workbook = item['workbook']

            status_search = spy.search(query={"Name": f'{job_name} Status'}, workbook=workbook, quiet=True)
            pulled_status = pd.DataFrame()
            formatted_last_execution = ''
            most_recent_status = ''
            try:
                now = pd.Timestamp.now(tz=spy.utils.get_user_timezone(spy._session.Session))
                if len(status_search) > 1:  # locate most recent_signal if there are naming conflicts...
                    search_df_with_ids = pd.DataFrame()
                    for unique_id in status_search['ID']:
                        search_by_id = spy.search(query={"Name": f"{job_name} Status", "ID": unique_id},
                                                  workbook=workbook, quiet=True)
                        search_df_with_ids = search_df_with_ids.append(search_by_id)
                    most_recent_signal_id = search_df_with_ids.sort_values(by=['Last Key Written']).tail(1)['ID'][0]
                    status_search = spy.search(query={"Name": f"{job_name} Status",
                                                      "ID": str(most_recent_signal_id)},
                                               workbook=workbook, quiet=True)
                if not status_search.empty:
                    pulled_status = spy.pull(status_search, start=now - pd.Timedelta('7 days'), end=now,
                                             grid=None, header='ID', quiet=True)
                    if not pulled_status.empty:
                        most_recent_status = pulled_status.iloc[-1][0]
                        formatted_last_execution = pulled_status.index[-1].strftime("%D - %H:%M:%S")
                execution_failure = False
            except Exception as e:
                execution_failure = True


            if item['Stopped']:
                item['execution_status'] = 'red'
                item['execution_description'] = 'Job Stopped.  Check Administration Panel.'
            elif execution_failure:
                item['execution_status'] = 'red'
                item['execution_description'] = f'There was an error in job scheduling.  See log for details.'
            elif status_search.empty:
                item['execution_status'] = 'orange'
                item['execution_description'] = f'Job has been scheduled but not yet executed.'
            elif pulled_status.empty:
                item['execution_status'] = 'orange'
                item['execution_description'] = f'A matching signal was found but no up to data has been pushed.'

            else:
                if most_recent_status == 'SUCCESS':
                    item['execution_status'] = 'green'
                    item['execution_description'] = f'Last Status Update : {formatted_last_execution}'
                elif most_recent_status == 'FAILURE':
                    item['execution_status'] = 'orange'
                    item['execution_description'] = 'Error - Check Executed Notebooks for details...'
                elif most_recent_status == 'PAUSED':
                    item['execution_status'] = 'orange'
                    item['execution_description'] = f'Job is Paused : {formatted_last_execution}'
                else:
                    item['execution_status'] = 'red'
                    item['execution_description'] = 'Unknown Execution Status.  Check Log Files.'

            if spy.user.is_admin or f'{spy.user.first_name} {spy.user.last_name}' == item['user']:
                item['edit_permissions'] = True
            else:
                item['edit_permissions'] = False

        self.items = items

    def vue_remove_job(self, item):
        new_df = self.active_jobs[self.active_jobs['job_name'] != item['job_name']]
        spy.jobs.push(new_df, datalab_notebook_url=self.url, quiet=True)
        self.retrieve_jobs_from_spy()

    def vue_start_job(self, item):
        new_df = deepcopy(self.active_jobs)
        new_df.loc[new_df.job_name == item['job_name'], "paused"] = False
        spy.jobs.push(new_df, datalab_notebook_url=self.url, quiet=True)
        self.retrieve_jobs_from_spy()

    def vue_pause_job(self, item):
        new_df = deepcopy(self.active_jobs)
        new_df.loc[new_df.job_name == item['job_name'], "paused"] = True
        spy.jobs.push(new_df, datalab_notebook_url=self.url, quiet=True)
        self.retrieve_jobs_from_spy()


class SchedulingUI(v.VuetifyTemplate):
    """
    An interface for scheduling new Qsearch jobs.

    Attributes
    ----------
    workbook_id : str
        ID of the current workbook in workbench.
    worksheet_id : str
        ID of the current worksheet in workbench.
    realtime_notebook_url : str
        url path to the notebook which contains the code for executing qsearch jobs.
    constant_job_parameters : dict
        additional job parameters to pass to the notebook.  This can be used to
        add logging information, constants, etc.
    """

    conditions = traitlets.List(default=[]).tag(sync=True)
    frequency = traitlets.Unicode().tag(sync=True)
    job_name = traitlets.Unicode().tag(sync=True)
    error_snackbar = traitlets.Bool().tag(sync=True)
    success_snackbar = traitlets.Bool().tag(sync=True)
    snackbar_msg = traitlets.Unicode().tag(sync=True)

    @traitlets.default('template')
    def _template(self):

        return '''
        <template>
            <v-card>
                <v-card-title>
                  Schedule
                  <v-spacer/><v-spacer/><v-spacer/><v-spacer/><v-spacer/><v-spacer/><v-spacer/><v-spacer/>
                </v-card-title>
                <v-container>
                  <v-row no-gutters justify='space-around'>
                    <v-col md="2">
                        <v-text-field v-model="job_name" label='Job Name' color='green'
                                      hint="New seeq variable to scope the resulting signals and insights.">
                        </v-text-field> 
                    </v-col>
                    <v-col md="2">
                        <v-text-field v-model="frequency" label='Frequency' color='green'
                                      hint="Frequency written in the form 'every x minutes' or 'every x hours'."></v-text-field> 
                    </v-col>
                    <v-col md="2" align-end>
                        <v-spacer/>
                        <v-btn @click='schedule_job' color=green dark absolute top>
                            <v-icon left> schedule </v-icon>
                            Schedule
                        </v-btn>       
                    </v-col>
                  </v-row> 
                </v-container>
                <v-snackbar v-model='error_snackbar' timeout='9000' color='red' absolute='true'>
                  {{snackbar_msg}}
                  <v-btn color = 'purple' flat @click="error_snackbar = false">Close</v-btn>
                </v-snackbar>
                <v-snackbar v-model='success_snackbar' timeout='4000' color='green' absolute='true'>
                  {{snackbar_msg}}
                  <v-btn color = 'purple' flat @click="success_snackbar = false">Close</v-btn>
                </v-snackbar>
            </v-card>
        </template>'''

    def __init__(self, workbook_id, worksheet_id, realtime_notebook_url, constant_job_parameters):
        super().__init__()
        self.workbook_id = workbook_id
        self.worksheet_id = worksheet_id
        self.realtime_notebook_url = realtime_notebook_url
        if constant_job_parameters is None:
            self.constant_job_parameters = dict()
        else:
            self.constant_job_parameters = constant_job_parameters
        self.submission_callbacks = list()

        self.populate_conditions()
        self.error_snackbar = False
        self.success_snackbar = False
        self.snackbar_msg = ''

        try:
            spy_version = spy.__version__
            system_api = sdk.SystemApi(spy.client)
            if int(spy_version.split('.')[0]) >= 54:
                configuration_output = system_api.get_configuration_options(limit=5000)
            else:
                configuration_output = system_api.get_configuration_options()

            self.scheduled_notebooks_enabled = next(opt.value for opt in configuration_output.configuration_options
                                                    if opt.path == 'Features/DataLab/ScheduledNotebooks/Enabled')

            self.minimum_frequency = next(opt.value for opt in configuration_output.configuration_options
                                          if opt.path == f'Features/DataLab/ScheduledNotebooks/'
                                                         f'MinimumScheduleFrequency')
        except ApiException:
            self.scheduled_notebooks_enabled = False
            self.minimum_frequency = 15

        if self.scheduled_notebooks_enabled is None:
            self.scheduled_notebooks_enabled = False

        if self.minimum_frequency is None:
            self.minimum_frequency = 15

    def populate_conditions(self):
        condition_search_results = spy.search(query={"Type": "Condition", 'Scoped To': self.workbook_id}, quiet=True)
        if not condition_search_results.empty:
            available_conditions = list(condition_search_results['Name'])
        else:
            available_conditions = list()
        conditions = ['AlwaysExecute']
        conditions.extend(available_conditions)
        self.conditions = conditions

    def vue_schedule_job(self, _):

        # Validate the job name...
        try:
            existing_jobs = spy.jobs.pull(datalab_notebook_url=self.realtime_notebook_url, all=True)
            if existing_jobs is not None and 'job_name' in existing_jobs.columns:
                duplicate_job_name = self.job_name in existing_jobs['job_name'].values
                if duplicate_job_name:
                    raise ValueError("Job Name must be unique.")
            if self.job_name == "":
                raise ValueError("A Job Name must be provided.")
        except ValueError as e:
            self.snackbar_msg = str(e)
            self.error_snackbar = True
            return

        # Validate the frequency
        try:
            valid_durations = ['hour', 'minute', 'day']

            frequency_is_parseable = type(pd.to_timedelta(
                self.frequency.lower().replace('every', ''))) == pd.Timedelta
            frequency_duration_valid = any(duration in self.frequency.lower() for duration in valid_durations)

            if not self.scheduled_notebooks_enabled:
                raise ValueError("Ensure scheduled notebooks are enabled from the admin panel and restart kernel.")

            config_delta = pd.to_timedelta(str(self.minimum_frequency) + 'minutes')
            freq_delta = pd.to_timedelta(self.frequency.lower().replace('every', ''))
            frequency_within_config = freq_delta >= config_delta

            if not frequency_is_parseable:
                raise TypeError('Frequency Error : Provide a valid cron expression, i.e. "every 30 minutes"')
            if not frequency_duration_valid:
                raise ValueError('Frequency Error : Must contain a valid duration... i.e. "every 30 minutes"')
            if not self.scheduled_notebooks_enabled:
                raise ValueError('Scheduled notebooks is not enabled from the admin panel.  Enable and retry.')
            if not frequency_within_config:
                raise ValueError(f'Frequency Error : Minimum configured frequency from '
                                 f'admin panel is {config_delta} minutes.  Frequency must be exceed this.')
            if 'every' not in self.frequency.lower():
                raise TypeError('Frequency Error : Begin with "every" followed by a duration... i.e. "every 1 hour"')

        except Exception as e:
            self.snackbar_msg = str(e)
            self.error_snackbar = True
            return

        try:
            server_name = spy.utils.get_data_lab_project_url().split('data-lab')[0]
            worksheet_url = f'{server_name}workbook/{self.workbook_id}/worksheet/{self.worksheet_id}'
            workbook_name = spy.workbooks.search({"ID": self.workbook_id}, quiet=True)['Name'].iloc[0]

            job_parameters = {'Schedule': [self.frequency], 'frequency': [self.frequency],
                              'user': [f'{spy.user.first_name} {spy.user.last_name}'],
                              'workbook_name': [workbook_name], 'worksheet_url': [worksheet_url],
                              'workbook': [self.workbook_id],
                              'paused': [False], 'job_name': [self.job_name]
                              }


            job_parameters.update(self.constant_job_parameters)
        except Exception as e:
            self.snackbar_msg = str(e)
            self.error_snackbar = True
            return

        # if job_parameters['model'][0] == 'None':
        #    self.snackbar_msg = 'Select a model to schedule.'
        #    self.error_snackbar = True
        #    return

        existing_jobs = spy.jobs.pull(datalab_notebook_url=self.realtime_notebook_url, all=True)
        if existing_jobs is None:
            updated_jobs = pd.DataFrame(job_parameters)
        else:
            updated_jobs = existing_jobs.append(pd.DataFrame(job_parameters), ignore_index=True, verify_integrity=True)

        try:
            spy.jobs.push(updated_jobs, datalab_notebook_url=self.realtime_notebook_url, quiet=True)
            self.snackbar_msg = f'Job "{self.job_name}" has been successfully ' \
                                f'scheduled and will appear green after first execution.'
            self.success_snackbar = True
            self.job_name = ''
            self.frequency = ''
            for submission_callback in self.submission_callbacks:
                submission_callback()
        except Exception as e:
            if 'may execute more often than the minimum schedule frequency' in str(e):
                self.snackbar_msg = f'For jobs scheduled with a frequency less than 1 hour, there is a special rule ' \
                                    f'to be followed.  The remainder of 60 divided by the job frequency must either ' \
                                    f'be greater than the minimum frequency, or be 0.  For example, if the minimum ' \
                                    f'scheduled frequency is 15 minutes, then 16 minutes is invalid since ' \
                                    f'60%16 = 12, which is less than 15 minutes.  On the other hand every 20 minutes' \
                                    f'is acceptable, since 60%20 is 0.'
            else:
                self.snackbar_msg = str(e)
            self.error_snackbar = True
            return

    def add_submit_callback(self, callback_function):
        self.submission_callbacks.append(callback_function)