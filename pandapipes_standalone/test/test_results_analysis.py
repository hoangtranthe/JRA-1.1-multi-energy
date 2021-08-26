"""Results analysis script for the co-simulation setup."""


import os
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
import random
import collections
import numpy as np
from matplotlib.lines import Line2D
import matplotlib.dates as mdates
from pandas.plotting import register_matplotlib_converters
from sklearn.metrics import mean_squared_error
from math import sqrt
import matplotlib.gridspec as gridspec

from pandas.plotting import register_matplotlib_converters
register_matplotlib_converters()

cwd = os.getcwd()

def nested_dict():

    return collections.defaultdict(nested_dict)


results_dict = nested_dict()


###############################
# Retrieving data from stores #
###############################


# # Simple-collector monitor store # #
sc_monitor_store = pd.HDFStore('test_collector_store.h5')

for collector in sc_monitor_store:

    for (simulator, attribute), value in sc_monitor_store[collector].items():

        results_dict[attribute] = value

sc_monitor_store.close()



###
# Data manipulations
###


###
# Plotting
###

plt_dict_network = {
    'mdot': ['mdot_cons1', 'mdot_cons1_set',
             'mdot_cons2', 'mdot_cons2_set',
             'mdot_grid', 'mdot_grid_set',
             'mdot_tank_in', 'mdot_tank_in_set','state'],
    # 'voltage_control': [
    #          'hp_on_request', 'hp_off_request', 'state'
    #          ],
    'Temperatures' : ['T_supply_cons1','T_supply_cons2','T_return_cons1','T_return_cons2','T_tank_forward','T_return_tank','T_return_grid'],
    'Power': ['Qdot_cons1', 'Qdot_cons2', 'Qdot_evap'],
    # 'Power': ['P_el_setpoint_hp', 'W_requested', 'P_requested'],
    # 'Power': ['P_rated', 'P_hp_el_setpoint', 'P_effective'],
    # 'hp': ['eta_hp']
}

plt_dict = plt_dict_network

plt.ion()
plt.show()

fig2, axes = plt.subplots(nrows=len(plt_dict.keys()), ncols=1) # two axes on figure

df = pd.DataFrame(columns=plt_dict)
for i, (title, variables) in enumerate(plt_dict.items()):
    #print(f"num, title, vars: {i}, {title}, {variables}", flush=True)
    axes[i].set_title(title)
    for v in variables:
        #print(v)
        axes[i].plot(results_dict[v], label=v)
        df[v] = results_dict[v]
    axes[i].legend(loc="upper right")

fig2.tight_layout()
df.to_csv('results.csv')