"""Results analysis script for the co-simulation setup."""


import os
import matplotlib.pyplot as plt
from pandas.tseries.offsets import DateOffset
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
import datetime

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
sc_monitor_store = pd.HDFStore('load_collector_store.h5')

for collector in sc_monitor_store:

    for (simulator, attribute), value in sc_monitor_store[collector].items():

        results_dict[attribute] = value

sc_monitor_store.close()


###
# Plotting
###

plt_dict_simple= {
    'plt1' : ['P'],
    'plt2' : ['out'],
}

plt_dict = plt_dict_simple

plt.ion()
plt.show()

fig2, axes = plt.subplots(nrows=len(plt_dict.keys()), ncols=1) # two axes on figure

for i, (title, variables) in enumerate(plt_dict.items()):
    #print(f"num, title, vars: {i}, {title}, {variables}", flush=True)
    axes[i].set_title(title)
    for v in variables:
        #print(v)
        axes[i].plot(results_dict[v], label=v)
    axes[i].legend(loc="upper right")


# Save results
index = pd.to_datetime(results_dict['out'].index, unit='s')
date = DateOffset(years=49, months=1)
results_dict['out'].index = index + date



# results_dict['out'].index = index.map(lambda t: t.replace(year=2019, month=2, day=1))
results_dict['out'].to_csv('load_distorted.csv')

fig2.tight_layout()