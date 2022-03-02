# -*- coding: utf-8 -*-

import pytest
import pickle
import pandas as pd
import numpy as np
from pathlib import Path
from seeq.addons.mps import _mps as mps

import sys
sys.path.append(".")


@pytest.mark.unit
def test_batch_calc():
    # test batch Sim calc

    # load test input
    batch_cond = pd.read_pickle('test_objects/data_pull_parameters_batchcal_input1.pkl')
    data_pull = pd.read_pickle('test_objects/data_pull_parameters_batchcal_input2.pkl')
    data_pull_c = pd.read_pickle('test_objects/data_pull_parameters_batchcal_input3.pkl')
    data_pull_known = pd.read_pickle('test_objects/data_pull_parameters_batchcal_input4.pkl')
    
    time_distort = 0.04
    
    # run function to test
    Batch_sim_df = mps.seeq_mps_dtw_batch(batch_cond, data_pull, data_pull_c, data_pull_known, True, time_distort)
    Batch_sim_df_test = pd.read_pickle('test_objects/batch_results.pkl')
    # Batch_sim_df_test.columns = ['Similarity']

    assert Batch_sim_df_test.equals(Batch_sim_df)


@pytest.mark.unit
def test_cts_calc_mass():

    # test continuous Mass calc with no data normalisation

    # load test input
    data_pull = pd.read_pickle('test_objects/data_pull_parameters_mass_input1.pkl')
    data_pull_c = pd.read_pickle('test_objects/data_pull_parameters_mass_input2.pkl')
    data_pull_known = pd.read_pickle('test_objects/data_pull_parameters_mass_input3.pkl')

    similarity = 0.9
    sim = True

    # run function to test
    min_idx_multivar = mps.seeq_mps_mass(data_pull, data_pull_c, data_pull_known, similarity, True, sim)

    # load test objects
    file_name2 = 'test_objects/cts_mass_results.pkl'
    file_2 = open(file_name2, 'rb')
    min_idx_multivar_test = pickle.load(file_2)
    
    file_2.close()

    assert np.array_equal(min_idx_multivar_test, min_idx_multivar)


@pytest.mark.unit
def test_cts_calc_dtw():

    # test continuous Mass calc with data normalisation

    # load test input
    data_pull = pd.read_pickle('test_objects/data_pull_parameters_dtw_input1.pkl')
    data_pull_c = pd.read_pickle('test_objects/data_pull_parameters_dtw_input2.pkl')
    data_pull_known = pd.read_pickle('test_objects/data_pull_parameters_dtw_input3.pkl')

    similarity = 0.9
    sim = True
    time_distort = 0.02
    
    # run function to test
    min_idx_multivar = mps.seeq_mps_dtw(data_pull, data_pull_c, data_pull_known, similarity, True, sim, time_distort)

    # load test objects
    file_name2 = 'test_objects/cts_dtw_results.pkl'
    file_2 = open(file_name2, 'rb')
    min_idx_multivar_test = pickle.load(file_2)

    file_2.close()

    assert np.array_equal(min_idx_multivar_test, min_idx_multivar)
