import pandas as pd
import numpy as np
from scipy import stats
from datetime import datetime, timedelta
import pickle
import os
from seeq import spy

import mass_ts as mts
from dtaidistance import dtw


def gather_workbook_worksheet_meta_data(workbook_id, worksheet_id):
    """
    This function gathers workbook object data and worksheet index

    Parameters
    ----------
    workbook_id : str
        The Seeq ID of the source workbook
    worksheet_id: str
        The Seeq ID of the source worksheet

    Returns
    -------
    desired_workbook: list of seeq.spy.workbooks._workbook objects
        and seeq spy workbook meta data
    sheet_index: int
        integer detailing the index of the source worksheet
    """

    wb_id = spy.workbooks.search({'ID': workbook_id},
                                 quiet=True
                                 )

    desired_workbook = spy.workbooks.pull(wb_id,
                                          include_referenced_workbooks=False, include_inventory=False,
                                          quiet=True, errors='catalog'
                                          )

    # find worksheet index
    try:
        sheet_list = desired_workbook[0].worksheets
        sheet_index = [i for i, s in enumerate(sheet_list) if worksheet_id in str(s)][0]

        return desired_workbook, sheet_index

    except IndexError:
        print('ERROR = Could not find worksheet: ' + str(worksheet_id))


def save_ref(workbook_id, worksheet_id, signal_pull_list, known_cap, time_frame, grid, save_name, mypath):
    """
    This function saves the reference profile time series data and metadata as a pickle file

    Parameters
    ----------
    workbook_id : str
        The Seeq ID of the source workbook
    worksheet_id: str
        The Seeq ID of the source worksheet
    signal_pull_list: list of str
        List of strings that detail the signal names to describe the reference profile to be saved
    known_cap: str
        Name (str) of the capsule that defines the reference/s to be saved
    time_frame: list of datetime
        Start and end datetimes of the analysis range to searched for the known capsule in the seeq.spy.pull
    grid: str
        resolution/griding of the seeq.spy.pull
    save_name: str
        name of the pickle file to saved as
    mypath
        path to folder to save the pickle file in
    """

    desired_workbook, sheet_index = gather_workbook_worksheet_meta_data(workbook_id, worksheet_id)

    # define signals to be searched and pulled
    items = desired_workbook[0].worksheets[sheet_index].display_items
    items_s = items[items.Type == 'Signal']
    items_s = items_s[items_s['Name'].isin(signal_pull_list)]

    # define 'known' condition to be pulled for all signals
    items_c = items[items.Type == 'Condition']
    items_c = items_c[items_c.Name == known_cap]
    data_pull_known = spy.pull(items_c, start=time_frame[0], end=time_frame[1], quiet=True, grid=grid)

    file_name = os.path.join(str(mypath), str(save_name) + '.pkl')

    with open(file_name, 'wb') as file_:
        pickle.dump(items_s, file_)
        pickle.dump(data_pull_known, file_)


def load_ref(load_name, mypath):
    """
    This function loads the reference profile time series data and metadata from a previously saved pickle file.

    Parameters
    ----------
    load_name: str
        Name of the pickle file to load.
    mypath: str
        Path to folder containing the pickle file to load.

    Returns
    -------
    items_s_ref: pd.DataFrame, pd.Series
        A dataframe or series that minimally has columns of ['Name', 'ID', 'Type', 'Color', 'Line Style', 'Line Width',
        'Lane', 'Samples Display', 'Axis Auto Scale', 'Axis Align', 'Axis Group', 'Axis Show'] to detail the signals
        that describe the known reference profile.
    data_pull_known: pd.DataFrame, pd.Series
        A dataframe or series that minimally has columns of
        ['Condition', 'Capsule Start','Capsule End','Capsule Is Uncertain']
        to detail the capsule of the known reference profile capsule.

    """

    file_name = os.path.join(str(mypath), str(load_name) + '.pkl')

    with open(file_name, 'rb') as file_:
        items_s_ref = pickle.load(file_)
        data_pull_known = pickle.load(file_)

    return items_s_ref, data_pull_known


def pull_ref_data(items_s_ref, data_pull_known, grid):
    """
    This function gathers the time series data of the reference. The reference conditions limits the timeframe of the
    time series data to be gathered, a signal list instructs the variables to be gathered and the sampling rate or
    griding is set.

    Parameters
    ----------
    items_s_ref: pd.DataFrame, pd.Series
        A dataframe or series that minimally has columns of
        ['Name', 'ID', 'Type', 'Color', 'Line Style', 'Line Width', 'Lane',
        'Samples Display', 'Axis Auto Scale', 'Axis Align', 'Axis Group',
        'Axis Show']. To detail the signals that describe the known reference profile.
    data_pull_known: pd.DataFrame, pd.Series
        A dataframe or series that minimally has columns of
        ['Condition', 'Capsule Start','Capsule End','Capsule Is Uncertain'].
        To detail the capsule of the known reference profile capsule.
    grid: str
        Resolution/griding of the spy pull.

    Returns
    -------
    data_pull_c: pd.DataFrame, pd.Series
        A dataframe or series that minimally has columns of "X, ..., Y" signals
        requested to be pulled (detailed in items_s_ref input variable) and 'Date-Time'
        with an index of timestamps.
        [X, ..., Y,'Date-Time'].
        This dataframe has all the time series data for the reference profile.
    """

    start_all = data_pull_known['Capsule Start'].iloc[0]
    end_all = data_pull_known['Capsule End'].iloc[-1]

    data_pull_c = spy.pull(items_s_ref, start=start_all, end=end_all, quiet=True, grid=grid)
    data_pull_c['Date-Time'] = pd.to_datetime(data_pull_c.index)
    data_pull_c = data_pull_c.dropna()

    return data_pull_c


def pull_mps_data(workbook_id, worksheet_id, signal_pull_list, items_s_ref, data_pull_known, time_frame, grid):
    """
    This function gathers all the time series data required for the analysis, for the reference and the search area.

    Parameters
    ----------
    workbook_id : str
        The Seeq ID of the source workbook.
    worksheet_id: str
        The Seeq ID of the source worksheet.
    signal_pull_list: list of str
        List of strings that detail the signal names to describe the reference profile.
    items_s_ref: pd.DataFrame, pd.Series
        A dataframe or series that minimally has columns of ['Name', 'ID', 'Type', 'Color', 'Line Style', 'Line Width',
        'Lane', 'Samples Display', 'Axis Auto Scale', 'Axis Align', 'Axis Group', 'Axis Show']. To detail the signals
        that describe the reference profile.
    data_pull_known: pd.DataFrame, pd.Series
        A dataframe or series that minimally has columns of
        ['Condition', 'Capsule Start','Capsule End','Capsule Is Uncertain'].
        to detail the capsule of the known reference profile capsule.
    time_frame: list of datetime
        Start and end of the analysis range to search for the known capsule in the spy pull.
    grid: str
        Details the resolution/griding of the spy pull

    Returns
    -------
    data_pull: pd.DataFrame, pd.Series
        A dataframe or series that minimally has columns of "X, ..., Y" signals
        requested to be pulled (detailed in items_s_ref input variable) and 'Date-Time'
        with an index of timestamps.
        [X, ..., Y,'Date-Time'].
        This dataframe has all the time series data for the analysis/search area.known_select
    data_pull_c: pd.DataFrame, pd.Series
        A dataframe or series that minimally has columns of "X, ..., Y" signals
        requested to be pulled (detailed in items_s_ref input variable) and 'Date-Time'
        with an index of timestamps.
        [X, ..., Y,'Date-Time'].
        This dataframe has all the time series data for the reference profile.
    sheet_index: int
        Integer detailing the index of the source worksheet.

    """

    desired_workbook, sheet_index = gather_workbook_worksheet_meta_data(workbook_id, worksheet_id)

    # define signals to be searched and pull in 1min grid
    items = desired_workbook[0].worksheets[sheet_index].display_items
    items_s = items[items.Type == 'Signal']
    items_s = items_s[items_s['Name'].isin(signal_pull_list)]

    data_pull = spy.pull(items_s, start=time_frame[0], end=time_frame[1], quiet=True, grid=grid)
    data_pull['Date-Time'] = pd.to_datetime(data_pull.index)
    data_pull = data_pull.dropna()

    data_pull_c = pull_ref_data(items_s_ref, data_pull_known, grid)

    # return signal data, known capsule start and send time, length of known window
    return data_pull, data_pull_c, sheet_index


def sort_and_prepare_results(data_pull, total_dist, window_step, threshold, known, sim_, max_):
    """
    This function takes the distance measurements from all variables at each window step, orders them numerically,
    computes a % similarity score by comparing against the minimum possible distance (zero) and the maximum distance
    (largest of the inverse of its self or maximum found distance) and removes overlapping 'found' capsules/events from
    most similar to least similar.

    Parameters
    ----------
    data_pull: pd.DataFrame, pd.Series
        A dataframe or series that minimally has columns of "X, ..., Y" signals
        requested to be pulled (detailed in items_s_ref input variable) and 'Date-Time'
        with an index of timestamps.
        [X, ..., Y,'Date-Time']. This dataframe has all the time series data for the analysis/search area.
    total_dist: list of float
        List of distance measurements between the two curves.
    window_step: int
        ize of the window stepping used by the algo.
    known: pd.DataFrame, pd.Series
        A dataframe or series that minimally has columns of "X, ..., Y" signals
        requested to be pulled (detailed in items_s_ref input variable) and 'Date-Time'
        with an index of timestamps.
        [X, ..., Y,'Date-Time'].
        This dataframe has strictly only the time series data for the reference profile start and end.
    sim_: bool
        Set to return similar or dis-similar results.
    threshold: float
        0 to 1 float to set similarity cutoff for found capsules.
    max_: float
        Max accumulative distance used to scale all other distances measured.
        
    Returns
    -------
    found_list: list of int
        Each int in the list is the sorted (highest similarity match 1st) index of each found capsule
        as an integer relative to data_pull.
    found_sim: list of float
        Corresponding similarity measurement (0 to 1) of found list with 100% being a perfect match.
    """

    # suppress warnings of "A value is trying to be set on a copy of a slice from a DataFrame."
    pd.options.mode.chained_assignment = None  # default='warn'
    found_list = []
    found_sim = []
    # create dataframe of results to remove sort, remove out of threshold set and remove duplicates
    total_dist_df = pd.DataFrame(total_dist, columns=['distance'])
    # adjust if window steps are used
    total_dist_df.index = total_dist_df.index * window_step
    total_dist_df['index_'] = total_dist_df.index

    # short by lowest distance (best match) and get index of lowest to then be used to find datetime
    if known.index[0] >= data_pull.index[0] and known.index[-1] <= data_pull.index[-1]:
        known_index = data_pull.index.get_loc(known.index[0])
        # remove known capsule
        total_dist_df = total_dist_df[(total_dist_df['index_'] > (known_index + known.shape[0])) |
                                      (total_dist_df['index_'] < (known_index - known.shape[0] * 0.5))
                                      ]

    # sort
    total_dist_df_sorted = total_dist_df.sort_values('distance', ascending=sim_)

    # min/max normalise
    min_ = 0
    if isinstance(max_, float):
        total_dist_df_sorted.distance.replace(np.inf, max_, inplace=True)
    else:
        total_dist_df_sorted.distance.replace(np.inf, 0, inplace=True)
        max_ = total_dist_df_sorted.distance.max()

    total_dist_df_sorted.distance = (total_dist_df_sorted.distance - min_) / (max_ - min_)
    total_dist_df_sorted.distance.where(total_dist_df_sorted.distance <= 1, 1, inplace=True)

    # remove out of threshold set
    if threshold > 0:
        total_dist_df_sorted_threshold_filtered = total_dist_df_sorted[total_dist_df_sorted.distance < (1 - threshold)]
    else:
        total_dist_df_sorted_threshold_filtered = total_dist_df_sorted

    for e in range(0, min(1000, total_dist_df_sorted_threshold_filtered.shape[0])):
        if e < total_dist_df_sorted_threshold_filtered.shape[0]:
            item = total_dist_df_sorted_threshold_filtered.index_.iloc[e]
            sim_save = total_dist_df_sorted_threshold_filtered.distance.iloc[e]

            min_window = item - known.shape[0]
            max_window = item + known.shape[0]
            total_dist_df_sorted_threshold_filtered = total_dist_df_sorted_threshold_filtered[
                (total_dist_df_sorted_threshold_filtered.index_ == item) |
                (total_dist_df_sorted_threshold_filtered.index_ > max_window) |
                (total_dist_df_sorted_threshold_filtered.index_ < min_window)
                ]
        else:
            break
        if known.index[0] >= data_pull.index[0] and known.index[-1] <= data_pull.index[-1]:
            known_index = data_pull.index.get_loc(known.index[0])
            # remove known capsule from found profiles and set as list to use for push capsules
            if (item < (known_index - known.shape[0] * 0.8)) or (item > (known_index + known.shape[0])):
                found_list.append(item)
                found_sim.append((1 - sim_save) * 100)
        else:
            found_list.append(item)
            found_sim.append((1 - sim_save) * 100)

    return found_list, found_sim


def known_select(data_pull_c, data_pull_known, select_):
    """
    This function uses the known start and end time of the reference capsule/s and extracts the time series data from
    the entire time series data set within the investigation range of the worksheet.

    Parameters
    ----------
    data_pull_c: pd.DataFrame, pd.Series
        A dataframe or series that minimally has columns of "X, ..., Y" signals
        requested to be pulled (detailed in items_s_ref input variable) and 'Date-Time'
        with an index of timestamps.
        [X, ..., Y,'Date-Time'].
        This dataframe has all the time series data for the reference profile.
    data_pull_known: pd.DataFrame, pd.Series
        A dataframe or series that minimally has columns of "X, ..., Y" signals
        requested to be pulled (detailed in items_s_ref input variable) and 'Date-Time'
        with an index of timestamps.
        [X, ..., Y,'Date-Time'].
        This dataframe has all the time series data for the analysis/search area.
    select_: str
        Name of the selected reference capsule.
    Returns
    -------
    known: pd.DataFrame, pd.Series
        A dataframe or series that minimally has columns of "X, ..., Y" signals
        requested to be pulled (detailed in items_s_ref input variable) and 'Date-Time'
        with an index of timestamps.
        [X, ..., Y,'Date-Time'].
        This dataframe has strictly only the time series data for the reference profile start and end.
    knownlength: int
        Length of the known dataframe.
    """
    try:
        known = data_pull_c[data_pull_c['Date-Time'] > data_pull_known['Capsule Start'][select_]]
        known = known[known['Date-Time'] < data_pull_known['Capsule End'][select_]]
        knownlength = known.shape[0]
    except:
        temp_df = data_pull_known
        temp_df['Capsule Start'] = pd.to_datetime(temp_df['Capsule Start'])
        temp_df['Capsule End'] = pd.to_datetime(temp_df['Capsule End'])

        known = data_pull_c[data_pull_c['Date-Time'] > temp_df['Capsule Start'][select_]]
        known = known[known['Date-Time'] < temp_df['Capsule End'][select_]]
        knownlength = known.shape[0]

    return known, knownlength


def seeq_mps_mass(data_pull, data_pull_c, data_pull_known, threshold, normalise, sim_):
    """
    This function measures the euclidean distance between the reference and search space time series data over the same
    duration (limited by the reference) using Mueen's Algorithm for Similarity Search [MASS]. The algorithm window steps
    through the time series data calculating a distance for each time period. It loops through all the variables
    in the dataset and sums the distances into an accumulative distance measurement for each time step. The function can
    be instructed to normalise the data before measurement. The distance scores are then converted to % similarity
    compared to minimum possible distance (zero) and the maximum distance (largest of the inverse of its self or maximum
    found distance). Finally the % of each variable/signal contribution to the similarity measurement is calculated.
    This function is intended to be applied to continuous process data.

    Technical reference found @ https://www.cs.unm.edu/~mueen/FastestSimilaritySearch.html

    Parameters
    ----------
    data_pull: pd.DataFrame, pd.Series
        A dataframe or series that minimally has columns of "X, ..., Y" signals
        requested to be pulled (detailed in items_s_ref input variable) and 'Date-Time'
        with an index of timestamps.
        [X, ..., Y,'Date-Time'].
        This dataframe has all the time series data for the analysis/search area.
    data_pull_c: pd.DataFrame, pd.Series
        A dataframe or series that minimally has columns of "X, ..., Y" signals
        requested to be pulled (detailed in items_s_ref input variable) and 'Date-Time'
        with an index of timestamps.
        [X, ..., Y,'Date-Time'].
        This dataframe has all the time series data for the reference profile.
    data_pull_known: pd.DataFrame, pd.Series
        A dataframe or series that minimally has columns of
        ['Condition', 'Capsule Start','Capsule End','Capsule Is Uncertain'].
        To detail the capsule of the known reference profile capsule.
    threshold: float
        0 to 1 float to set similarity cutoff for found capsules.
    normalise: bool
        Set normalisation of the input data to the algo.
    sim_: bool
        Set to return similar or dis-similar results.

    Returns
    -------
    found_all_sorted: numpy.ndarray
        numpy array of three columns
        1st = found capsules similarity measurement (float 0 to 1)
        2nd = integer index of each found capsule relative to data_pull
        3rd = integer describing the duration/length of the found capsule (each integer is defined by griding in
        'pull_mps_data')

    """

    found_list_overall = []
    found_sim_overall = []
    found_length_overall = []
    found_cap_known = []
    var_columns = []

    for var_1 in data_pull.columns[:-1]:
        for cap_ in range(data_pull_known.shape[0]):
            var_columns.append(str(var_1) + '_' + str(cap_))

    # loop on the known capsules
    for capsule_ in range(data_pull_known.shape[0]):
        max_ = 0
        known, knownlength = known_select(data_pull_c, data_pull_known, capsule_)

        # no window step therefore = 1
        window_step = 1
        for var in data_pull.columns[:-1]:
            chosen_var_list = data_pull.columns[:-1]
            qry = known[var].to_numpy()

            # capture max distance
            max_v = mts.mass(qry, qry * -1, normalize_query=normalise)
            if not isinstance(max_v, float):
                max_v = mts.mass(qry, np.zeros(len(qry)), normalize_query=normalise)
                if not isinstance(max_v, float):
                    if normalise:
                        max_v = float(len(qry))
                    else:
                        max_v = float(np.max(qry) * len(qry))

            max_ += max_v

            ts = data_pull[var].to_numpy()
            new_dist = (mts.mass(ts, qry, normalize_query=normalise))
            # size for addition
            if var == chosen_var_list[0]:
                total_dist = np.zeros(new_dist.shape[0])
                if capsule_ == 0:
                    meta_data = pd.DataFrame(index=[*range(len(new_dist))], columns=var_columns)
            # Totalise distances to find best multi variate match
            if np.inf not in new_dist and True not in np.isnan(new_dist):
                total_dist += new_dist

            meta_data[str(var) + '_' + str(capsule_)] = pd.Series(new_dist)

            found_cap_known.append(capsule_)

        # sort distances and prepare results to index to og data set
        found_list, found_sim = sort_and_prepare_results(data_pull, total_dist, window_step,
                                                         threshold, known, sim_, max_)

        found_length = [knownlength for x in range(len(found_list))]
        capsule_listgen = [capsule_ for x in range(len(found_list))]
        found_list_overall.extend(found_list)
        found_sim_overall.extend(found_sim)
        found_length_overall.extend(found_length)
        found_cap_known.extend(capsule_listgen)

    if known.index[0] >= data_pull.index[0] and known.index[-1] <= data_pull.index[-1]:
        # known add in to filter out
        found_list_overall.extend([data_pull.index.get_loc(known.index[0])])
        found_sim_overall.extend([1000])
        found_length_overall.extend([knownlength])

    found_all_sorted = sorted(zip(found_sim_overall, found_list_overall, found_length_overall,
                                  found_cap_known, found_cap_known), reverse=True)
    found_all_sorted = np.asarray(found_all_sorted)
    found_all_sorted = pd.DataFrame(found_all_sorted)

    for e in range(0, min(1000, found_all_sorted.shape[0])):
        if e < found_all_sorted.shape[0]:
            item = found_all_sorted.iloc[e, 1]
            shape = found_all_sorted.iloc[e, 2]

            min_window = item - shape
            max_window = item + shape

            found_all_sorted = found_all_sorted[
                (found_all_sorted[1] == item) |
                (found_all_sorted[1] > max_window) |
                (found_all_sorted[1] < min_window)
                ]

        else:
            break

    found_all_sorted = found_all_sorted[found_all_sorted.iloc[:, 0] != 1000]

    for var in data_pull.columns[:-1]:
        found_all_sorted[len(found_all_sorted.columns)] = 0
        for i in found_all_sorted.index:
            loc_c = str(var) + '_' + str(found_all_sorted[3][i])[0]
            loc_i = found_all_sorted[1][i]
            if meta_data[loc_c][loc_i] < 99999999999999999:
                found_all_sorted[len(found_all_sorted.columns) - 1][i] = meta_data[loc_c][loc_i]

    found_all_sorted['sum'] = found_all_sorted.loc[:, 5:].sum(axis=1)
    if found_all_sorted.shape[0] == 0:
        return found_all_sorted
    else:
        found_all_sorted.loc[:, 5:] = found_all_sorted.loc[:, 5:].div(found_all_sorted["sum"], axis=0) * 100
        found_all_sorted = found_all_sorted.drop("sum", 1)
        found_all_sorted = found_all_sorted.to_numpy()

        return found_all_sorted


def seeq_mps_dtw(data_pull, data_pull_c, data_pull_known, threshold, normalise, sim_, time_distort):
    """
    This function measures the distance between the reference and search space time series data over one or many window
    size/durations. This is achieved by utilising the dynamic time warping algorithm, which searches for the smallest
    distance from each data point to a corresponding reference data point within an assigned search window. This
    function window steps through the search area calculating a distance for each time period. It loops through all the
    variables in the dataset and sums the distances into an accumulative distance measurement for each step. The
    function can be instructed to normalise the data before measurement. Then the distance scores are converted to %
    similarity compared to minimum possible distance (zero) and the maximum distance (largest of the inverse of its self
    or maximum found distance). Finally the % of each variable/signal contribution to the similarity measurement is
    calculated. This function is intended to be applied to continuous process data. Technical reference
    https://www.cs.unm.edu/~mueen/DTW.pdf

    Parameters
    ----------
    data_pull: pd.DataFrame, pd.Series
        A dataframe or series that minimally has columns of "X, ..., Y" signals
        requested to be pulled (detailed in items_s_ref input variable) and 'Date-Time'
        with an index of timestamps.
        [X, ..., Y,'Date-Time'].
        This dataframe has all the time series data for the analysis/search area.
    data_pull_c: pd.DataFrame, pd.Series
        A dataframe or series that minimally has columns of "X, ..., Y" signals
        requested to be pulled (detailed in items_s_ref input variable) and 'Date-Time'
        with an index of timestamps.
        [X, ..., Y,'Date-Time'].
        This dataframe has all the time series data for the reference profile.
    data_pull_known: pd.DataFrame, pd.Series
        A dataframe or series that minimally has columns of
        ['Condition', 'Capsule Start','Capsule End','Capsule Is Uncertain'].
        To detail the capsule of the known reference profile capsule.
    threshold: float
        0 to 1 float to set similarity cutoff for found capsules.
    normalise: bool
        Set normalisation of the input data to the algo.
    sim_: bool
        Set to return similar or dis-similar results.
    time_distort: float
        0 to 1 float to set % of time distortion of the searching window length in the window stepping of the algo.

    Returns
    -------
    found_all_sorted: numpy.ndarray
        numpy array of three columns
        1st = found capsules similarity measurement (float 0 to 1)
        2nd = integer index of each found capsule relative to data_pull
        3rd = integer describing the duration/length of the found capsule (each integer is defined by griding in
        'pull_mps_data')

    """

    time_distort = int(time_distort * 100)
    found_list_overall = []
    found_sim_overall = []
    found_length_overall = []
    found_cap_known = []
    var_columns = []
    found_time_dist_overall = []

    # loop on the known capsules
    for capsule_ in range(data_pull_known.shape[0]):
        max_ = 0
        known, knownlength = known_select(data_pull_c, data_pull_known, capsule_)

        for time_distort_ in range(0, 1 + time_distort, 1):
            search_size_stretch = int(known.shape[0] * (time_distort_ / 100))
            # size of steps taken during dtw distance measurement across the dataset
            window_step = 1 #round(len(known) * 0.05)
            if window_step <= 0:
                window_step = 1
            for var in data_pull.columns[:-1]:
                chosen_var_list = data_pull.columns[:-1]
                qry = known[var].to_numpy()

                # capture max distance
                # normalise data
                if normalise:
                    qry = stats.zscore(qry)
                    if True in np.isnan(qry):
                        qry = np.zeros(len(qry))

                max_ += dtw.distance_fast(qry, (-1 * qry), window=round(known.shape[0] * (10 / 100)))

                ts = data_pull[var].to_numpy()
                dist = []
                # normalise data
                if normalise:
                    qry = stats.zscore(qry)
                    ts = stats.zscore(ts)
                    if True in np.isnan(qry):
                        qry = np.zeros(len(qry))
                    if True in np.isnan(ts):
                        ts = np.zeros(len(ts))
                # loop over window size of known length
                for i in range(0, (ts.shape[0] - known.shape[0]), window_step):
                    if i - search_size_stretch < 0:
                        temp_start = i
                    else:
                        temp_start = i - search_size_stretch
                    target = ts[temp_start:i + known.shape[0] + search_size_stretch]
                    distance = dtw.distance_fast(qry, target, window=round(known.shape[0] * (10 / 100)))
                    dist.append(distance)

                # size for cost function addition from zero
                if var == chosen_var_list[0]:
                    total_dist = np.zeros(len(dist))
                    if capsule_ == 0 and time_distort_ == 0:
                        meta_data = pd.DataFrame(index=[*range(len(dist))], columns=var_columns)

                # Totalise distances to find best multi variate match
                if np.inf not in dist and True not in np.isnan(dist):
                    total_dist += dist

                meta_data[str(var) + '_' + str(capsule_) + str(time_distort_)] = pd.Series(dist)

            # sort distances and prepare results to index to og data set
            found_list, found_sim = sort_and_prepare_results(data_pull, total_dist, window_step, threshold,
                                                             known, sim_, max_)
            found_length = [knownlength + (2 * search_size_stretch) for x in range(len(found_list))]

            found_list_overall.extend(found_list)
            found_sim_overall.extend(found_sim)
            found_length_overall.extend(found_length)
            time_distort_listgen = [time_distort_ for x in range(len(found_list))]
            found_time_dist_overall.extend(time_distort_listgen)
            capsule_listgen = [capsule_ for x in range(len(found_list))]
            found_cap_known.extend(capsule_listgen)

            if known.index[0] >= data_pull.index[0] and known.index[-1] <= data_pull.index[-1]:
                # known add in to filter out
                found_list_overall.extend([data_pull.index.get_loc(known.index[0])])
                found_sim_overall.extend([1000])
                found_length_overall.extend([knownlength])

    found_all_sorted = sorted(zip(found_sim_overall, found_list_overall, found_length_overall,
                                  found_cap_known, found_time_dist_overall), reverse=True)
    found_all_sorted = np.asarray(found_all_sorted)
    found_all_sorted = pd.DataFrame(found_all_sorted)

    for e in range(0, min(1000, found_all_sorted.shape[0])):
        if e < found_all_sorted.shape[0]:
            item = found_all_sorted.iloc[e, 1]
            # shape = found_all_sorted.iloc[e,2]

            min_window = item - knownlength
            max_window = item + knownlength

            found_all_sorted = found_all_sorted[
                (found_all_sorted.iloc[:, 1] == item) |
                (found_all_sorted.iloc[:, 1] > max_window) |
                (found_all_sorted.iloc[:, 1] < min_window)
                ]
        else:
            break

    found_all_sorted = found_all_sorted[found_all_sorted.iloc[:, 0] != 1000]

    for var in data_pull.columns[:-1]:
        found_all_sorted[len(found_all_sorted.columns)] = 0
        for i in found_all_sorted.index:
            loc_c = str(var) + '_' + str(found_all_sorted[3][i])[0] + str(found_all_sorted[4][i])[0]
            loc_i = int(found_all_sorted[1][i])
            found_all_sorted[len(found_all_sorted.columns) - 1][i] = meta_data[loc_c][loc_i / window_step]

    found_all_sorted['sum'] = found_all_sorted.loc[:, 5:].sum(axis=1)
    if found_all_sorted.shape[0] == 0:
        return found_all_sorted
    else:

        found_all_sorted.loc[:, 5:] = found_all_sorted.loc[:, 5:].div(found_all_sorted["sum"], axis=0) * 100
        found_all_sorted = found_all_sorted.drop("sum", 1)
        found_all_sorted = found_all_sorted.drop_duplicates(subset=[1])
        found_all_sorted = found_all_sorted.to_numpy()

        return found_all_sorted


def seeq_mps_dtw_batch(batch_cond, data_pull, data_pull_c, data_pull_known, normalise, time_distort):
    """
    This function is similar to the "seeq_mps_dtw" function but instead of window stepping through the entire search
    area it only measures the distance between two time series datasets for each capsule in the batch condition. This
    function is intended to be applied to batch process data.

    Parameters
    ----------
    batch_cond: pd.DataFrame, pd.Series
        pd.DataFrame, pd.Series
        A dataframe or series that minimally has columns of "X, ..., Y" conditions
        requested to be analysed with index of (x, ..., Y) and columns of at least Capsule Start, Capsule End.
        This dataframe has all the data for the batches capsules required.
    data_pull: pd.DataFrame, pd.Series
        A dataframe or series that minimally has columns of "X, ..., Y" signals
        requested to be pulled (detailed in items_s_ref input variable) and 'Date-Time'
        with an index of timestamps.
        [X, ..., Y,'Date-Time'].
        This dataframe has all the time series data for the analysis/search area
    data_pull_c: pd.DataFrame, pd.Series
        A dataframe or series that minimally has columns of "X, ..., Y" signals
        requested to be pulled (detailed in items_s_ref input variable) and 'Date-Time'
        with an index of timestamps.
        [X, ..., Y,'Date-Time'].
        This dataframe has all the time series data for the reference profile.
    data_pull_known: pd.DataFrame, pd.Series
        A dataframe or series that minimally has columns of
        ['Condition', 'Capsule Start','Capsule End','Capsule Is Uncertain'].
        To detail the capsule of the known reference profile capsule.
    normalise: bool
        Set normalisation of the input data to the algo.
    time_distort: float
        0 to 1 float to set % of time distortion of the searching window length in the window stepping of the algo.

    Returns
    -------
    batch_sim_df: pd.DataFrame
        A dataframe or series that minimally has columns of
        ['Similarity', 'Date-Time'].
        This has the resulting similarity measure of each defined capsule with the centered datetime

    """

    time_distort = int(time_distort * 100)
    meta_data = pd.DataFrame(index=batch_cond.index, columns=data_pull.columns[:-1])
    # loop on the known capsules
    for capsule_ in range(data_pull_known.shape[0]):
        max_ = 0
        known, knownlength = known_select(data_pull_c, data_pull_known, capsule_)

        for var in data_pull.columns[:-1]:
            chosen_var_list = data_pull.columns[:-1]

            qry = known[var].to_numpy()

            # capture max distance
            if normalise:
                try:
                    if (qry.max() - qry.min()) == 0:
                        pass
                    else:
                        qry = (qry - qry.min()) / (qry.max() - qry.min())
                except:
                    pass
            max_ += dtw.distance_fast(qry, (-1 * qry))

            dist = []

            for b in batch_cond.index:
                ts = data_pull[data_pull['Date-Time'] > batch_cond['Capsule Start'][b]]
                ts = ts[ts['Date-Time'] < batch_cond['Capsule End'][b]]
                # normalise data if level doesnt matter, only shape
                ts = ts[var].to_numpy()

                if ts.shape[0] < int(qry.shape[0] * 0.25):
                    print("Input capsule as too few data points, please remove capsule starting at " +
                          str(batch_cond['Capsule Start'][b]))
                    pass
                else:
                    if normalise:
                        if (qry.max() - qry.min()) == 0 or (ts.max() - ts.min()) == 0:
                            pass
                        else:
                            qry = (qry - qry.min()) / (qry.max() - qry.min())
                            ts = (ts - ts.min()) / (ts.max() - ts.min())

                    distance = dtw.distance_fast(qry, ts, window=int(len(qry) * (2 * time_distort / 100)))
                    meta_data[var][b] = distance
                    dist.append(distance)

            # size for cost function addition from zero
            if var == chosen_var_list[0]:
                total_dist = np.zeros(len(dist))

            # Totalise distances to find best multi variate match
            if np.inf not in dist and True not in np.isnan(dist):
                total_dist += dist

        total_dist_df = pd.DataFrame(total_dist, columns=['distance'])

        min_ = 0

        total_dist_df.distance.replace(np.inf, max_, inplace=True)
        total_dist_df.distance = (total_dist_df.distance - min_) / (max_ - min_)
        total_dist_df.distance.where(total_dist_df.distance <= 1, 1, inplace=True)

        total_dist = np.asarray(total_dist_df)

        if capsule_ == 0:
            found_sim_overall = total_dist
        else:
            for i in range(len(found_sim_overall)):
                if total_dist[i] < found_sim_overall[i]:
                    found_sim_overall[i] = total_dist[i]

    batch_sim_df = pd.DataFrame(found_sim_overall, columns=['Similarity'])
    batch_sim_df['Similarity'] = (batch_sim_df['Similarity']) * 100
    batch_sim_df['Date-Time'] = batch_cond['Capsule Start'] + (
            batch_cond['Capsule End'] - batch_cond['Capsule Start']) / 2

    batch_sim_df.index = pd.to_datetime(batch_sim_df['Date-Time'])
    batch_sim_df = batch_sim_df.drop('Date-Time', 1)

    meta_data.columns = "% Contribution to Dissimilarity from " + meta_data.columns

    meta_data['sum'] = meta_data.sum(axis=1)
    for c in meta_data.columns[:-1]:
        for i in meta_data.index:
            if meta_data['sum'][i] == 0:
                pass
            else:
                meta_data[c][i] = meta_data[c][i] / meta_data['sum'][i] * 100
    # meta_data= meta_data.div(meta_data["sum"], axis=0)*100
    meta_data = meta_data.drop("sum", 1)
    meta_data.index = batch_sim_df.index
    batch_sim_df = pd.concat([batch_sim_df, meta_data], axis=1)

    return batch_sim_df


def push_mps_results_batch(batch_sim_df, workbook_id, condition_name, Sheet_index):
    """
    This function pushes the % similarity score as a % dis-similarity time series signal to a new worksheet within the
    desired workbook in the case mps is in batch mode. In addition each variable's % contribution to the dis-similarity
    is also pushes as a signal per variable.

    Parameters
    ----------
    batch_sim_df: pd.DataFrame
        A dataframe or series that minimally has columns of
        ['Similarity', 'Date-Time'].
        This has the resulting similarity measure of each defined capsule with the centered datetime.
    workbook_id : str
        The Seeq ID of the source workbook
    condition_name: str
        Name of condition to leverage in the pushed item names.
    Sheet_index: int
        Integer detailing the index of the source worksheet.


    Returns
    -------
    end: bool
        Indicator for UI to display successful ending.
    """

    batch_sim_df.rename(columns={"Similarity": condition_name + "_Dissimilarity_measure"}, inplace=True)

    for col_name in batch_sim_df.columns:
        if 'Contribution' in col_name:
            batch_sim_df.rename(columns={col_name: col_name + " " + condition_name}, inplace=True)

    # get info from worksheet before push overwrites
    wb_id = spy.workbooks.search({'ID': workbook_id},
                                 quiet=True
                                 )

    workbook = spy.workbooks.pull(wb_id,
                                  include_referenced_workbooks=False, include_inventory=False,
                                  quiet=True, errors='catalog'
                                  )[0]

    worksheet_og = workbook.worksheets[Sheet_index]
    current_display_items = worksheet_og.display_items
    worksheet_name = "MPS results " + str(datetime.now().strftime("%d/%m/%Y %H:%M:%S"))
    # push similarity signal
    push_result_2 = spy.push(data=batch_sim_df,
                             workbook=workbook_id,
                             worksheet=worksheet_name,
                             quiet=True
                             )

    # push worksheet back in after overwrite
    new_display_items = pd.concat([current_display_items, push_result_2], axis=0, sort=True)
    lane_ = current_display_items[current_display_items['Samples Display'] == 'Line']['Lane'].max()

    workbook = spy.workbooks.pull(wb_id,
                                  include_referenced_workbooks=False, include_inventory=False,
                                  quiet=True, errors='catalog'
                                  )[0]

    lane_count = 1
    for name in batch_sim_df.columns:
        i = new_display_items.loc[new_display_items['Name'] == name].index[0]
        new_display_items["Samples Display"].loc[i] = "Bars"
        new_display_items["Line Width"].loc[i] = 40
        new_display_items["Lane"].loc[i] = lane_ + lane_count
        lane_count += 1

    workbook.worksheets[worksheet_name].display_items = new_display_items
    workbook.worksheets[worksheet_name].display_range = worksheet_og.display_range

    spy.workbooks.push(workbook, quiet=True)

    push_result_2["Value Unit Of Measure"] = "%"
    push_result_2["Maximum Interpolation"] = "1 sec"
    spy.push(metadata=push_result_2, quiet=True)

    end = True

    return end


def push_mps_results(
        Return_top_x, min_idx_multivar, data_pull, workbook_id, condition_name, Sheet_index, grid):
    """
    This function pushes the % similarity score as a % dis-similarity time series signal to a new worksheet within the
    desired workbook in the case mps is in continuous mode. In addition each variable's % contribution to the
    dis-similarity is also pushes as a signal per variable.

    Parameters
    ----------
    Return_top_x: int
        Variable to limit number of top found capsules.
    min_idx_multivar: numpy.ndarray
        numpy array of three columns
        1st = found capsules similarity measurement (float 0 to 1)
        2nd = integer index of each found capsule relative to data_pull
        3rd = integer describing the duration/length of the found capsule (each integer is defined by griding in
        'pull_mps_data')
    data_pull: pd.DataFrame, pd.Series
        A dataframe or series that minimally has columns of "X, ..., Y" signals
        requested to be pulled (detailed in items_s_ref input variable) and 'Date-Time'
        with an index of timestamps.
        [X, ..., Y,'Date-Time'].
        This dataframe has all the time series data for the analysis/search area.
    workbook_id : str
        The Seeq ID of the source workbook.
    condition_name: str
        Name of condition to leverage in the pushed item names.
    Sheet_index: int
        Integer detailing the index of the source worksheet.
    grid: str
        Resolution/griding of the spy pull.


    Returns
    -------
    end: bool
        Indicator for UI to display successful ending.
    """
    worksheet_name = "MPS results " + str(datetime.now().strftime("%d/%m/%Y %H:%M:%S"))
    grid_ = {'1sec': 1, '10sec': 10, '30sec': 30, '1min': 60, '5min': 300, '10min': 600, '30min': 1800}[grid]

    # if less than requested top results
    if len(min_idx_multivar) == 0:
        print("No Results Found")

    else:

        # Prep and unzip found data
        found_list = min_idx_multivar[:Return_top_x, 1].tolist()
        sim_list = min_idx_multivar[:Return_top_x, 0].tolist()
        known_length_list = min_idx_multivar[:Return_top_x, 2].tolist()

        # use index to find datetime
        push_cond = pd.DataFrame(data_pull['Date-Time'].iloc[found_list])
        push_cond.columns = ["Capsule Start"]
        push_cond["Capsule End"] = push_cond["Capsule Start"]

        # add by known length

        for i in range(len(known_length_list)):
            push_cond["Capsule End"].iloc[i] = push_cond["Capsule Start"].iloc[i] + timedelta(
                seconds=known_length_list[i] * grid_)

        push_cond = push_cond.reset_index(drop=True)
        push_cond['Date-Time'] = pd.to_datetime(push_cond.index)
        push_cond['Similarity'] = sim_list

        # get info from worksheet before push overwrites
        wb_id = spy.workbooks.search({'ID': workbook_id},
                                     quiet=True
                                     )

        workbook = spy.workbooks.pull(wb_id,
                                      include_referenced_workbooks=False, include_inventory=False,
                                      quiet=True, errors='catalog'
                                      )[0]

        worksheet_og = workbook.worksheets[Sheet_index]
        current_display_items = worksheet_og.display_items
        lane_ = current_display_items[current_display_items['Samples Display'] == 'Line']['Lane'].max()

        # push found conditions
        push_cond.reset_index(drop=True, inplace=True)

        push_result = spy.push(data=push_cond, workbook=workbook_id,
                               worksheet=worksheet_name,
                               metadata=pd.DataFrame([{
                                   'Name': condition_name,
                                   'Type': 'Condition',
                                   'Maximum Duration': '20d'
                               }]),
                               quiet=True
                               )

        # create dataframe to push similarity signal
        push_sig = pd.DataFrame(min_idx_multivar).drop([1, 2, 3, 4], 1)
        push_sig = push_sig.iloc[:Return_top_x]

        temp_c_list = data_pull.columns[:-1]
        temp_c_list = ["% Contribution to Dissimilarity from " + x + " " + condition_name for x in temp_c_list]
        name_ = condition_name + "_Dissimilarity_measure"
        temp_c_list.insert(0, name_)

        push_sig.columns = temp_c_list

        push_sig['temp'] = push_cond["Capsule Start"]

        for i in range(len(known_length_list)):
            push_sig['temp'].iloc[i] = push_sig['temp'].iloc[i] + (
                    timedelta(seconds=(known_length_list[i]) / 2) * grid_)

        push_sig.index = pd.to_datetime(push_sig.temp)
        push_sig = push_sig.drop('temp', 1)

        # change to dissimilarity
        push_sig[name_] = 100 - push_sig[name_]

        # push similarity signal
        push_result_2 = spy.push(data=push_sig,
                                 workbook=workbook_id,
                                 worksheet=worksheet_name,
                                 quiet=True
                                 )

        push_result_2["Value Unit Of Measure"] = "%"
        push_result_2["Maximum Interpolation"] = "1 sec"
        spy.push(metadata=push_result_2, quiet=True)

        # push worksheet back in after overwrite
        new_display_items = pd.concat([current_display_items, push_result, push_result_2], axis=0, sort=True)

        workbook = spy.workbooks.pull(wb_id,
                                      include_referenced_workbooks=False, include_inventory=False,
                                      quiet=True, errors='catalog'
                                      )[0]

        lane_count = 1
        for name in push_sig.columns:
            i = new_display_items.loc[new_display_items['Name'] == name].index[0]
            new_display_items["Samples Display"].loc[i] = "Bars"
            new_display_items["Line Width"].loc[i] = 40
            new_display_items["Lane"].loc[i] = lane_ + lane_count
            lane_count += 1

        new_display_items.reset_index(drop=True, inplace=True)

        workbook.worksheets[worksheet_name].display_items = new_display_items
        workbook.worksheets[worksheet_name].display_range = worksheet_og.display_range
        spy.workbooks.push(workbook, quiet=True)

        end = True

        return end
