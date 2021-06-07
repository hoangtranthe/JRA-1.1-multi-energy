import os
import numpy as np
import pandas as pd
from pandas import read_json

import pandapower as pp
import pandapower.networks as nw
import pandapower.topology as top
import pandapower.converter
import pandapower.estimation
import pandapower.test
from pandapower.timeseries import DFData
from pandapower.timeseries import OutputWriter
from pandapower.timeseries.run_time_series import run_timeseries
import pandapower.control as control
import DiscreteHPControl

import plot_network
import quasidyn_calc

dirname = os.path.dirname(__file__)

#create empty net
net = pp.create_empty_network()

#create buses
networks = pd.read_csv("netw_params/netws.csv", sep=";", header=0, decimal=".")
for _, network in networks.iterrows():
    for i in range(network.n_bus):
        pp.create_bus(net, name="Bus_%s" %i, vn_kv=network.vn_kv, type="b")

net.bus_geodata = read_json("""{"x":{"0":2.0,"1":4.0,"2":6.0},"y":{"0":11,"1":11,"2":11}}""")
net.bus_geodata = net.bus_geodata.loc[net.bus.index]


# create external grid
pp.create_ext_grid(net, pp.get_element_index(net, "bus", "Bus_0"), vm_pu=1.02, va_degree=0, name="External Grid")


#create branch elements
lv_lines = pd.read_csv("netw_params/lv_lines.csv", sep=";", header=0, decimal='.')
for _, line in lv_lines.iterrows():
    from_bus = pp.get_element_index(net, "bus", line.from_bus)
    to_bus = pp.get_element_index(net, "bus", line.to_bus)
    pp.create_line(net, from_bus, to_bus, length_km=line.length, std_type=line.std_type, name=line.line_name)


# create loads
lv_loads = pd.read_csv("netw_params/lv_loads.csv", sep=";", header=0, decimal='.')
for _, load in lv_loads.iterrows():
    bus_idx = pp.get_element_index(net, "bus", load.bus)
    pp.create_load_from_cosphi(net, bus=bus_idx, sn_mva=load.s, cos_phi=load.cosphi, mode="ind", name=load.load_name,
                               max_p_mw=load.max_p_mw, min_p_mw=load.min_p_mw, controllable=load.controllable, scaling=load.scaling)


# create PVs
lv_PVs = pd.read_csv("netw_params/lv_PVs.csv", sep=";", header=0, decimal='.')
for _, PV in lv_PVs.iterrows():
    bus_idx = pp.get_element_index(net, "bus", PV.bus)
    pp.create_sgen(net, bus=bus_idx, p_mw=PV.p, q_mvar=PV.q, type=PV.type, name=PV.PV_name, scaling=PV.scaling)


#create switch
lv_buses = net.bus[net.bus.vn_kv == networks.loc[0][2]].index
lv_switches = net.line[(net.line.from_bus.isin(lv_buses)) & (net.line.to_bus.isin(lv_buses))]
for _, line in lv_switches.iterrows():
    pp.create_switch(net, line.from_bus, line.name, et="l", closed=True, type="LBS",
                     name="Switch_%s-%s" %(net.bus.name.at[line.from_bus], line["name"]))


#create heat pump controller
hp_controller = DiscreteHPControl.DiscreteHPControl(net=net, hid=1, delta_vm_pu=0.1, deadband=0.01,
                                                    delta_vm_lower_pu=-0.1, delta_vm_upper_pu=0.1)

# # Load flow calculation
# pp.runpp(net, run_control=True)


# Plot network diagram
# plot_network.plot_overview(net)

#QuasiDyn Calculation
output_dir_quasi = os.path.join(dirname, "QuasiDynamic_Results")
print("Results can be found in your local temp folder: {}".format(output_dir_quasi))
if not os.path.exists(output_dir_quasi):
    os.mkdir(output_dir_quasi)
quasidyn_calc.quasidyn(output_dir_quasi, net, n_timesteps=96, data_subfolder="netw_params",
                                  data_filename="load_gen_profiles_15p.csv")
quasidyn_calc.plot_quasi_res(dirname, "QuasiDynamic_Results", 'plot_info.csv', net, n_timesteps=96, stepsize=15)

