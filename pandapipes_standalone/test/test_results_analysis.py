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

plt_dict_new = {
    'mdot': ['mdot_ch_in', 'mdot_dis_out','mdot_evap_in', 'mdot_cond_out'],
    'Temp' : ['T_hot','T_avg','T_cold','T_cond_out','T_return_tank','T_return_grid'],
    'Power': ['Qdot_cons1', 'Qdot_cons2','Qdot_evap', 'Qdot_cond']
}

plt_dict_network = {
    'mdot': [#'mdot_cons1', 'mdot_cons1_set',
             #'mdot_cons2', 'mdot_cons2_set',
             'mdot_grid', 'mdot_grid_set',
             'mdot_tank_in', 'mdot_tank_in_set',
             ],
    'Temperatures' : ['T_hot','T_avg','T_cold','T_cond_out','T_return_tank','T_return_grid'],
    #'Power': ['Qdot_cons1', 'Qdot_cons2', 'Qdot_evap',]
}

plt_dict = plt_dict_network

plt.ion()
plt.show()

# plt.figure(1)
# # first all - in one
# for vs in plt_dict.values():
#     for v in vs:
#         test = results_dict[v]
#         plt.plot(results_dict[v],  linewidth=3)
#
# plt.legend([v for vs in plt_dict.values() for v in vs],loc="upper right")
# plt.tight_layout()

fig2, axes = plt.subplots(nrows=len(plt_dict.keys()), ncols=1) # two axes on figure

for i, (title, variables) in enumerate(plt_dict.items()):
    #print(f"num, title, vars: {i}, {title}, {variables}", flush=True)
    axes[i].set_title(title)
    for v in variables:
        #print(v)
        axes[i].plot(results_dict[v], label=v)
    axes[i].legend(loc="upper right")

fig2.tight_layout()
'''
# plot in groups
fig1, (ax1, ax2, ax3) = plt.subplots(nrows=3, ncols=1) # two axes on figure
ax1.plot(results_dict['state'], label = 'state')
ax1.plot(results_dict['eta_hp'], label = 'eta_hp')
ax1.plot(results_dict['mdot_1_supply'], label = 'mdot_1_supply')
ax1.plot(results_dict['mdot_3_supply'], label = 'mdot_3_supply')

ax2.plot(results_dict['T_tank_target'], label = 'T_tank_target')
ax2.plot(results_dict['T_avg'], label = 'T_avg')
ax2.plot(results_dict['T_supply'], label = 'Tsupply')
ax2.plot(results_dict['T_hot'], label = 'T_hot')
ax2.plot(results_dict['T_cond_out'], label = 'T_cond_out')

ax3.plot(results_dict['Q_HP_set'], label = 'Q_HP_set')
ax3.plot(results_dict['Q_set'], label = 'Q_set')
ax3.plot(results_dict['Qdot_cond'], label = 'Qdot_cond' )
ax3.plot(results_dict['P_effective'], label = 'P_eff')
ax3.plot(results_dict['P_e_max'], label = 'P_max')

ax1.legend(loc="upper right")
ax2.legend(loc="upper right")
ax3.legend(loc="upper right")
'''

# eta heat pump plot
# plt.figure(4)
# plt.scatter(results_dict['P_effective']/250.0,results_dict['eta_hp'], c = results_dict['T_cond_out'])
# cb = plt.colorbar()
# plt.xlabel('% P el.')
# plt.ylabel('eta_hp')
# cb.set_label('T_cond_out')
