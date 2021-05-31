"""
    Models a district-integrated heat pump (one entity = one heat pump)
"""

from itertools import count
from .simulator import ConstantTcondHP
from mosaik_api import Simulator
from typing import Dict
from statistics import mean

META = {
    'models': {
        'ConstantTcondHP': {
            'public': True,
            'params': [
                'P_rated', 'lambda_comp', 'P_0', 'eta_sys', 'eta_comp', 'dt', 'T_cond_out_target', 'opmode'
            ],
            'attrs': [
                # Input
                'T_cond_in', 'T_evap_in', 'Q_set',
                'mdot_cond_in', 'mdot_evap_in', 'opmode',
                # Output
                'Qdot_cond', 'Qdot_evap',
                'P_effective', 'W_effective',
                'Q_set', 'W_requested',
                'mdot_cond_out', 'mdot_evap_out',
                'T_cond_out', 'T_evap_out',
                'eta_hp'
            ],
        },
    },
}


class ConstantTcondHPSimulator(Simulator):

    step_size = 10
    eid_prefix = ''
    last_time = 0

    def __init__(self, META=META):
        super().__init__(META)

        # Per-entity dicts
        self.eid_counters = {}
        self.simulators: Dict[ConstantTcondHP] = {}
        self.entityparams = {}
        self.output_vars = {
            'eta_hp', 'Qdot_cond', 'Qdot_evap', 'P_effective', 'W_requested', 'W_effective',
            'T_cond_out', 'T_evap_out', 'mdot_cond_out', 'mdot_evap_out'}
        self.input_vars = {'T_cond_in', 'T_evap_in', 'Q_set', 'mdot_cond_in', 'mdot_evap_in', 'opmode'}

    def init(self, sid, step_size=10, eid_prefix="DistrictHP"):
        self.step_size = step_size
        self.eid_prefix = eid_prefix

        return self.meta

    def create(self, num, model, **model_params):

        counter = self.eid_counters.setdefault(model, count())
        entities = []

        for _ in range(num):

            eid = '%s_%s' % (self.eid_prefix, next(counter))

            self.entityparams[eid] = model_params
            esim = ConstantTcondHP(**model_params)

            self.simulators[eid] = esim

            entities.append({'eid': eid, 'type': model})

        return entities

    def step(self, time, inputs):
        for eid, esim in self.simulators.items():

            data = inputs.get(eid, {})

            for attr, incoming in data.items():
                if attr in self.input_vars:
                    if 'mdot' in attr:
                        newval = mean(-val for val in incoming.values())  # Flip the sign of incoming mass flows to comply with generator convention.
                        setattr(esim, attr, newval)

                    else:
                        newval = mean(val for val in incoming.values())
                        setattr(esim, attr, newval)

                else:
                    raise AttributeError(f"ConstantTcondHPSim {eid} has no input attribute {attr}.")

            # for _ in range(time - self.last_time):
            #     esim.step_single()
            esim.step_single()

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
                    raise AttributeError(f"ConstantTcondHPSim {eid} has no attribute {attr}.")

            data[eid] = mydata

        return data


if __name__ == '__main__':

    test = ConstantTcondHPSimulator()
