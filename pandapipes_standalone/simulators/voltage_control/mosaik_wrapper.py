"""
    Model of the voltage controller.
"""

from itertools import count
from .simulator import VoltageController
from mosaik_api import Simulator
from typing import Dict
from statistics import mean

META = {
    'models': {
        'VoltageController': {
            'public': True,
            'params': [],
            'attrs': [
                # Inputs (none)
                # Output
                'P_hp_el_setpoint'
            ],
        },
    },
}


class VoltageControlSimulator(Simulator):

    step_size = 10
    eid_prefix = ''
    last_time = 0

    def __init__(self, META=META):
        super().__init__(META)

        # Per-entity dicts
        self.eid_counters = {}
        self.simulators: Dict[VoltageController] = {}
        self.entityparams = {}
        self.output_vars = {'P_hp_el_setpoint'}
        self.input_vars = {}

    def init(self, sid, step_size=10, eid_prefix="VoltageController"):

        self.step_size = step_size
        self.eid_prefix = eid_prefix

        return self.meta

    def create(self, num, model, **model_params):
        counter = self.eid_counters.setdefault(model, count())
        entities = []

        for _ in range(num):

            eid = '%s_%s' % (self.eid_prefix, next(counter))

            self.entityparams[eid] = model_params
            esim = VoltageController(**model_params)

            self.simulators[eid] = esim

            entities.append({'eid': eid, 'type': model})

        return entities

    def step(self, time, inputs):
        for eid, esim in self.simulators.items():
            data = inputs.get(eid, {})

            for attr, incoming in data.items():
                if attr in self.input_vars:
                    newval = mean(val for val in incoming.values())
                    setattr(esim, attr, newval)

                else:
                    raise AttributeError(f"VoltageControlSimulator {eid} has no input attribute {attr}.")

            esim.step_single(time)

        self.last_time = time

        return time + self.step_size

    def get_data(self, outputs):
        data = {}

        for eid, esim in self.simulators.items():
            requests = outputs.get(eid, [])
            mydata = {}

            for attr in requests:
                if attr in self.input_vars or attr in self.output_vars:
                    mydata[attr] = getattr(esim, attr)
                else:
                    raise AttributeError(f"VoltageControlSimulator {eid} has no attribute {attr}.")
            data[eid] = mydata
        return data


if __name__ == '__main__':
    test = VoltageControlSimulator()
