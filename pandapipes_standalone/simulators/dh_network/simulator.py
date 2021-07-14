# Copyright (c) 2021 by ERIGrid 2.0. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.

"""
	External heating grid model.
"""

import matplotlib.pyplot as plt
import pandas as pd
from dataclasses import dataclass, field
from typing import Dict
from .utils.dh_network_simulator.sources.dh_network_simulator import DHNetworkSimulator

# Global
OUTPUT_PLOTTING_PERIOD = 60 * 60 * 4 - 60

@dataclass
class DHNetwork:
	"""
		Pandapipes district heating network model.
	"""

	# Parameters
	T_amb: float = 8  # Ambient ground temperature [degC]
	enable_logging: bool = True  # enable power flow logging
	T_supply_grid: float = 75  # Supply temperature of the external grid [degC]
	P_grid_bar: float = 6  # Pressure of the external grid [bar]
	P_hp_bar: float = 6  # Pressure of the heat pump + storage unit [bar]
	dynamic_temp_flow_enabled: bool = True  # Enable external temperature flow sim incl. network inertia

	# Magnitudes
	CP_WATER: float = 4186  # Specific heat capacity of water [J/(kgK)]

	# Input
	Qdot_evap: float = 0  # Heat consumption of heat pump evaporator [kW]
	Qdot_cons1: float = 500  # Heat consumption of consumer 1 [kW]
	Qdot_cons2: float = 500  # Heat consumption of consumer 2 [kW]
	T_tank_forward: float = 70  # Supply temp of storage unit [degC]

	mdot_cons1_set: float = 4  # Mass flow at consumer 1 [kg/s]
	mdot_cons2_set: float = 4  # Mass flow at consumer 2 [kg/s]
	mdot_bypass_set: float = 0.5  # Mass flow through bypass (const.) [kg/s]
	mdot_grid_set: float = 7.5  # Mass flow injected by grid [kg/s]
	mdot_tank_in_set: float = 0  # Mass flow injected in the tank [kg/s]
	mdot_tank_out_set: float = - mdot_tank_in_set  # Mass flow supplied by the tank [kg/s]


	# Variables
	T_return_tank: float = 40  # Return temperature into the storage unit [degC]
	T_evap_in: float = 40  # Return temperature towards the heat pump evaporator [degC]
	T_return_grid: float = 40  # Return temperature of the external grid [degC]
	T_supply_cons1: float = 70  # Supply temperature at consumer 1 [degC]
	T_supply_cons2: float = 70  # Supply temperature at consumer 2 [degC]
	T_return_cons1: float = 40  # Return temperature at consumer 1 [degC]
	T_return_cons2: float = 40  # Return temperature at consumer 2 [degC]
	mdot_cons1: float = 4  # Mass flow at consumer 1 [kg/s]
	mdot_cons2: float = 4  # Mass flow at consumer 2 [kg/s]
	mdot_bypass: float = 0.5  # Mass flow through bypass (const.) [kg/s]
	mdot_grid: float = 7.5  # Mass flow injected by grid [kg/s]
	mdot_tank_in: float = 0  # Mass flow injected in the tank [kg/s]
	mdot_tank_out: float = - mdot_tank_in  # Mass flow supplied by the tank [kg/s]

	# Internal variables
	plot_results_enabled: bool = False  # calculates static and dynamic heat flow and compares both results (only when dynamic temp flow enabled!)
	compare_to_static_results: bool = False  # calculates static and dynamic heat flow and compares both results (only when dynamic temp flow enabled
	store: Dict[str, pd.DataFrame] = field(default_factory=dict)
	cur_t: float = 0  # Actual time [s]
	forward_pipe_list: list = None
	backward_pipe_list: list = None

	# Network utils
	dhn_sim: DHNetworkSimulator = field(init=False)
	junction: list = None
	pipe: list = None
	heat_exchanger: list = None
	valve: list = None
	controller: list = None
	sink: list = None
	source: list = None
	circ_pump: list = None

	# Component list
	componentList: list = None

	def __post_init__(self):
		self.dhn_sim = DHNetworkSimulator()
		self.dhn_sim.load_network(from_file=True,
									path='./resources/dh_network/',
									format='json_readable')
		self._init_output_store()

	def _init_output_store(self):
		# Init output storage
		if self.dynamic_temp_flow_enabled:
			self.store['dynamic'] = {}
			if self.compare_to_static_results:
				self.store['static'] = {}

		else:
			self.store['static'] = {}

	def step_single(self, time):
		j = self.junction
		v = self.valve

		# Set actual time
		self.cur_t = time

		# update inputs
		self._update()

		# Set simulation mode
		if not self.dynamic_temp_flow_enabled:
			mode = 'dynamic'
		else:
			mode = 'static'

		# Run simulation
		output = self.dhn_sim.run_simulation(sim_mode=mode)

		# Plot results
		if self.plot_results_enabled:
			if self.cur_t == OUTPUT_PLOTTING_PERIOD:
				self._plot_outputs()

		# Set output variables
		self.T_return_tank = round(output.res_junction.at[j.index('n3r'), 't_k'] - 273.15, 2)
		## TODO: Implement getter function get(component='node', name='n3r', parameter='t_k')
		self.T_evap_in = round(output.res_junction.at[j.index('n3r'), 't_k'] - 273.15, 2)
		self.T_return_grid = round(output.res_junction.at[j.index('n1r'), 't_k'] - 273.15, 2)
		self.T_supply_cons1 = round(output.res_junction.at[j.index('n5s'), 't_k'] - 273.15, 2)
		self.T_supply_cons2 = round(output.res_junction.at[j.index('n7s'), 't_k'] - 273.15, 2)
		self.T_return_cons1 = round(output.res_junction.at[j.index('n5r'), 't_k'] - 273.15, 2)
		self.T_return_cons2 = round(output.res_junction.at[j.index('n7r'), 't_k'] - 273.15, 2)

		self.mdot_cons1 = round(output.res_valve.at[v.index('sub_v1'), 'mdot_from_kg_per_s'], 2)
		self.mdot_cons2 = round(output.res_valve.at[v.index('sub_v2'), 'mdot_from_kg_per_s'], 2)
		self.mdot_bypass = round(output.res_valve.at[v.index('bypass'), 'mdot_from_kg_per_s'], 2)
		self.mdot_grid = round(output.res_valve.at[v.index('grid_v1'), 'mdot_from_kg_per_s'], 2)
		self.mdot_tank_out = round(output.res_valve.at[v.index('tank_v1'), 'mdot_from_kg_per_s'], 2)
		self.mdot_tank_in = - self.mdot_tank_out


	def _store_output(self, output, label='static'):  # TODO: Improve due to low performance
		data = {}

		for j in self.junction:
			data.update({'temp_' + j: round(output.res_junction.at[self.junction.index(j), 't_k'] - 273.15, 2)})

		for l in self.pipe:
			# Get temperature
			data.update({'temp_' + l: round(output.res_pipe.at[self.pipe.index(l), 't_to_k'] - 273.15, 2)})

			# Get mass flow
			data.update({'mdot_' + l: round(output.res_pipe.at[self.pipe.index(l), 'mdot_from_kg_per_s'], 2)})

			# Determine thermal inertia
			dx = output.pipe.at[self.pipe.index(l), 'length_km'] * 1000
			v_mean = output.res_pipe.at[self.pipe.index(l), 'v_mean_m_per_s']
			dt = dx / v_mean
			data.update({'dt_' + l: round(dt, 2)})

		df = pd.DataFrame.from_dict(self.store[label])
		df = df.append((pd.DataFrame(data=data, index=[self.cur_t])))
		self.store[label] = df.to_dict()

	def _plot_outputs(self):
		plt_dict = {
			# 'temp': ['n1s', 'n2s', 'n3s', 'n3s_tank', 'n4s', 'n5s', 'n6s', 'n7s', 'n8s'],
			'temp': ['n3s', 'n5s', 'n4s', 'n6s', 'n7s'],
			#'dt': ['l2s', 'l3s', 'l4s', 'l5s', 'l6s'],
			'mdot': ['l2s', 'l3s', 'l4s', 'l5s', 'l6s'],
		}

		# define different linestyles for static and dynamic results
		ls = {'static': '-', 'dynamic': '--'}

		# Plot data
		fig, ax = plt.subplots(nrows=len(plt_dict.keys()), ncols=1)
		for sim in self.store:
			df = pd.DataFrame.from_dict(self.store[sim])
			for i, (title, variables) in enumerate(plt_dict.items()):

				# create subplot figure setup
				if len(plt_dict.items()) is 1:
					axes = ax
				else:
					axes = ax[i]

				# plot data
				axes.set_title(title)
				for v in variables:
					axes.plot(df[title + '_' + v], label=v, linestyle=ls[sim])
				axes.set_prop_cycle(None)  # same colormap for dynamic and static
				axes.legend(loc="upper right")

	def _update(self):
		hex = self.heat_exchanger
		ctrl = self.controller
		sink = self.sink
		source = self.source
		v = self.valve

		self.mdot_tank_out_set = - self.mdot_tank_in_set
		self.mdot_grid_set = self.mdot_cons1_set + self.mdot_cons2_set + self.mdot_bypass_set - self.mdot_tank_out_set

		# TODO: Create getter and setter for DHNNetworkSimulator class
		######################### Test
		self.dhn_sim.update_network_component(name='n1s',
											  type='junction',
											  parameter='tfluid_k',
											  value=1000)
		########################

		# # Update grid mass flow
		# self.net.sink.at[sink.index('sink_grid'), 'mdot_kg_per_s'] = self.mdot_grid_set
		# self.dhn_sim.update_network_component(name='sink_grid',
		# 									  type='sink',
		# 									  parameter='mdot_kg_per_s',
		# 									  value=self.mdot_grid_set)

		# # Update controller(s)
		# self.net.controller.at[ctrl.index('bypass_ctrl'), 'object'].set_mdot_setpoint(self.mdot_bypass_set)
		# self.dhn_sim.update_network_component(name='bypass_ctrl',
		# 									  type='controller',
		# 									  parameter='mdot_setpoint',
		# 									  value=self.mdot_bypass_set)

		# self.net.controller.at[ctrl.index('hex1_ctrl'), 'object'].set_mdot_setpoint(self.mdot_cons1_set)
		# self.net.controller.at[ctrl.index('hex2_ctrl'), 'object'].set_mdot_setpoint(self.mdot_cons2_set)
		# self.net.controller.at[ctrl.index('grid_ctrl'), 'object'].set_mdot_setpoint(self.mdot_grid_set)
		#
		# # Update tank
		# self.net.sink.at[sink.index('sink_tank'), 'mdot_kg_per_s'] = self.mdot_tank_out_set
		# self.net.ext_grid.at[source.index('supply_tank'), 't_k'] = self.T_tank_forward + 273.15
		# self.net.controller.at[ctrl.index('tank_ctrl'), 'object'].set_mdot_setpoint(self.mdot_tank_out_set)
		#
		# # Update load
		# self.net.heat_exchanger.at[hex.index('hex1'), 'qext_w'] = self.Qdot_cons1 * 1000
		# self.net.heat_exchanger.at[hex.index('hex2'), 'qext_w'] = self.Qdot_cons2 * 1000
		# self.net.heat_exchanger.at[hex.index('hp_evap'), 'qext_w'] = self.Qdot_evap * 1000