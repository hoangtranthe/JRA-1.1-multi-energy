'''MOSAIK scenario.'''

import os
import mosaik
import mosaik.util
import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
import time as t_time
import datetime
import logging

logging.basicConfig(filename='../cosimulation_logging.log', filemode='w', level=logging.CRITICAL)

scenario_start_time = t_time.time()

simulation_local_time = t_time.ctime(scenario_start_time)

print("Co-Simulation started at :", simulation_local_time)

cwd = os.getcwd()

# Sim config and other parameters
SIM_CONFIG = {'DemandSim': {'python':  'simulators:TSSimSimulator'},
              'MultiFractalDistorter': {'python': 'mosaik_modules:MultiFractalMultiplier'},
              'Collector': {'python':  'simulators:Collector'},
              'MultiCollector': {'cmd': 'python mosaik_modules/multicollector.py %(addr)s'},
              }

END = 60 * 60 * 72  # 3600 seconds = 1 hour

world = mosaik.World(SIM_CONFIG)

simulators_dict = {}
entities_dict = {}


consumer_demand_series = pd.read_csv('./resources/heat_demand_load_profile_feb_to_march_2019.csv', index_col=0, parse_dates=True)
consumer_t_start = '2019-03-02 00:00:00'

###
# Simulators step calls
###
load_flow_step = 10
collector_step = 10
dh_heat_demand_step = 10
multifractaldistorter_step = 10
multicollector_step = 10

###
# Mosaik Components needed
###

# Heat Demand simulator
simulators_dict['consumer_demand'] = world.start('DemandSim', eid_prefix='heatdemand_', step_size=dh_heat_demand_step)
entities_dict['consumer_demand'] = simulators_dict['consumer_demand'].TSSim(
    t_start=consumer_t_start,
    series=consumer_demand_series.copy(),
    fieldname='hourly_heat_load_profile_500kW',
)

# # Collector # #
simulators_dict['collector'] = world.start(
    'Collector',
    step_size=collector_step,
    print_results=True,
    save_h5=True,
    h5_store_name='test/load_collector_store.h5',
    h5_frame_name='test'
)

entities_dict['sc_monitor'] = simulators_dict['collector'].Collector()


# Multi-fractal distorter
simulators_dict['multifractaldistorter_sim'] = world.start('MultiFractalDistorter', step_size=multifractaldistorter_step, verbose=False)
entities_dict["MFD_DemandQ_consumer1"] = simulators_dict['multifractaldistorter_sim'].MultiFractalDistorter.create(1)[0]

###############
# Connections #
###############

# Electrical time serie player -> multi-fractal distorter ('P')
world.connect(entities_dict['consumer_demand'], entities_dict['MFD_DemandQ_consumer1'], ('P', 'in'))

###################
# Data collection #
###################

# Simple Collector
collector_connections = {
    'consumer_demand': [
        'P',
    ],
    'MFD_DemandQ_consumer1': [
        'out',
    ],
}

# MultiCollector
for ent, outputnames in collector_connections.items():
    for outputname in outputnames:
        world.connect(entities_dict[ent], entities_dict['sc_monitor'], outputname)

world.run(until=END)

scenario_stop_time = t_time.time()

scenario_run_elapsed_time = str(datetime.timedelta(seconds=scenario_stop_time - scenario_start_time))

print('*' * 80)
print('TOTAL CO-SIMULATION TIME:')
print(scenario_run_elapsed_time)
print('*' * 80)
