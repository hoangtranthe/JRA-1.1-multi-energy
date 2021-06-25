# Copyright (c) 2021 by ERIGrid 2.0. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.

"""
	Voltage control model.
"""

from dataclasses import dataclass, field
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from ..util import clamp, safediv

P_HP_RATED = 100  # Rated heat pump electricity consumption [kWe]

@dataclass
class VoltageController:

	## Inputs
	# place inputs here

	## Output
	P_hp_el_setpoint: float = 0  # Proposed HP setpoint of el. consumption [kWe]

	def __post_init__(self):
		pass

	def step_single(self, time):
		self.P_hp_el_setpoint = doDummyControl(time) * P_HP_RATED
		pass

def doDummyControl(t):
	# Create sawtooth of consumption setpoints for a simulation period of 72h, amplitude=[0,1]
	from scipy import signal
	period = np.arange(0, 72 * 60 * 60, 1)
	freq = 1/(3*60*60)
	tri = np.abs(signal.sawtooth(2 * np.pi * freq * period))
	# plt.plot(period, tri)
	df = pd.DataFrame(tri, index=period, columns=['tri'])

	# Return proposed consumption setpoint at time t
	return df.loc[t, 'tri']

if __name__ == '__main__':

	test = VoltageController()

