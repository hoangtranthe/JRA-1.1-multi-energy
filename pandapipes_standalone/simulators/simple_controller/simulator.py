"""Three way valve model."""

import matplotlib.pyplot as plt
import pandas as pd
from dataclasses import dataclass, field
import numpy as np

@dataclass
class SimpleFlexHeatController:
	"""
		Simple controller for the 'Flex Heat System' in NORDHAVN.
		Defines the mass flow in the system based on the consumer mass flow requirements.
	"""
	# Parameters
	T_tank_max: float = 72  # Maximum tank temperature - [degC]
	T_tank_min: float = 65  # Minimum tank temperature - [degC]
	T_hp_min: float = 70  # Minimum heat pump output temperature - [degC]

	# Variables
	## Input
	mdot_HEX1: float = 0.0  # Mass flow requested by the consumer 1 HEX - [kg/s]
	mdot_HEX2: float = 0.0  # Mass flow requested by the consumer 1 HEX - [kg/s]
	mdot_bypass: float = 0.5  # Mass flow through network bypass - [kg/s]
	T_tank_hot: float = 50  # Average tank temperature - [degC]
	T_hp_forward: float = 70  # Heat pump output temperature - [degC]

	## Internal Vars
	mdot_min: int = 0.11  # Minimum forward mass flow

	## Output
	mdot_1_supply: float = 0.0  # Supply 3 way valve mass flow at port 1 - [kg/s]
	mdot_2_supply: float = 0.0  # Supply 3 way valve mass flow at port 2 - [kg/s]
	mdot_3_supply: float = 0.0  # Supply 3 way valve mass flow at port 3 - [kg/s]

	mdot_1_return: float = 0.0  # Return 3 way valve mass flow at port 1 - [kg/s]
	mdot_2_return: float = 0.0  # Return 3 way valve mass flow at port 2 - [kg/s]
	mdot_3_return: float = 0.0  # Return 3 way valve mass flow at port 3 - [kg/s]

	Q_HP_set: float = 0  # Thermal power output of heat pump [kW]
	mdot_HP_out: float = 0  # HP forward mass flow [kg/s]

	state: int = 1  # state variable 1..5 - setting mass flows

	# Constants
	Cp_water = 4.180  # [kJ/(kg.degK)]

	def __post_init__(self):
		self.step_single()

	def step_single(self):
		self._update_state()
		self._do_state_based_control()

	def _do_state_based_control(self):
		self.mdot_2_supply = -(self.mdot_HEX1 + self.mdot_HEX2 + self.mdot_bypass)
		self.mdot_1_return = self.mdot_HEX1 + self.mdot_HEX2 + self.mdot_bypass

		if self.state == 1:  # Mode 1: External grid supplies heat, hp and tank inactive
			self.mdot_1_supply = - self.mdot_2_supply - self.mdot_min
			self.mdot_HP_out = 0

		elif self.state == 2:  # Mode 2: External grid supplies heat, HP charges tank
			self.mdot_1_supply = - self.mdot_2_supply - self.mdot_min
			self.mdot_HP_out = -3.5  # Set HP outflow

		elif self.state == 3:  # Mode 3: Discharge the tank, hp off
			self.mdot_1_supply = self.mdot_min
			self.Q_HP_set = 0
			self.mdot_HP_out = 0

		elif self.state == 4:  # Mode 4: Discharge the tank, hp on
			self.mdot_1_supply = self.mdot_min
			self.mdot_HP_out = -3.5

		elif self.state == 6:  # Mode 4: Discharge the tank, hp on
			self.mdot_1_supply = - self.mdot_2_supply / 2
			self.mdot_HP_out = -3.5

		self.mdot_3_supply = -(self.mdot_1_supply + self.mdot_2_supply)

		self.mdot_3_return = -self.mdot_3_supply

		self.mdot_2_return = -self.mdot_1_supply

	def _update_state(self):
		state_old = self.state
		if self.state is not 2:
			if self.T_tank_hot < self.T_tank_min:
				self.state = 2  # Mode 1: External grid suppies, tank inactive

		# elif self.state is 1:
		# 	#if self.T_hp_forward > self.T_hp_min:
		# 	if self.state is state_old:
		# 		self.state = 2  # Mode 2: Charge the tank, external supply

		elif self.state is 2:  # Mode 2: Charge the tank, external supply
			if self.T_tank_hot > self.T_tank_max:
				self.state = 3  # Mode 3: Discharge the tank, hp off

		if self.state != state_old:
			print(f"Controller state changed from {state_old} to {self.state}")

if __name__ == '__main__':

	test = SimpleFlexHeatController()

