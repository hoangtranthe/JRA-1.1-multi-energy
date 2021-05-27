# Copyright (c) 2021 by ERIGrid 2.0. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.

'''MOSAIK scenario.'''

import os
import mosaik
import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
import time as t_time
import datetime
import logging
import sys

logging.basicConfig(filename='cosimulation_logging.log', filemode='w', level=logging.DEBUG)

scenario_start_time = t_time.time()

simulation_local_time = t_time.ctime(scenario_start_time)

print("Co-Simulation started at :", simulation_local_time)

# # Get current working directory # #
cwd = os.getcwd()

# Sim config and other parameters
SIM_CONFIG = {
              'SWSTSim':                    {'python':  'simulators:StratifiedWaterStorageTankSimulator'},
              'ConstantTcondHPSim':         {'python':  'simulators:ConstantTcondHPSimulator'},
              'HEXConsumerSim':             {'python':  'simulators:HEXConsumerSimulator'},
              'DHNetworkSim':               {'python':  'simulators:DHNetworkSimulator'},
              'SimpleControllerSim':        {'python':  'simulators:SimpleFlexHeatControllerSimulator'},
              'TSSim':                      {'python':  'simulators:TSSimSimulator'},
              'CollectorSim':               {'python':  'simulators:Collector'},
              }


#############################
# INPUTS #
#############################
HP_TEMP_COND_OUT_TARGET = 75
TEMP_SUPPLY_HEX_INIT = 75  # Return temperature of hex consumer
EXT_SOURCE_SUPPLY_TEMP = 75  # Supply temperature of external dhn

TEMP_RETURN_HEX_INIT = 45  # Return temperature of hex consumer
STORAGE_TANK_INIT_TEMP = 70  # Storage tank initial temperature


# 1 mosaik time-step = 1 second.
STEP_SIZE = 60
PHYSICAL_STEP_SIZE = STEP_SIZE  # Physical evolution [s]
CONTROL_STEP_SIZE = STEP_SIZE  # Flow control [s]
PIPEFLOW_STEP_SIZE = 60
OPTIMIZER_STEP_SIZE = STEP_SIZE  # Used for MPC controller [s]
END = 6 * 60 * 60

# # Set which day we are looking at.
consumer_demand_series = pd.read_csv('./resources/heat/tc08ts01/distorted_heat_demand_load_profiles.csv', index_col=0, parse_dates=True)
consumer_t_start = '2019-02-01 00:00:00'

#############################
# Start MOSAIK orchestrator #
#############################

world = mosaik.World(SIM_CONFIG)

simulators = {}
entities = {}

###############################
# Initialize/START simulators #
###############################

# #  Heat consumer - Heat exchanger (HEX) # #
simulators['hex_consumer'] = world.start(
    'HEXConsumerSim',
    step_size=PHYSICAL_STEP_SIZE
)

# #  District heating network # #
simulators['dh_network'] = world.start(
    'DHNetworkSim',
    step_size=PIPEFLOW_STEP_SIZE
)

# # Time series player for the consumer heat demand # #
# # Time series player for flexheat demand # #
simulators['consumer_demand'] = world.start(
    'TSSim',
   eid_prefix='consumerheatdemand_',
   step_size=PHYSICAL_STEP_SIZE
)


# # Stratified water storage tank # #
simulators['storage_tank'] = world.start(
    'SWSTSim',
    step_size=PHYSICAL_STEP_SIZE
)

# # Heat pump - Constant output temperature at the condenser
simulators['hp'] = world.start(
    'ConstantTcondHPSim',
    eid_prefix='heatpump_',
    step_size=PHYSICAL_STEP_SIZE,
)

# # Simple controller # #
simulators['simple_controller'] = world.start(
    'SimpleControllerSim',
    step_size=PHYSICAL_STEP_SIZE
)

# # Collector # #
simulators['collector'] = world.start(
    'CollectorSim',
    step_size=PHYSICAL_STEP_SIZE,
    print_results=False,
    save_h5=True,
    h5_store_name='test/test_collector_store.h5',
    h5_frame_name='test'
)


########################
# Instantiate entities #
########################

# #  District Heating Network# #
entities['dh_network'] = simulators['dh_network'].DHNetwork(
    T_supply_grid=75,
    P_grid_bar=6,
    T_amb=8,
    dynamic_temp_flow_enabled=False,
)

# #  Heat consumer - Heat exchanger (HEX) # #
entities['hex_consumer1'] = simulators['hex_consumer'].HEXConsumer(
    T_return_target=40,
    P_heat=500,
    mdot_hex_in=3.5,
    mdot_hex_out=-3.5,
)
entities['hex_consumer2'] = simulators['hex_consumer'].HEXConsumer(
    T_return_target=40,
    P_heat=500,
    mdot_hex_in=3.5,
    mdot_hex_out=-3.5,
)

# # Time series player for the consumer heat demand # #
entities['consumer_demand1'] = simulators['consumer_demand'].TSSim(
    t_start=consumer_t_start,
    series=consumer_demand_series.copy(),
    fieldname='consumer1',
)


entities['consumer_demand2'] = simulators['consumer_demand'].TSSim(
    t_start=consumer_t_start,
    series=consumer_demand_series.copy(),
    fieldname='consumer2',
)

# # Stratified water storage tank # #
entities['storage_tank'] = simulators['storage_tank'].WaterStorageTank(
    INNER_HEIGHT=9.2-0.5-0.4-0.4,  # Full tank height, minus valve height, minus half rounded end height
    INNER_DIAMETER=3.72,
    INSULATION_THICKNESS=0.1,
    STEEL_THICKNESS=0.02,
    NB_LAYERS=10,
    T_volume_initial=60,  # degC
    dt=STEP_SIZE
)

# # Heat pump
entities['hp'] = simulators['hp'].ConstantTcondHP(
    P_rated=250.0,
    lambda_comp=0.2,
    P_0=0.3,
    eta_sys=0.8,
    eta_comp=0.7,
    dt=STEP_SIZE,
    T_cond_out_target=HP_TEMP_COND_OUT_TARGET,  # degC
    opmode='constant_T_out',  # Constant output power at condenser
)

# # Simple controller # #
entities['simple_controller'] = simulators['simple_controller'].SimpleFlexHeatController()


# # Collector # #
entities['sc_monitor'] = simulators['collector'].Collector()


###############
# Connections #
###############

# physical coupling
# simple flow control
world.connect(entities['simple_controller'], entities['dh_network'], ('mdot_1_supply', 'mdot_grid_set'))
world.connect(entities['simple_controller'], entities['dh_network'], ('mdot_3_supply', 'mdot_tank_in_set'))

# dh network
world.connect(entities['hex_consumer1'], entities['dh_network'], ('mdot_hex_out', 'mdot_cons1_set'))
world.connect(entities['hex_consumer2'], entities['dh_network'], ('mdot_hex_out', 'mdot_cons2_set'))


# Flexheat system
# heat demand control
# Consumer 1
world.connect(entities['consumer_demand1'], entities['dh_network'], ('P', 'Qdot_cons1'))
world.connect(entities['consumer_demand1'], entities['hex_consumer1'], ('P', 'P_heat'))
world.connect(entities['hex_consumer1'], entities['simple_controller'], ('mdot_hex_out', 'mdot_HEX1'))
world.connect(entities['dh_network'], entities['hex_consumer1'], ('T_supply_cons1', 'T_supply'),
              time_shifted=True, initial_data={'T_supply_cons1': 70})
# Consumer 2
world.connect(entities['consumer_demand2'], entities['dh_network'], ('P', 'Qdot_cons2'))
world.connect(entities['consumer_demand2'], entities['hex_consumer2'], ('P', 'P_heat'))
world.connect(entities['hex_consumer2'], entities['simple_controller'], ('mdot_hex_out', 'mdot_HEX2'))
world.connect(entities['dh_network'], entities['hex_consumer2'], ('T_supply_cons2', 'T_supply'),
              time_shifted=True, initial_data={'T_supply_cons2': 70})

# heat pump
world.connect(entities['simple_controller'], entities['hp'], ('mdot_2_return', 'mdot_evap_in'))
# world.connect(entities['3wayvalve_return'], entities['hp'], ('T2', 'T_evap_in'))  # Replaced by dh_network connector
world.connect(entities['dh_network'], entities['hp'], ('T_evap_in', 'T_evap_in'),
              time_shifted=True, initial_data={'T_evap_in': 40})
world.connect(entities['simple_controller'], entities['hp'], ('Q_HP_set', 'Q_set'))
world.connect(entities['hp'], entities['dh_network'], ('Qdot_evap', 'Qdot_evap'))
world.connect(entities['storage_tank'], entities['hp'], ('T_cold', 'T_cond_in'),
              time_shifted=True, initial_data={'T_cold': STORAGE_TANK_INIT_TEMP})
world.connect(entities['simple_controller'], entities['hp'], ('mdot_HP_out', 'mdot_cond_in'))
world.connect(entities['hp'], entities['simple_controller'], ('T_cond_out', 'T_hp_forward'),
              time_shifted=True, initial_data={'T_cond_out': 50})

# storage tank inlet
world.connect(entities['hp'], entities['storage_tank'], ('mdot_cond_out', 'mdot_ch_in'))
world.connect(entities['hp'], entities['storage_tank'], ('T_cond_out', 'T_ch_in'))
world.connect(entities['simple_controller'], entities['storage_tank'], ('mdot_3_supply', 'mdot_dis_out'))
world.connect(entities['dh_network'], entities['storage_tank'], ('T_return_tank', 'T_dis_in'))

# storage tank outlet
world.connect(entities['storage_tank'], entities['dh_network'], ('T_hot', 'T_tank_forward'),
              time_shifted=True, initial_data={'T_hot': STORAGE_TANK_INIT_TEMP})
world.connect(entities['storage_tank'], entities['simple_controller'], ('T_hot', 'T_tank_hot'),
              time_shifted=True, initial_data={'T_hot': STORAGE_TANK_INIT_TEMP})


###################
# Data collection #
###################

# Simple Collector
collector_connections = {
    'storage_tank': [
        'T_cold', 'T_hot', 'T_avg',
        'mdot_ch_in', 'mdot_dis_in', 'mdot_ch_out', 'mdot_dis_out',
        'T_ch_in', 'T_dis_in'],
    'hex_consumer1': [
        'P_heat', 'mdot_hex_in', 'mdot_hex_out',
        'T_supply', 'T_return'],
    'hex_consumer2': [
        'P_heat', 'mdot_hex_in', 'mdot_hex_out',
        'T_supply', 'T_return'],
    'hp': [
        'T_cond_out', 'T_cond_in',
        'T_evap_in', 'T_evap_out',
        'mdot_cond_in', 'mdot_cond_out',
        'mdot_evap_in', 'mdot_evap_out',
        'Q_set', 'Qdot_cond',
        'W_effective', 'W_requested',
        'P_effective', 'eta_hp'],
    'dh_network': [
        'T_tank_forward', 'T_supply_cons1', 'T_supply_cons2', 'T_return_cons1', 'T_return_cons2','T_return_tank','T_return_grid',
        'mdot_cons1_set', 'mdot_cons2_set', 'mdot_grid_set', 'mdot_tank_in_set',
        'mdot_cons1', 'mdot_cons2', 'mdot_grid', 'mdot_tank_in',
        'Qdot_cons1', 'Qdot_cons2', 'Qdot_evap'
    ],
}

# MultiCollector
for ent, outputnames in collector_connections.items():
    for outputname in outputnames:
        world.connect(entities[ent], entities['sc_monitor'], outputname)


world.run(until=END)

scenario_stop_time = t_time.time()

scenario_run_elapsed_time = str(datetime.timedelta(seconds=scenario_stop_time - scenario_start_time))

print('*' * 80)
print('TOTAL CO-SIMULATION TIME:')
print(scenario_run_elapsed_time)
print('*' * 80)
