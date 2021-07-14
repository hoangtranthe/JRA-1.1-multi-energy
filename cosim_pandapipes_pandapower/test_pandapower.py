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
from simulators.el_network.simulator import make_eid as grid_id

logging.basicConfig(filename='cosimulation_logging.log', filemode='w', level=logging.INFO)

scenario_start_time = t_time.time()

simulation_local_time = t_time.ctime(scenario_start_time)

print("Co-Simulation started at :", simulation_local_time)

# # Get current working directory # #
cwd = os.getcwd()

# Sim config and other parameters
SIM_CONFIG = {
    'ElNetworkSim': {
        'python': 'simulators:ElectricNetworkSimulator'
    },
    'TSSim': {
        'python': 'simulators:TSSimSimulator'
    },
    'CollectorSim': {
        'python': 'simulators:Collector'
    },
    'VoltageControlSim':
    {
        'python': 'simulators:VoltageControlSimulator'
    },
}

# 1 mosaik time-step = 1 second.
STEP_SIZE = 60 * 1
END = 1 * 24 * 60 * 60

# # Set which day we are looking at.
power_demand_series = pd.read_csv('./resources/power/load_gen_profiles_15p.csv', index_col=0, parse_dates=True)
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

# #  Electrical network # #
simulators['el_network'] = world.start(
    'ElNetworkSim',
    step_size=STEP_SIZE, 
    mode='pf'
)

# # Time series player for the electrical load profiles # #
# # Time series player for the PV generation # #
simulators['load_gen_profiles'] = world.start(
    'TSSim',
    eid_prefix='powerdemand_',
    step_size=STEP_SIZE
)

# # Collector # #
simulators['collector'] = world.start(
    'CollectorSim',
    step_size=STEP_SIZE,
    print_results=False,
    save_h5=True,
    h5_store_name='results/test_collector_store.h5',
    h5_frame_name='results'
)

# # Voltage controller # #
simulators['voltage_controller'] = world.start(
    'VoltageControlSim',
    step_size=STEP_SIZE
)

########################
# Instantiate entities #
########################

# # Electrical Network # #
entities['el_network'] = simulators['el_network'].Grid(
    gridfile='resources/power/power_grid_model.json',
)

grid = entities['el_network'].children
el_nodes_load = {element.eid: element for element in grid if element.type in 'Load'}
el_nodes_gen = {element.eid: element for element in grid if element.type in 'Sgen'}
el_nodes_bus = {element.eid: element for element in grid if element.type in 'Bus'}
el_nodes_line = {element.eid: element for element in grid if element.type in 'Line'}

# # Time series player for the electrical load profiles # #
entities['consumer_load1'] = simulators['load_gen_profiles'].TSSim(
    t_start=consumer_t_start,
    series=power_demand_series.copy(),
    fieldname='Load_1',
    interp_method='pchip'
)

entities['consumer_load2'] = simulators['load_gen_profiles'].TSSim(
    t_start=consumer_t_start,
    series=power_demand_series.copy(),
    fieldname='Load_2',
    interp_method='pchip'
)

# # Time series player for the PV generation # #
entities['gen_pv1'] = simulators['load_gen_profiles'].TSSim(
    t_start=consumer_t_start,
    series=power_demand_series.copy(),
    fieldname='PV_1',
    interp_method='pchip',
    scale = 0.6
)

entities['gen_pv2'] = simulators['load_gen_profiles'].TSSim(
    t_start=consumer_t_start,
    series=power_demand_series.copy(),
    fieldname='PV_2',
    interp_method='pchip'
)

# # Voltage controller # #
entities['voltage_controller'] = simulators['voltage_controller'].VoltageController(
    delta_vm_upper_pu = 0.1,
    delta_vm_lower_pu_hp_on = -0.1,
    delta_vm_lower_pu_hp_off = -0.08, # -0.05
    delta_vm_deadband = 0.03,
    hp_p_el_mw_rated = 0.1, # 0.25
    hp_p_el_mw_min = 0.35 * 0.1, # 0.35 * 0.25
    hp_operation_steps_min = 30 * 60 / STEP_SIZE,
    k_p = 0.25
)

# # Collector # #
entities['sc_monitor'] = simulators['collector'].Collector()

###############
# Connections #
###############

# Connect electrical consumption profiles to electrical loads.
world.connect(entities['consumer_load1'], el_nodes_load[grid_id('Load_1',0)], ('P', 'p_mw'))
world.connect(entities['consumer_load2'], el_nodes_load[grid_id('Load_2',0)], ('P', 'p_mw'))

# Connect PV profiles to static generators.
world.connect(entities['gen_pv1'], el_nodes_gen[grid_id('PV_1',0)], ('P', 'p_mw'))
world.connect(entities['gen_pv2'], el_nodes_gen[grid_id('PV_2',0)], ('P', 'p_mw'))

# voltage control

world.connect(el_nodes_bus[grid_id('Bus_1',0)], entities['voltage_controller'], ('vm_pu', 'vmeas_pu'))
world.connect(entities['voltage_controller'], el_nodes_load[grid_id('Heat Pump',0)], ('hp_p_el_mw_setpoint', 'p_mw'),
              time_shifted=True, initial_data={'hp_p_el_mw_setpoint': 0.15})

###################
# Data collection #
###################

for load in el_nodes_load.values():
    world.connect(load, entities['sc_monitor'], 'p_mw')
for gen in el_nodes_gen.values():
    world.connect(gen, entities['sc_monitor'], 'p_mw')
for bus in el_nodes_bus.values():
    world.connect(bus, entities['sc_monitor'], 'vm_pu')
for line in el_nodes_line.values():
    world.connect(line, entities['sc_monitor'], 'loading_percent')

######################
# Run the simulation #
######################

world.run(until=END)

scenario_stop_time = t_time.time()
scenario_run_elapsed_time = str(datetime.timedelta(seconds=scenario_stop_time - scenario_start_time))

print('*' * 80)
print('TOTAL CO-SIMULATION TIME:')
print(scenario_run_elapsed_time)
print('*' * 80)
