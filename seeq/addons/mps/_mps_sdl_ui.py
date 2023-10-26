from IPython.display import clear_output
from IPython.display import display
from datetime import datetime, timedelta
import pytz
import ipywidgets as ipw

import pandas as pd

from seeq import spy, sdk
import json

from os import listdir, path, makedirs
from os.path import isfile, join

from . import _mps as mps


class MpsUI(ipw.VBox):
    """
    This Class creates an ipywidget based user interface for the MPS Add-on, it contains the options required to
    complete a continuous or batch mode mps analysis. Results are pushed to the workbook the Add-on was launched from
    or the specified workbook if running locally.

    """

    def __init__(self, server, workbook_id, worksheet_id):

        # self._user_timezone = _utils.get_user_timezone()
        self.server = server
        self.workbook_id = workbook_id
        self.worksheet_id = worksheet_id

        # Set the compatibility option so that you maximize the chance that SPy will remain compatible with your notebook/script
        spy.options.compatibility = 187.5

        max_name = 0

        # get name to push
        try:
            t_ = spy.search({'Name': 'MPS Analysis ', },
                            workbook=workbook_id,
                            quiet=True)

            t_ = t_[t_["Type"] == 'StoredSignal']
            t_list = t_.Name.to_list()
            t_list = [i.replace('MPS Analysis ', "") for i in t_list]
            t_list = [i.replace('_Dissimilarity_measure', "") for i in t_list]

            for i in t_list:
                try:
                    int(i)
                    if int(i) > max_name:
                        max_name = int(i)
                except:
                    pass
        except:
            pass
        self.output = ipw.Output()
        self.found_cap_name_ = ipw.Text(
            value='MPS Analysis ' + str(max_name + 1),
            placeholder='MPS Analysis ' + str(max_name + 1),
            description='Result Name',
            disabled=False
        )

        self.url = ipw.Text(
            value='',
            placeholder='',
            description='WB URL',
            disabled=False
        )

        self.get_meta = ipw.Button(description="Connect to workbook")
        text_title = 'Multivariate Pattern Search'
        self.title_ = ipw.HTML(value = f"<b><font color='green'><font size=5>{text_title}</b>")


        self.find__ = ipw.HBox([ipw.Label(value="")])

        self.find_sig_ = ipw.HBox([ipw.Label(value="Select Signals to be used in analysis")])

        self.signals_ = ipw.Dropdown(
            options=[' '],
            value=' ',
            description='Signal_1:',
            disabled=False,
        )

        self.add_sig_ = ipw.Button(description="Signal", disabled=False, icon='plus', layout=ipw.Layout(left='150px'))

        self.remove_sig_ = ipw.Button(description="Signal", disabled=True, icon='minus',
                                      layout=ipw.Layout(left='150px'))

        self.all_sig_ = ipw.Button(description="Add All Signals", disabled=False, layout=ipw.Layout(width='150px'))

        self.time_title = ipw.HBox(
            [ipw.Label(value="2. Time Frame of search default set to workbook investigation range")])

        self.time_frame1 = ipw.DatePicker(
            description='Start',
            layout=ipw.Layout(width='250px'),
            disabled=False
        )

        self.time_frame2 = ipw.DatePicker(
            description='End',
            layout=ipw.Layout(width='250px'),
            disabled=False
        )

        self.Algo_ = ipw.HBox([ipw.Label(value="Select important characteristics")])

        self.data_type_ = ipw.HBox([ipw.Label(value="Batch or continuous data")])

        self.time_title = ipw.Label(value="Find shorter/longer capsules?")

        self.Shape_ = ipw.Checkbox(value=False,
                                   description='Shape of Signal',
                                   disabled=False,
                                   indent=True
                                   )
        self.Level_ = ipw.Checkbox(value=False,
                                   description='Level of Signal',
                                   disabled=False,
                                   indent=True
                                   )

        self.known_cap_ = ipw.Dropdown(
            options=[' '],
            value=' ',
            description='Condition:',
            disabled=False,
        )

        self.second_res = ipw.SelectionSlider(options=['1sec', '10sec', '30sec', '1min', '5min', '10min', '30min'],
                                              value='1min',
                                              description='Griding:',
                                              disabled=False,
                                              continuous_update=False,
                                              orientation='horizontal',
                                              readout=True
                                              )

        self.dissim_ = ipw.Checkbox(
            value=False,
            description='Return dis-similar results',
            disabled=False,
            indent=True
        )

        self.similarity_ = ipw.FloatSlider(
            value=0.9,
            min=0,
            max=1,
            step=0.02,
            description='Threshold %',
            disabled=False,
            continuous_update=False,
            orientation='horizontal',
            readout=True,
            readout_format='.0%',
        )

        self.time_distort_ = ipw.HBox([ipw.FloatSlider(
            value=0.02,
            min=0,
            max=0.1,
            step=0.01,
            description='Low',
            disabled=False,
            continuous_update=False,
            orientation='horizontal',
            readout=False,
            layout=ipw.Layout(width='250px')
        ),
            ipw.Label(value="High delta")])

        self.batch_cap_ = ipw.Dropdown(
            options=[' '],
            value=' ',
            description='Condition:',
            disabled=False,
        )

        self.return_all_ = ipw.Button(
            description='All',
            tooltip='Click me to set app to return all results',
            layout=ipw.Layout(width='50px'),
            disabled=False
        )
        self.return_top_x_ = ipw.Text(
            value='10',
            placeholder='',
            description='# of capsules:',
            disabled=False,
            layout=ipw.Layout(width='250px')
        )

        self.return_ = ipw.HBox([self.return_top_x_, self.return_all_])

        self.start_hour = ipw.Dropdown(
            options=["00", "01", "02", "03", "04", "05", "06", "07", "08", "09", "10", "11", '12', '13', '14', '15',
                     '16', '17', '18', '19', '20', '21', '22', '23', '24'],
            value='00',
            layout=ipw.Layout(width='47px'),
            disabled=False,
        )

        self.start_min = ipw.Dropdown(
            options=['00', '10', '20', '30', '40', '50'],
            value='00',
            layout=ipw.Layout(width='47px'),
            disabled=False,
        )

        self.end_hour = ipw.Dropdown(
            options=["00", "01", "02", "03", "04", "05", "06", "07", "08", "09", "10", "11", '12', '13', '14', '15',
                     '16', '17', '18', '19', '20', '21', '22', '23', '24'],
            value='00',
            layout=ipw.Layout(width='47px'),
            disabled=False,
        )

        self.end_min = ipw.Dropdown(
            options=['00', '10', '20', '30', '40', '50'],
            value='00',
            layout=ipw.Layout(width='47px'),
            disabled=False,
        )

        self.time_title_ = ipw.HBox([ipw.Label(value="", layout=ipw.Layout(width='150px')),
                                     ipw.Label(value="Date", layout=ipw.Layout(width='100px')),
                                     ipw.Label(value="hr", layout=ipw.Layout(width='50px')),
                                     ipw.Label(value="min", layout=ipw.Layout(width='50px'))])

        self.start_hrmin = ipw.HBox([self.time_frame1, self.start_hour, self.start_min])
        self.end_hrmin = ipw.HBox([self.time_frame2, self.end_hour, self.end_min])

        self.button = ipw.Button(description="Execute", layout=ipw.Layout(left='200px'), disabled=True)

        # get meta data to populate widgets
        try:
            self.condition_list, self.signal_list, self.sheet_start, self.sheet_end, self.sheet_index = \
                self.get_worksheet_data(
                    self.workbook_id,
                    self.worksheet_id)
            nodata_ = False
        except:
            Error_msg = "Error: Please ensure the analysis worksheet has at least one numerical signal and one " \
                        "condition, Or check your version of Seeq server matches the installed version of seeq module "\
                        "(spy)"
            self.display_list = [ipw.HTML(value=f"<b><font color='red'><font size=4>{Error_msg}</b>")]

            super().__init__(self.display_list)

            nodata_ = True

        if not nodata_:

            self.known_cap_.options = self.condition_list
            self.batch_cap_.options = self.condition_list
            self.time_frame1.value = datetime.strptime(str(self.sheet_start)[:10], '%Y-%m-%d')
            self.time_frame2.value = datetime.strptime(str(self.sheet_end)[:10], '%Y-%m-%d')

            self.start_hour.value = str(self.sheet_start)[11:13]
            if round(int(str(self.sheet_start)[14:16]) / 10) * 10 == 60:
                self.start_min.value = "50"
            elif round(int(str(self.sheet_start)[14:16]) / 10) * 10 == 0:
                self.start_min.value = "00"
            else:
                self.start_min.value = str(round(int(str(self.sheet_start)[14:16]) / 10) * 10)

                self.end_hour.value = str(self.sheet_end)[11:13]
            if round(int(str(self.sheet_end)[14:16]) / 10) * 10 == 60:
                self.end_min.value = "50"
            elif round(int(str(self.sheet_end)[14:16]) / 10) * 10 == 0:
                self.end_min.value = "00"
            else:
                self.end_min.value = str(round(int(str(self.sheet_end)[14:16]) / 10) * 10)

            self.signals_.options = [""] + self.signal_list

            self.mypath = 'References'
            if not path.exists(self.mypath):
                makedirs(self.mypath)

            self.files_ = [f[:-4] for f in listdir(self.mypath) if isfile(join(self.mypath, f))]

            self.pick_load_file_ = ipw.Dropdown(
                options=[' '] + self.files_,
                value=' ',
                description='Select file:',
                disabled=False,
            )

            self.save_name = ipw.Text(
                value='',
                placeholder='',
                description='Save name',
                disabled=False
            )

            self.load_button_ = ipw.Button(description="Load", layout=ipw.Layout(left='150px'))

            self.save_button_ = ipw.Button(description="save", layout=ipw.Layout(left='150px'))

            self.select_dropdown = ipw.Accordion(children=[
                ipw.VBox([self.known_cap_, self.find_sig_, self.all_sig_, self.signals_, self.add_sig_, self.remove_sig_
                          ])
            ],
                selected_index=0,
                layout=ipw.Layout(width='370px'))

            self.select_dropdown.set_title(0, "Select condition within investigation range")

            self.load_save_dropdown = ipw.Accordion(children=[
                ipw.VBox([self.save_name,
                          self.save_button_
                          ]),
                ipw.VBox([self.pick_load_file_,
                          self.load_button_
                          ])
            ],
                selected_index=None,
                layout=ipw.Layout(width='370px'))

            self.load_save_dropdown.set_title(0, "Save reference")
            self.load_save_dropdown.set_title(1, "Load reference")
            self.items_s_ref = None
            self.data_pull_known = None
            self.time_dropdown = ipw.Accordion(
                children=[ipw.VBox([self.time_title_, self.start_hrmin, self.end_hrmin, self.second_res
                                    ])],
                selected_index=None,
                layout=ipw.Layout(width='370px'))

            self.time_dropdown.set_title(0, "Select Analysis timeframe")

            self.adv_dropdown = ipw.Accordion(
                children=[ipw.VBox([self.Algo_, self.Shape_, self.Level_, self.time_title, self.time_distort_,
                                    ])],
                selected_index=None,
                layout=ipw.Layout(width='370px'))

            self.adv_dropdown.set_title(0, "Advanced Options")

            self.batch_text = ipw.HBox([ipw.Label(value="Please select batch condition", layout=ipw.Layout(left='11px'))])

            self.batch_data = ipw.Button(description="Batch")
            self.cont_data = ipw.Button(description="Continuous")
            self.space_ = ipw.HBox([ipw.Label(value="                    ")])

            self.bat_con_select = ipw.VBox([
                                    ipw.HBox([self.batch_data, self.cont_data]),
                                    self.space_
                                            ])

            self.load_ref_ = ipw.Button(description="Review Ref", layout=ipw.Layout(left='150px'))
            self.ref_title2_ = ipw.HBox([ipw.Label(value="Select the corresponding signals to match reference")])



            self.display_list = [self.title_, self.found_cap_name_, self.find__, self.select_dropdown,
                                 self.load_save_dropdown,
                                 self.data_type_, self.bat_con_select, self.space_,
                                 self.time_dropdown,
                                 self.adv_dropdown,
                                 self.space_, self.button
                                 ]

            super().__init__(self.display_list)

            self.return_all_.on_click(self.return_all)
            self.save_button_.on_click(self.save)
            self.load_button_.on_click(self.load_ref)
            self.load_ref_.on_click(self.review_ref)
            self.button.on_click(self.on_button_clicked2)
            self.all_sig_.on_click(self.add_all_sig)
            self.batch_data.on_click(self.bat_data_push)
            self.cont_data.on_click(self.cont_data_push)
            self.remove_sig_.on_click(self.remove_sig_select)
            self.add_sig_.on_click(self.new_sig_select)

    # action on click of execute MPS: Pull data to pandas, run MASS, push found conditions back to worksheet
    def on_button_clicked2(self, b):

        users_api = sdk.UsersApi(spy.client)
        me = users_api.get_me()
        stores = json.loads(me.workbench)
        lz_ = stores['state']['stores']['sqWorkbenchStore']['userTimeZone']

        self.button.description = "Pulling data..."
        self.button.button_style = 'warning'
        if self.load_button_.button_style == 'success':
            load_name = self.pick_load_file_.value
            self.items_s_ref, self.data_pull_known = mps.load_ref(load_name, self.mypath)
        else:

            time_frame = [datetime.strptime(
                str(self.time_frame1.value)[:10] + " " + self.start_hour.value + ":" + self.start_min.value,
                '%Y-%m-%d %H:%M').replace(tzinfo=pytz.timezone(lz_)),
                          datetime.strptime(
                              str(self.time_frame2.value)[:10] + " " + self.end_hour.value + ":" + self.end_min.value,
                              '%Y-%m-%d %H:%M').replace(tzinfo=pytz.timezone(lz_))]

            time_frame = [time_frame[0].astimezone(pytz.timezone("UTC")),
                          time_frame[1].astimezone(pytz.timezone("UTC"))]

            known_cap = str(self.known_cap_.value)
            griding = self.second_res.value

            signal_pull_list = []
            if self.display_list[3].children[0].children[2].description == "UNDO add all":
                signal_pull_list = self.signal_list

            else:
                for s in range(len(self.display_list[3].children[0].children) - 5):
                    signal_pull_list = signal_pull_list + [self.display_list[3].children[0].children[3 + s].value]

            desired_workbook, sheet_index = mps.gather_workbook_worksheet_meta_data(self.workbook_id, self.worksheet_id)

            items = desired_workbook[0].worksheets[sheet_index].display_items
            items_s = items[items.Type == 'Signal']
            self.items_s_ref = items_s[items_s['Name'].isin(signal_pull_list)]

            items_c = items[items.Type == 'Condition']
            items_c = items_c[items_c.Name == known_cap]
            self.data_pull_known = spy.pull(items_c, start=time_frame[0], end=time_frame[1], quiet=True, grid=griding)

        time_frame = [datetime.strptime(
            str(self.time_frame1.value)[:10] + " " + self.start_hour.value + ":" + self.start_min.value,
            '%Y-%m-%d %H:%M').replace(tzinfo=pytz.timezone(lz_)),
                      datetime.strptime(
                          str(self.time_frame2.value)[:10] + " " + self.end_hour.value + ":" + self.end_min.value,
                          '%Y-%m-%d %H:%M').replace(tzinfo=pytz.timezone(lz_))]
        time_frame = [time_frame[0].astimezone(pytz.timezone("UTC")), time_frame[1].astimezone(pytz.timezone("UTC"))]

        # normalise = normalise_.value
        sim = not self.dissim_.value
        similarity = self.similarity_.value
        time_distort = self.time_distort_.children[0].value

        griding = self.second_res.value
        if self.return_all_.button_style == 'info':
            return_top_x = 1000
        else:
            return_top_x = int(self.return_top_x_.value)

        found_cap_name = str(self.found_cap_name_.value)
        known_cap = str(self.known_cap_.value)
        batch_cond = str(self.batch_cap_.value)

        signal_pull_list = []

        if self.load_button_.button_style == 'success' and not self.save_button_.button_style == 'success':
            for i in range(len(self.display_list[3].children[0].children) - 2):
                signal_pull_list = signal_pull_list + [
                    self.display_list[3].children[0].children[2 + i].children[1].value]
        else:
            for s in range(len(self.display_list[3].children[0].children) - 5):
                signal_pull_list = signal_pull_list + [self.display_list[3].children[0].children[3 + s].value]

        data_pull, data_pull_c, sheet_index = mps.pull_mps_data(self.workbook_id,
                                                                self.worksheet_id,
                                                                signal_pull_list,
                                                                self.items_s_ref,
                                                                self.data_pull_known,
                                                                time_frame,
                                                                griding)

        self.button.description = "MPS Calculating..."

        # Capture all in if batch and cont

        if self.batch_data.button_style == 'info':

            desired_workbook = spy.workbooks.pull(spy.workbooks.search({'ID': self.workbook_id},
                                                                       include_referenced_workbooks=False,
                                                                       include_inventory=False,
                                                                       quiet=True, errors='catalog'
                                                                       ),
                                                  include_referenced_workbooks=False,
                                                  quiet=True
                                                  )

            items = desired_workbook[0].worksheets[sheet_index].display_items
            items_c = items[items.Type == 'Condition']
            items_c = items_c[items_c.Name == batch_cond]
            batch_cond = spy.pull(items_c, start=time_frame[0], end=time_frame[1], quiet=True, grid=griding)
            time_distort = 0.04

            Batch_sim_df = mps.seeq_mps_dtw_batch(batch_cond, data_pull, data_pull_c, self.data_pull_known,
                                                  True, time_distort)

            self.button.description = "Pushing results..."
            end = mps.push_mps_results_batch(Batch_sim_df, self.workbook_id, found_cap_name, sheet_index)

            self.button.button_style = 'success'
            self.button.description = "Success!"

        else:

            if self.Shape_.value and self.Level_.value:

                min_idx_multivar = mps.seeq_mps_mass(data_pull,
                                                     data_pull_c,
                                                     self.data_pull_known,
                                                     similarity,
                                                     True,
                                                     sim
                                                     )

            elif self.Level_.value:
                min_idx_multivar = mps.seeq_mps_dtw(data_pull,
                                                    data_pull_c,
                                                    self.data_pull_known,
                                                    similarity,
                                                    False,
                                                    sim,
                                                    time_distort
                                                    )
            elif self.Shape_.value:
                min_idx_multivar = mps.seeq_mps_mass(data_pull,
                                                     data_pull_c,
                                                     self.data_pull_known,
                                                     similarity,
                                                     False,
                                                     sim
                                                     )
            else:
                min_idx_multivar = mps.seeq_mps_dtw(data_pull,
                                                    data_pull_c,
                                                    self.data_pull_known,
                                                    similarity,
                                                    True,
                                                    sim,
                                                    time_distort
                                                    )

            self.button.description = "Pushing results..."

            end = mps.push_mps_results(return_top_x,
                                       min_idx_multivar,
                                       data_pull,
                                       self.workbook_id,
                                       found_cap_name,
                                       sheet_index,
                                       griding
                                       )

            if end:
                self.button.button_style = 'success'
                self.button.description = "Success!"

            self.button.button_style = 'success'
            self.button.description = "Success!"

    def get_worksheet_data(self, workbook_id, worksheet_id):

        """
        This function obtains worksheet information used to pre-populate options within the user interface. This
        includes lists of conditions and signals, investigation start and end datetime and index of the worksheet.

        Parameters
        ----------
        workbook_id : str
            The Seeq ID of the source workbook
        worksheet_id: str
            The Seeq ID of the source worksheet


        Returns
        -------
        condition_list: list of str
            List of names of all conditions found in the source worksheet
        signal_list: list of str
            List of names of all signals found in the source worksheet
        sheet_start: datetime
            datetime of the start of the investigation range from the source worksheet
        sheet_end: datetime
            datetime of the end of the investigation range from the source worksheet
        sheet_index: int
            integer detailing the index of the source worksheet

        """

        users_api = sdk.UsersApi(spy.client)
        me = users_api.get_me()
        stores = json.loads(me.workbench)
        lz_ = stores['state']['stores']['sqWorkbenchStore']['userTimeZone']

        spy_search = spy.workbooks.search({'ID': workbook_id},
                                          quiet=True
                                          )

        desired_workbook = spy.workbooks.pull(spy_search,
                                              include_referenced_workbooks=False, include_inventory=False,
                                              quiet=True, errors='catalog'
                                              )

        # find worksheet index from url
        # find worksheet index
        count = 0
        try:
            sheet_list = desired_workbook[0].worksheets
            sheet_index = [i for i, s in enumerate(sheet_list) if worksheet_id in str(s)][0]
            sheet_start = desired_workbook[0].worksheets[sheet_index].display_range['Start'].astimezone(
                pytz.timezone(lz_))
            sheet_end = desired_workbook[0].worksheets[sheet_index].display_range['End'].astimezone(
                pytz.timezone(lz_))
            count += 1
        except:
            print('ERROR = Could not find worksheet: ' + str(worksheet_id))

        # define items in sheet
        items = desired_workbook[0].worksheets[sheet_index].display_items

        try:
            items_c = items[items.Type == 'Condition']
            condition_list = items_c.Name.to_list()
            count += 1
        except:
            print('ERROR = Could not find any Conditions')

        try:
            items_s = items[items.Type == 'Signal']
            signal_list = items_s.Name.to_list()
            count += 1
        except:
            print('ERROR = Could not find any signals')

        try:
            tf1 = desired_workbook[0].worksheets[sheet_index].display_range['Start']
            tf2 = tf1 + timedelta(minutes=30)
            items = desired_workbook[0].worksheets[sheet_index].display_items
            items_s = items[items.Type == 'Signal']
            items_s = items_s[items_s['Name'].isin(signal_list)]

            data_pull = spy.pull(items_s, start=tf1, end=tf2, quiet=True)
            count += 1

            for c in data_pull.columns:
                if 'float64' != data_pull.dtypes[c]:
                    try:
                        signal_list.remove(c)
                    except:
                        pass
        except:
            pass

        if count == 4:
            return condition_list, signal_list, sheet_start, sheet_end, sheet_index

    def review_ref(self, b):

        self.load_ref_.description = "Working.."
        self.load_ref_.button_style = 'warning'

        load_name = self.pick_load_file_.value
        load_sheet_name = str(load_name) + ' reference review ' + str(datetime.now().strftime("%d/%m/%Y %H:%M:%S"))
        items_s_ref, data_pull_known = mps.load_ref(load_name, self.mypath)
        condition_name2 = data_pull_known['Condition'].values[0]

        push_ref_cap = spy.push(data=data_pull_known,
                                metadata=pd.DataFrame([{'Name': condition_name2,
                                                        'Type': 'Condition',
                                                        'Maximum Duration': '20d'
                                                        }]),
                                workbook=self.workbook_id,
                                worksheet=load_sheet_name,
                                quiet=True
                                )

        workbook = spy.workbooks.pull(spy.workbooks.search({'ID': self.workbook_id},
                                                           include_referenced_workbooks=False, include_inventory=False,
                                                           quiet=True, errors='catalog'
                                                           ),
                                      include_referenced_workbooks=False,
                                      quiet=True
                                      )
        sheet_index_ = \
            [i for i, s in enumerate(workbook[0].worksheets) if load_sheet_name in str(s)][0]

        worksheet = workbook[0].worksheets[sheet_index_]

        new_display_items_ = pd.concat([push_ref_cap, items_s_ref], axis=0, sort=True)
        new_display_items_.reset_index(drop=True, inplace=True)
        worksheet.display_items = new_display_items_

        new_worksheet_start = worksheet.display_range['Start'] - 3 * (
                worksheet.display_range['End'] - worksheet.display_range['Start'])
        new_worksheet_end = worksheet.display_range['End'] + 3 * (
                worksheet.display_range['End'] - worksheet.display_range['Start'])

        worksheet.investigate_range = pd.DataFrame.from_dict(
            {'Start': [new_worksheet_start], 'End': [new_worksheet_end]})
        worksheet.display_range = pd.DataFrame.from_dict({'Start': [new_worksheet_start], 'End': [new_worksheet_end]})

        spy.workbooks.push(workbook, quiet=True)

        self.load_ref_.description = "link below"
        self.load_ref_.button_style = 'success'
        self.load_ref_.disabled = True
        link_title = 'Worksheet added to analysis workbook for review'
        link_widget = ipw.HTML(f"<b><font color='blue'><font size=2>{link_title}</b>")

        self.display_list[4].children[1].children = self.display_list[4].children[1].children[:] + (link_widget,)

        clear_output()

        display(ipw.VBox(self.display_list))

    def load_ref(self, b):

        self.load_button_.description = "Loading.."
        self.load_button_.button_style = 'warning'

        self.pick_load_file_.disabled = True
        self.load_button_.description = "Loaded!"
        self.load_button_.button_style = 'success'
        self.load_button_.disabled = True

        # display of loaded refs and prompt selection of corresponding signals

        load_name = self.pick_load_file_.value
        items_s_ref, data_pull_known = mps.load_ref(load_name, self.mypath)

        ref_signals = items_s_ref["Name"].to_list()

        load_sig_count = 0

        self.display_list[4].children[1].children = self.display_list[4].children[1].children[:2] + (self.load_ref_,)

        for s in ref_signals:

            if s in self.signal_list:
                dropdown_value_ = s
            else:
                dropdown_value_ = [""]
            load_sig_count += 1

            self.display_list[3].children[0].children = self.display_list[3].children[0].children[
                                                        :2 + (load_sig_count - 1) * 2] + \
                                                        (ipw.Box([
                                                            ipw.HTML(value="<b>" + str(s) + "</b>", tooltips=[s]),
                                                            ipw.Dropdown(
                                                                options=[""] + self.signal_list,
                                                                value=dropdown_value_,
                                                                description='Signal_' + str(load_sig_count) + ':',
                                                                disabled=False,
                                                            )
                                                        ], layout=ipw.Layout(display='flex',
                                                                             flex_flow='column',
                                                                             align_items='stretch'
                                                                             # justify_content='space-between'
                                                                             )
                                                        ),
                                                        )

        self.display_list[3].children[0].children = self.display_list[3].children[0].children[:1] + (self.ref_title2_,)\
                                                    + self.display_list[3].children[0].children[2:]
        self.button.disabled = False

        clear_output()

        display(ipw.VBox(self.display_list))

    def save(self, b):

        users_api = sdk.UsersApi(spy.client)
        me = users_api.get_me()
        stores = json.loads(me.workbench)
        lz_ = stores['state']['stores']['sqWorkbenchStore']['userTimeZone']

        time_frame = [datetime.strptime(
            str(self.time_frame1.value)[:10] + " " + self.start_hour.value + ":" + self.start_min.value,
            '%Y-%m-%d %H:%M').replace(tzinfo=pytz.timezone(lz_)),
                      datetime.strptime(
                          str(self.time_frame2.value)[:10] + " " + self.end_hour.value + ":" + self.end_min.value,
                          '%Y-%m-%d %H:%M').replace(tzinfo=pytz.timezone(lz_))]

        time_frame = [time_frame[0].astimezone(pytz.timezone("UTC")), time_frame[1].astimezone(pytz.timezone("UTC"))]
        known_cap = str(self.known_cap_.value)
        griding = self.second_res.value

        signal_pull_list = []
        if self.display_list[3].children[0].children[2].description == "UNDO add all":
            signal_pull_list = self.signal_list

        else:
            for s in range(len(self.display_list[3].children[0].children) - 5):
                signal_pull_list = signal_pull_list + [self.display_list[3].children[0].children[3 + s].value]

        file_save_name = self.display_list[4].children[0].children[0].value

        if file_save_name == ' ':
            print("Please name save file")
        elif file_save_name in self.files_:
            print('file with this name already exists')
        else:
            self.save_button_.description = "Saving..."
            self.save_button_.button_style = 'warning'
            mps.save_ref(self.workbook_id, self.worksheet_id, signal_pull_list, known_cap, time_frame,
                         griding, file_save_name, self.mypath)
            self.save_button_.description = "Saved!"
            self.save_button_.button_style = 'success'

            self.pick_load_file_.options = [file_save_name]
            self.pick_load_file_.value = file_save_name
            self.pick_load_file_.disabled = True
            self.load_button_.description = "Loaded!"
            self.load_button_.button_style = 'success'
            self.load_button_.disabled = True

        self.button.disabled = False

    def add_all_sig(self, b):

        if self.all_sig_.description == "UNDO add all":
            location = [i for i, n in enumerate(self.display_list[3].children[0].children) if n == self.remove_sig_][0]

            self.display_list[3].children[0].children = self.display_list[3].children[0].children[:4] + \
                                                        self.display_list[3].children[0].children[location - 1:]
            self.all_sig_.description = "Add All Signals"

        else:
            self.all_sig_.description = "UNDO add all"
            self.remove_sig_.disabled = False
            temp_sl = [''] + self.signal_list
            for s in self.signal_list:

                location = [i for i, n in enumerate(self.display_list[3].children[0].children) if n == self.remove_sig_]
                location = location[0]

                self.display_list[3].children[0].children[location - 2].options = temp_sl
                self.display_list[3].children[0].children[location - 2].value = s

                temp_sl.remove(s)

                if s == self.signal_list[-1]:
                    pass

                else:
                    self.display_list[3].children[0].children = self.display_list[3].children[0].children[
                                                                :location - 1] + \
                                                                (ipw.Dropdown(
                                                                    options=temp_sl,
                                                                    value='',
                                                                    description='Signal_' + str(location - 3) + ':',
                                                                    disabled=False,
                                                                ),
                                                                ) + \
                                                                self.display_list[3].children[0].children[location - 1:]

            clear_output()

            display(ipw.VBox(self.display_list))

    def bat_data_push(self, b):

        t = list(self.condition_list)
        t.remove(str(self.known_cap_.value))
        self.batch_cap_.options = t

        self.display_list[6].children = [
                                ipw.HBox([self.batch_data, self.cont_data]),
                                self.batch_text,
                                self.batch_cap_]

        self.button.disabled = False
        self.batch_data.button_style = 'info'
        self.cont_data.button_style = ''

        clear_output()

        display(ipw.VBox(self.display_list))

    def cont_data_push(self, b):

        self.display_list[6].children = [
                                ipw.HBox([self.batch_data, self.cont_data]),
                                self.similarity_,
                                self.return_]

        self.button.disabled = False
        self.cont_data.button_style = 'info'
        self.batch_data.button_style = ''

        clear_output()

        display(ipw.VBox(self.display_list))

    def new_sig_select(self, b):

        location = [i for i, n in enumerate(self.display_list[3].children[0].children) if n == self.remove_sig_][0]

        if self.display_list[3].children[0].children[location - 2].value == '':
            print("PLease pick a signal")
        else:

            remove_item = self.display_list[3].children[0].children[location - 2].value
            temp_sl = list(self.display_list[3].children[0].children[location - 2].options)

            self.display_list[3].children[0].children[location - 2].disabled = True

            if len(temp_sl) > 2:

                temp_sl.remove(remove_item)

                self.display_list[3].children[0].children = self.display_list[3].children[0].children[:location - 1] + \
                                                            (ipw.Dropdown(
                                                                options=temp_sl,
                                                                value='',
                                                                description='Signal_' + str(location - 3) + ':',
                                                                disabled=False,
                                                            ),
                                                            ) + \
                                                            self.display_list[3].children[0].children[location - 1:]

                self.remove_sig_.disabled = False
            else:
                self.add_sig_.description = 'Full'
                self.add_sig_.disabled = True

            clear_output()

            display(ipw.VBox(self.display_list))

    def remove_sig_select(self, b):

        location = [i for i, n in enumerate(self.display_list[3].children[0].children) if n == self.remove_sig_][0]

        if location > 5:

            self.display_list[3].children[0].children = self.display_list[3].children[0].children[:location - 2] + \
                                                        self.display_list[3].children[0].children[location - 1:]

            clear_output()

            self.display_list[3].children[0].children[location - 3].disabled = False

            display(ipw.VBox(self.display_list))

            if [i for i, n in enumerate(self.display_list[3].children[0].children) if n == self.remove_sig_][0] == 5:
                self.remove_sig_.disabled = True

            self.add_sig_.description = ''
            self.add_sig_.disabled = False

        else:

            print("no signals to remove")

    def return_all(self, b):
        if self.return_all_.button_style == 'info':
            self.return_top_x_.disabled = False
            self.return_top_x_.value = '10'
            self.return_all_.button_style = ''
        else:
            self.return_top_x_.disabled = True
            self.return_top_x_.value = 'inf'
            self.return_all_.button_style = 'info'
