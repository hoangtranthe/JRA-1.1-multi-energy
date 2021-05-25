import matplotlib.pyplot as mpl
import numpy as np
from pandas import read_json

import pandapower as pp
import pandapower.networks as nw
import pandapower.plotting as plt
from pandapower.plotting import get_collection_sizes

def plot_net(net, ax=None):
    if ax is None:
        fig, ax = mpl.subplots(1, 1, figsize=(12, 4))

    sizes = get_collection_sizes(net, load_size=2.0, ext_grid_size=2.0, sgen_size=2.0)

    # create collections for elements
    collections = list()
    collections.append(plt.create_bus_collection(net, patch_type="rect", size=sizes["bus"]))
    collections.append(plt.create_line_collection(net, use_bus_geodata=True))
    # collections.append(plt.create_trafo_collection(net, size=sizes["trafo"]))
    collections.append(plt.create_ext_grid_collection(net, size=sizes["ext_grid"], orientation=1.5*np.pi))
    collections.append(plt.create_bus_bus_switch_collection(net, size=sizes["switch"]))
    collections.append(plt.create_load_collection(net, size=sizes["load"]))
    collections.append(plt.create_sgen_collection(net, size=sizes["sgen"], orientation=2*np.pi))

    # add labels for each bus
    for idx in net.bus_geodata.index:
        x = net.bus_geodata.loc[idx, "x"] + sizes["bus"] * 3
        y = net.bus_geodata.loc[idx, "y"] + sizes["bus"] * 2
        ax.text(x, y, str(idx), fontsize=12, color="r")

    for _, element in net.sgen.iterrows():
        x = net.bus_geodata.loc[element.bus, "x"] - sizes["bus"] * 2
        y = net.bus_geodata.loc[element.bus, "y"] + sizes["bus"] * 10
        ax.text(x, y, "PV_%s" %element.bus, fontsize=12, color="r")

    for _, element in net.load.iterrows():
        x = net.bus_geodata.loc[element.bus, "x"] - sizes["bus"] * 2
        y = net.bus_geodata.loc[element.bus, "y"] - sizes["bus"] * 10
        ax.text(x, y, "Load_%s" % element.bus, fontsize=12, color="r")

    plt.draw_collections(collections, ax=ax)
    mpl.tight_layout()


def plot_overview(net):
    fig, axes = mpl.subplots(figsize=(12, 4))
    pp.runpp(net)
    plot_net(net, ax=axes)
    mpl.show()
