"""
    A simple data collector that prints all data when the simulator ends.
"""

import datetime
import time as t_time
import collections
import logging
import mosaik_api
import pandas as pd


META = {
    'models': {
        'MultiCollector': {
            'public': True,
            'any_inputs': True,
            'params': [],
            'attrs': [],
            },
        },
    }


class MultiCollector(mosaik_api.Simulator):
    def __init__(self):
        super().__init__(META)

        self.verbose = False
        self.time_dict = {
            'step': 0,
            'finalize': 0,
        }

        self.eid = None
        self.data = collections.defaultdict(lambda: collections.defaultdict(list))
        self.time_list = []

        self.step_size = None

    def init(self, sid, step_size, print_results=True, save_h5=True, h5_storename='multicollectorstore', verbose=False):
        """
        Initialize the simulator with the ID 'sid' and apply
        additional parameters (sim_params) sent by mosaik.
        Return the meta data 'meta'.
        """

        self.step_size = step_size
        self.print_results = print_results
        self.save_h5 = save_h5
        self.h5_storename = h5_storename
        self.verbose = verbose

        return self.meta

    def create(self, num, model):
        """
        Create 'num' instances of model using the provided 'model_params'.
        """

        if num > 1 or self.eid is not None:

            raise RuntimeError("Can only create one instance of Collector per simulator.")

        self.eid = 'Collector'

        return [{'eid': self.eid, 'type': model}]

    def step(self, time, inputs):
        """
        Perform the next simulation step from time 'time'using input values
        from inputs and return the new simulation time (the time at which step()
        should be called again).
        """

        t_start = t_time.time()

        data = inputs[self.eid]

        for attr, values in data.items():

            for src, value in values.items():

                self.data[src][attr].append(value.copy())

        self.time_list.append(time)

        t_stop = t_time.time()
        t_delta = t_stop - t_start
        self.time_dict['step'] += t_delta

        return time + self.step_size

    def finalize(self):
        """
        Method to do some clean-up operations after the simulation finished.
        """

        t_start = t_time.time()

        if self.print_results:

            print('Collected data:')

            for sim, sim_data in sorted(self.data.items()):

                print('- {0}'.format(sim))

                for attr, values in sorted(sim_data.items()):

                    print('  - {0}:'.format(attr))
                    print(values)

        if self.save_h5:
            framename= ''

            store = pd.HDFStore('./test/' + self.h5_storename)

            for src, data in self.data.items():

                for attr, values in data.items():

                    framename = src + '/' + attr
                    panel = pd.DataFrame(values, index=self.time_list)
                    store[framename] = panel

            store.close()
            print('Saved to store: {0}, dataframe: {1}'.format(self.h5_storename, framename))

        t_stop = t_time.time()
        t_delta = t_stop - t_start
        self.time_dict['finalize'] += t_delta

        print('-' * 80)
        print('MultiCollector elapsed time summary:')
        print('-' * 80)

        for function, elpased_time in self.time_dict.items():

            print('{0}: {1}'.format(function, str(datetime.timedelta(seconds=elpased_time))))
        



if __name__ == '__main__':
    mosaik_api.start_simulation(MultiCollector())
