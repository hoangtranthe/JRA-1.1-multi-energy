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
from math import fabs

@dataclass
class VoltageController:

    ## Parameters
    delta_vm_upper_pu: float = 0.1
    delta_vm_lower_pu_hp_on: float = -0.1
    delta_vm_lower_pu_hp_off: float = -0.08
    delta_vm_deadband: float = 0.03

    hp_p_el_mw_rated: float = 0.1
    hp_p_el_mw_min: float = 0.35 * hp_p_el_mw_rated
    hp_p_el_mw_step: float = 0.01

    hp_operation_steps_min: int = 6

    k_p: float = 0.25

    ## Internal variables
    hp_operation_steps: int = 0

    ## Inputs
    vmeas_pu: float = 1. # voltage measurement at bus connect to HP in p.u.

    ## Output
    hp_p_el_mw_setpoint: float = 0.  # Proposed HP setpoint of el. consumption [MWe]
    hp_p_el_kw_setpoint: float = 0.  # Proposed HP setpoint of el. consumption [kWe]

    def __post_init__(self):

        if (self.hp_p_el_mw_step <= 0.):
            raise ValueError('parameter "hp_p_el_mw_step" must be a positive number')

        self.hp_p_el_mw_setpoint = self.hp_p_el_mw_min
        self.hp_p_el_kw_setpoint = 1e3 * self.hp_p_el_mw_setpoint

    def step_single(self, time):

        # Increment counter.
        self.hp_operation_steps += 1

        hp_off = (self.hp_p_el_mw_setpoint == 0)

        if hp_off and (self.hp_operation_steps < self.hp_operation_steps_min):
            return

        # Calculate voltage deviation.
        delta_v_meas_pu = self.vmeas_pu - 1

        delta_vm_lower_pu = self.delta_vm_lower_pu_hp_off if hp_off else self.delta_vm_lower_pu_hp_on

        # Check delta_vm_deadband.
        if delta_vm_lower_pu < delta_v_meas_pu < self.delta_vm_upper_pu:
            if (self.hp_p_el_mw_setpoint == 0 ) and (self.hp_operation_steps >= self.hp_operation_steps_min):
                self.hp_p_el_mw_setpoint = self.hp_p_el_mw_min
                self.hp_operation_steps = 0 # Turn on HP --> reset counter
            return

        # Calculate residual.
        res = self.k_p * (delta_v_meas_pu - self.delta_vm_deadband) / self.hp_p_el_mw_step
        step_res = int(res)

        # Use step functions to adapt HP setpoint.
        if fabs(res - step_res) > self.hp_p_el_mw_step:
            self.hp_p_el_mw_setpoint += self.hp_p_el_mw_step * (step_res + 1)

        # Check min and max for HP setpoint.
        if (self.hp_p_el_mw_setpoint > self.hp_p_el_mw_rated):
            self.hp_p_el_mw_setpoint = self.hp_p_el_mw_rated
        elif (self.hp_p_el_mw_setpoint < self.hp_p_el_mw_min) and (self.hp_operation_steps >= self.hp_operation_steps_min):
            self.hp_p_el_mw_setpoint = 0
            self.hp_operation_steps = 0 # Turn off HP --> reset counter
        elif (self.hp_p_el_mw_setpoint < self.hp_p_el_mw_min) and (self.hp_operation_steps < self.hp_operation_steps_min):
            self.hp_p_el_mw_setpoint = self.hp_p_el_mw_min

        self.hp_p_el_kw_setpoint = 1e3 * self.hp_p_el_mw_setpoint


if __name__ == '__main__':

    test = VoltageController()

