# Copyright (c) 2021 by ERIGrid 2.0. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.

"""
    Time series player/simulator
"""

import matplotlib.pyplot as plt
import pandas as pd
from dataclasses import dataclass, field
import numpy as np
import datetime
import os
from pathlib import Path

@dataclass
class TSSim:
    """
        Time series simulator that plays a given time series at the given date.
    """

    # Parameters
    t_start : datetime.datetime = None
    fieldname: str = 'P'  # Name of the field in the dataframe to use.

    # Variables
    ## Internal
    cur_t: datetime.datetime = None
    current_h_start: datetime.datetime = None
    current_h_stop: datetime.datetime = None
    current_y_start: datetime.datetime = None
    current_y_stop: datetime.datetime = None

    ## Input
    series: pd.DataFrame() = None

    ## Output
    val: float = 0.0  # Value to return from the time series played

    def __post_init__(self):

        self.sim_check()
        self.update_hour_bin()
        self.step_single(0)

    def sim_check(self):

        self.t_start = pd.to_datetime(self.t_start)
        self.cur_t = self.t_start

        assert self.t_start in self.series.index, "Simulation starting date: \"{0}\", is not in time series input.".format(self.t_start)

    def update_hour_bin(self):
            self.cur_date = pd.to_datetime(self.cur_t.date())
            self.cur_date_hour = self.cur_date + pd.Timedelta(hours=self.cur_t.hour)
            self.next_date_hour = self.cur_date_hour + pd.Timedelta(hours=1)

            self.current_h_start, self.current_y_start = (self.cur_date_hour, self.series[self.fieldname].loc[self.cur_date_hour])
            self.current_h_stop, self.current_y_stop = (self.next_date_hour, self.series[self.fieldname].loc[self.next_date_hour])

    def step_single(self, t):

            """
            Method to update the time serie simulator power draw.
            input: simulation time
            output: active power draw -> P
            """

            self.cur_t = self.t_start + pd.Timedelta(seconds=t)

            if self.cur_t in self.series.index:
                self.P = self.series[self.fieldname][self.cur_t]

            else:
                ix = np.searchsorted(self.series[self.fieldname].index, self.cur_t)

                if ix == 0:
                    self.P = self.series[self.fieldname].iloc[0]  # Return first value
                elif ix == len(self.series[self.fieldname]):
                    self.P = self.series[self.fieldname].iloc[-1]  # Return last value
                else:
                    if self.current_h_start < self.cur_t < self.current_h_stop:
                        # We are still in the current bin. Interpolate linearly.
                        self.P = self.current_y_start * (1 - (self.cur_t - self.current_h_start) / (self.current_h_stop - self.current_h_start)) + self.current_y_stop * ((self.cur_t - self.current_h_start) / (self.current_h_stop - self.current_h_start))
                    else:
                        # We are in a different bin! Update our values then interpolate.
                        self.update_hour_bin()
                        self.P = self.current_y_start * (1 - (self.cur_t - self.current_h_start) / (self.current_h_stop - self.current_h_start)) + self.current_y_stop * ((self.cur_t - self.current_h_start) / (self.current_h_stop - self.current_h_start))


if __name__ == '__main__':
    cwd = os.getcwd()  # Get current working directory
    p = Path(cwd).parents[1]  # Get two parents up in the folder structure

    # Extra test data set from the resource folder
    store = pd.HDFStore(p / 'resources/heat/time_series/NORDHAVN_2018_1H_heat_TS.h5')  
    series = store[store.keys()[0]]
    store.close()

    # Instantiate a test class object
    test = TSSim(series=series, t_start='2018-11-18 00:00:00')
