# -*- coding: utf-8 -*-

import numpy as np
from pandapower.control.basic_controller import Controller

try:
    import pplog as logging
except ImportError:
    import logging
logger = logging.getLogger(__name__)


class HPController(Controller):
    """
    Heat Pump Controller with Heat Pump consumption-based voltage control

    INPUT:
       **net** (attrdict) - Pandapower struct

       **hid** (int) - ID of the Heat Pupm that is controlled

       **tol** (float) - Voltage tolerance band at bus in Percent

       **in_service** (bool) - Indicates if the element is currently active


    OPTIONAL:
        **recycle** (bool, True) - Re-use of internal-data in a time series loop.
    """

    def __init__(self, net, hid, deadband, tol, in_service, level=0, order=0, recycle=True, load ="load", **kwargs):
        super().__init__(net, in_service=in_service, level=level, order=order, recycle=recycle,
                         **kwargs)
        self.hid = hid
        self.load = load
        self.deadband = deadband

        self.element_in_service = net[self.load].at[self.hid, "in_service"]

        self.controlled_bus = net[self.load].at[hid, "bus"]
        if self.controlled_bus in net.ext_grid.loc[net.ext_grid.in_service, 'bus'].values:
            logger.warning("Controlled Bus is Slack Bus - deactivating controller")
            self.set_active(net, False)
        elif self.controlled_bus in net.ext_grid.loc[
            ~net.ext_grid.in_service, 'bus'].values:
            logger.warning("Controlled Bus is Slack Bus with slack out of service - "
                           "not deactivating controller")


        self.hp_max_p_mw = net[self.load].at[hid, "max_p_mw"]
        self.hp_p_mw = net[self.load].at[hid, "p_mw"]

        self.tol = tol

        self.set_recycle(net)

    def set_recycle(self, net):
        allowed_elements = ["load"]
        if net.controller.at[self.index, 'recycle'] is False or self.load not in allowed_elements:
            # if recycle is set to False by the user when creating the controller it is deactivated or when
            # const control controls an element which is not able to be recycled
            net.controller.at[self.index, 'recycle'] = False
            return
        # these variables determine what is re-calculated during a time series run
        recycle = dict(load=True, gen=False, bus_pq=False)
        net.controller.at[self.index, 'recycle'] = recycle

    def timestep(self, net):
        self.hp_p_mw = net[self.load].at[self.hid, "p_mw"]

    def __repr__(self):
        s = '%s of %s %d' % (self.__class__.__name__, self.load, self.hid)
        return s

    def __str__(self):
        s = '%s of %s %d' % (self.__class__.__name__, self.load, self.hid)
        return s