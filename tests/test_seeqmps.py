# -*- coding: utf-8 -*-

import pytest
import pickle
import pandas as pd
import numpy as np

from seeq.addons.mps import _mps as mps


import sys
sys.path.append(".")


@pytest.mark.unit
def test_batch_calc():
    # test batch Sim calc

    # load test input

    batch_cond = pd.read_csv('test_objects/data_pull_parameters_batchcal_input1.csv', index_col=0)
    batch_cond['Capsule Start'] = pd.to_datetime(batch_cond['Capsule Start'])
    batch_cond['Capsule End'] = pd.to_datetime(batch_cond['Capsule End'])
    data_pull = pd.read_csv('test_objects/data_pull_parameters_batchcal_input2.csv', index_col=0)
    data_pull['Date-Time'] = pd.to_datetime(data_pull['Date-Time'])
    data_pull.index = pd.to_datetime(data_pull.index)
    data_pull_c = pd.read_csv('test_objects/data_pull_parameters_batchcal_input3.csv', index_col=0)
    data_pull_c['Date-Time'] = pd.to_datetime(data_pull_c['Date-Time'])
    data_pull_c.index = pd.to_datetime(data_pull_c.index)
    data_pull_known = pd.read_csv('test_objects/data_pull_parameters_batchcal_input4.csv', index_col=0)
    data_pull_known['Capsule Start'] = pd.to_datetime(data_pull_known['Capsule Start'])
    data_pull_known['Capsule End'] = pd.to_datetime(data_pull_known['Capsule End'])

    time_distort = 0.04

    # run function to test
    Batch_sim_df = mps.seeq_mps_dtw_batch(batch_cond, data_pull, data_pull_c, data_pull_known, True, time_distort)
    Batch_sim_df = Batch_sim_df.apply(pd.to_numeric)
    Batch_sim_df = Batch_sim_df.round(decimals=2)
    Batch_sim_df_test = pd.read_csv('test_objects/batch_results.csv', index_col=0)
    Batch_sim_df_test.index = pd.to_datetime(Batch_sim_df_test.index, format='mixed')
    Batch_sim_df_test = Batch_sim_df_test.round(decimals=2)

    # Batch_sim_df_test.columns = ['Similarity']

    assert Batch_sim_df_test.equals(Batch_sim_df)


@pytest.mark.unit
def test_cts_calc_mass():

    # test continuous Mass calc with no data normalisation

    # load test input
    data_pull = pd.read_csv('test_objects/data_pull_parameters_mass_input1.csv', index_col=0)
    data_pull_c = pd.read_csv('test_objects/data_pull_parameters_mass_input2.csv', index_col=0)
    data_pull_known = pd.read_csv('test_objects/data_pull_parameters_mass_input3.csv', index_col=0)

    similarity = 0.9
    sim = True

    # run function to test
    min_idx_multivar = mps.seeq_mps_mass(data_pull, data_pull_c, data_pull_known, similarity, True, sim)

    # load test objects
    file_name2 = 'test_objects/cts_mass_results.pkl'
    file_2 = open(file_name2, 'rb')
    min_idx_multivar_test = pickle.load(file_2)
    
    file_2.close()

    assert np.allclose(min_idx_multivar_test, min_idx_multivar, atol=0.1)


@pytest.mark.unit
def test_cts_calc_dtw():

    # test continuous Mass calc with data normalisation

    # load test input
    data_pull = pd.read_csv('test_objects/data_pull_parameters_dtw_input1.csv', index_col=0)
    data_pull_c = pd.read_csv('test_objects/data_pull_parameters_dtw_input2.csv', index_col=0)
    data_pull_known = pd.read_csv('test_objects/data_pull_parameters_dtw_input3.csv', index_col=0)

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

    assert np.allclose(min_idx_multivar_test, min_idx_multivar, atol=0.1)
