# Copyright (c) 2021 by ERIGrid 2.0. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.

"""
    An entity which loads a timeseries of relative demand and repeats it when asked
"""

import time as t_time
import datetime
import logging
import os
from itertools import count
from dataclasses import dataclass, field
from typing import List
import mosaik_api
import pandas as pd
import numpy as np

META = {
    'models': {
        'MultiFractalDistorter': {
            'public': True,
            'params': ['L', 'L_min', 'sigma'],
            'attrs': ['in', 'out'],
        },
    },
}

MY_DIR = os.path.abspath(os.path.dirname(__file__))


@dataclass
class MyMultiFractal:
    L: float                                 # Length of top-level interval
    min_L: float                             # Length of shortest interval
    sigma: float                             # splitting factor (relative split is 1+sigma, 1-sigma)
    use_discrete: bool = False               # Use 1 +/- sigma? Otherwise, use normal distribution
    raw_val: float = 0.0                     # Value of data

    N: float = field(init=False)             # Number of levels in stack
    L_0: float = field(init=False)           # Current top-level interval starting point
    r: List[float] = field(init=False)       # splitting factor at each level
    prev_i: List[float] = field(init=False)  # whether we are in the first or second half of the interval in each iteration
    val: float = field(init=False)           # Number of levels in stack

    def __post_init__(self):
        self.L_0 = 0.0
        self.N = int(np.ceil(np.log2(self.L / self.min_L)))
        self.r = [0.0] * self.N
        self.prev_i = [0] * self.N
        self._first_run = True
        self.val = self.raw_val

    def calc_val(self, t):
        """
        .
        """

        self.val = self.raw_val * self.get_factor(t)

    def get_factor(self, t):
        """
        .
        """

        rollover = self._first_run

        while self.L_0 + self.L < t:

            self.L_0 += self.L
            rollover = True

        t_rel = t - self.L_0
        self._first_run = False

        return self._get_factor(t_rel, self.L, S=0.0, n=0, draw_new=rollover)

    def _get_factor(self, t, L, S, n, draw_new=False):
        """
            Recursively-invoked function which gets the factor for the multifractal at level n,
            where the width is L, the length in the superinterval on all levels above is S,
            at a time t
            :param eid:
            :param t:
            :param L:
            :param S:
            :param n:
            :param draw_new:
        """

        if L < self.min_L:

            return 1

        if draw_new:

            self.r[n] = self._draw_new()

        i_n = int(t > L / 2 + S)
        S_below = S + i_n * L / 2
        r_local = 1 + self.sigma * self.r[n] * (1 - 2 * i_n)
        draw_new_below = draw_new or not self.prev_i[n] == i_n
        self.prev_i[n] = i_n

        return r_local * self._get_factor(t, L/2, S_below, n+1, draw_new=draw_new_below)

    def _draw_new(self):
        """
        .
        """

        if self.use_discrete:

            return 2 * np.random.randint(2) - 1

        else:

            return min(0.9, max(0.1, np.random.normal(0, 1)))


class MultiFractalMultiplier(mosaik_api.Simulator):
    def __init__(self, META=META):
        super().__init__(META)

        self.verbose = False
        self.time_dict = {
            'step': 0,
            'get_data': 0,
        }

        # Per-entity dicts
        self.eid_counters = {}
        self.simulator_entities = {}
        self.entityparams = {}

    def init(self, sid, step_size=5, eid_prefix="MMF", verbose=False):
        """
        Initialize the simulator with the ID 'sid' and apply
        additional parameters (sim_params) sent by mosaik.
        Return the meta data 'meta'.
        """

        self.step_size = step_size
        self.eid_prefix = eid_prefix

        return self.meta

    def create(self, num, model, L=3600, L_min=10, sigma=0.05):
        """
        Create 'num' instances of model using the provided 'model_params'.
        """

        counter = self.eid_counters.setdefault(model, count())
        entities = []

        for _ in range(num):

            eid = '{0}_{1}_{2}'.format(self.eid_prefix, model, next(counter))

            esim = MyMultiFractal(L=L, min_L=L_min, sigma=sigma)
            self.simulator_entities[eid] = esim

            entities.append({'eid': eid, 'type': model, 'sigma':0.3})

        return entities

    ###
    #  Functions used online
    ###

    def step(self, time, inputs):
        """
        Perform the next simulation step from time 'time'using input values
        from inputs and return the new simulation time (the time at which step()
        should be called again).
        """

        t_start = t_time.time()

        for eid, esim in self.simulator_entities.items():

            data = inputs.get(eid, {})

            for attr, vals in data.items():

                if attr == 'in':

                    esim.raw_val = np.mean(list(vals.values()))

            esim.calc_val(time)

        t_stop = t_time.time()
        t_delta = t_stop - t_start
        self.time_dict['step'] += t_delta

        return time + self.step_size

    def get_data(self, outputs):
        """
        Return the data for the requested attributes in outputs.
        """

        t_start = t_time.time()

        data = {}

        for eid, esim in self.simulator_entities.items():

            requests = outputs.get(eid, [])
            mydata = {}

            for attr in requests:

                if attr == 'out':

                    mydata[attr] = esim.val

                elif attr == 'in':

                    None

                else:

                    raise RuntimeError("MultiFractalMultiplier {0} has no attribute {1}.".format(eid, attr))

            data[eid] = mydata

        t_stop = t_time.time()
        t_delta = t_stop - t_start
        self.time_dict['step'] += t_delta

        return data

    def finalize(self):
        """
        Method to do some clean-up operations after the simulation finished.
        """

        print('-' * 80)
        print('Electrical power Multi-Fractal-Distorter elpased time summary:')
        print('-' * 80)

        for function, elpased_time in self.time_dict.items():

            print('{0}: {1}'.format(function, str(datetime.timedelta(seconds=elpased_time))))


if __name__ == '__main__':
    # mosaik_api.start_simulation(PPPowerSystem())
    mmf = MyMultiFractal(3600, 1, 1.0)
    ts = np.arange(3600)
    ys = [mmf.get_factor(t) for t in ts]
