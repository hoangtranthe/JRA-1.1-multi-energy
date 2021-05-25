__author__ = 'Tran The HOANG'


from heatpump_control import HPController
import math

class DiscreteHPControl(HPController):
    """
    Heat Pump Controller with Heat Pump consumption-based voltage control.
    INPUT:
        **net** (attrdict) - Pandapower struct
        **hid** (int) - ID of the heat pump that is controlled
    OPTIONAL:
        **tol** (float, 0.001) - Voltage tolerance band at bus in Percent (default: 1% = 0.01pu)
        **in_service** (bool, True) - Indicates if the controller is currently in_service
        **drop_same_existing_ctrl** (bool, False) - Indicates if already existing controllers of the same type and with the same matching parameters (e.g. at same element) should be dropped
    """

    def __init__(self, net, hid, delta_vm_upper_pu, delta_vm_lower_pu, deadband, load="load", tol=1e-3, in_service=True, order=0, drop_same_existing_ctrl=False,
                 matching_params=None, **kwargs):
        if matching_params is None:
            matching_params = {"hid": hid, 'load': load}
        super(DiscreteHPControl, self).__init__(
            net, hid, deadband, tol=tol, in_service=in_service, order=order, load=load,
            drop_same_existing_ctrl=drop_same_existing_ctrl, matching_params=matching_params,
            **kwargs)

        self.delta_vm_upper_pu = delta_vm_upper_pu
        self.delta_vm_lower_pu = delta_vm_lower_pu
        self.deadband = deadband
        self.hp_p_mw = net[self.load].at[hid, "p_mw"]
        self.hp_max_p_mw = net[self.load].at[hid, "max_p_mw"]
        self.hp_min_p_mw = net[self.load].at[hid, "min_p_mw"]

    def control_step(self, net):
        """
        Implements one step of the Discrete controller, always stepping only one tap position up or down
        """
        self.hp_p_mw = net[self.load].at[self.hid, "p_mw"]
        self.hp_max_p_mw = net[self.load].at[self.hid, "max_p_mw"]
        self.hp_min_p_mw = net[self.load].at[self.hid, "min_p_mw"]
        self.vmeas_pu = net.res_bus.at[self.controlled_bus, "vm_pu"]
        delta_v_meas_pu = self.vmeas_pu - 1

        if delta_v_meas_pu - self.delta_vm_upper_pu > self.deadband:
            hp_p_setpoint_mw = self.hp_p_mw + 0.05 * self.hp_max_p_mw

            if hp_p_setpoint_mw < self.hp_max_p_mw:
                self.hp_p_mw = hp_p_setpoint_mw

            else:
                self.hp_p_mw = self.hp_max_p_mw


        elif delta_v_meas_pu - self.delta_vm_lower_pu < -self.deadband and self.hp_p_mw > self.hp_min_p_mw:
            hp_p_setpoint_mw = self.hp_p_mw - 0.02 * self.hp_max_p_mw

            if hp_p_setpoint_mw >= self.hp_min_p_mw:
                self.hp_p_mw = hp_p_setpoint_mw

            elif hp_p_setpoint_mw < self.hp_min_p_mw:
                self.hp_p_mw = self.hp_min_p_mw


        elif delta_v_meas_pu - self.delta_vm_lower_pu < -self.deadband and self.hp_p_mw == self.hp_min_p_mw:
            self.hp_p_mw = self.hp_min_p_mw

        net[self.load].at[self.hid, "p_mw"] = self.hp_p_mw

    def is_converged(self, net):
        """
        Checks if the voltage is within the desired voltage band, then returns True
        """
        if not self.hid in net[self.load].index or \
           not net[self.load].at[self.hid, 'in_service']:
            return True

        self.vmeas_pu = net.res_bus.at[self.controlled_bus, "vm_pu"]
        delta_v_meas_pu = self.vmeas_pu - 1


        if delta_v_meas_pu > self.delta_vm_upper_pu + self.deadband and net[self.load].at[self.hid, "p_mw"] == self.hp_max_p_mw:
            return True

        elif delta_v_meas_pu < self.delta_vm_lower_pu - self.deadband and net[self.load].at[self.hid, "p_mw"] == self.hp_min_p_mw:
            return True

        return self.delta_vm_lower_pu - self.deadband <= delta_v_meas_pu <= self.delta_vm_upper_pu + self.deadband
