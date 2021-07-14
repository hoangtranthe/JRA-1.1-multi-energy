import pandas as pd
import pandapipes as pp
import pandapipes.control.run_control as run_control
from pandapipes.pandapipes_net import pandapipesNet
import sys
from .io.import_export import *
from .component_models.valve_control import CtrlValve

# Do not print python UserWarnings
if not sys.warnoptions:
    import warnings


def add_network_components_to(net, components_dict):
    # TODO: Add components via pandapipes.create()
    # pp.create_sinks()
    # pp.create_sources()
    # pp.create_pipes()
    # pp.create_junctions()
    _create_junctions(net)  # TODO: To be replaces with junction import
    # pp.create_valves()
    # _create_ext_grids()
    # _create_controllers(net)
    # _create_heat_exchangers()
    pass

def save_network(net, file_path=''):
    export_network_components(net, type='json_default', path=file_path)

def run_hydraulic_control(net):
    # Ignore user warnings of control
    try:
        run_control(net, max_iter=100)

    except:
        # Throw UserWarning
        warnings.warn(f'ControllerNotConverged: Maximum number of iterations per controller is reached at time t={self.cur_t}.', UserWarning)

def _run_static_pipeflow(net):
    pp.pipeflow(net, transient=False, mode="all", max_iter=100, run_control=True, heat_transfer=True)
    # Store results
    # self._store_output(label='static')

def _run_dynamic_pipeflow(net):
    if compare_to_static_results:
        # static temperature flow calculation
        _run_static_pipeflow()

        # Store results
        _store_output(label='static')

    # Dynamic heat flow distribution
    _internal_heatflow_calc()

    # Store results
    # self._store_output(label='dynamic')

def _internal_heatflow_calc(self):
    # Define forward and backward pipe sequence
    forward_pipe_list = self._get_forward_pipe_stream()
    backward_pipe_list = self._get_backward_pipe_stream()

    _calc_forward_pipe_tempflow()
    _calc_backward_pipe_tempflow()

def _calc_forward_pipe_tempflow(self):
    for pipe in forward_pipe_list:
        _internal_tempflow_calc(pipe)
        _update_temperature_flow(pipe)

def _calc_consumer_return_temperature(hex):
    h = self.heat_exchanger
    p = self.pipe

    from_j_id = self.net.heat_exchanger.at[h.index(hex), 'from_junction']
    to_j_id = self.net.heat_exchanger.at[h.index(hex), 'to_junction']
    qext_w = self.net.heat_exchanger.at[h.index(hex), 'qext_w']
    forward_temp = self.net.res_junction.at[from_j_id, 't_k']
    mdot = self.net.res_heat_exchanger.at[h.index(hex), 'mdot_from_kg_per_s']
    cp_w = self.CP_WATER

    # Set forward temperature to hex component
    self.net.res_heat_exchanger.at[h.index(hex), 't_from_k'] = forward_temp

    # Calc return temperature at hex component
    return_temp = forward_temp - qext_w / (cp_w * mdot)

    # Set return temperature at hex component and connected junctions and pipes
    self.net.res_heat_exchanger.at[h.index(hex), 't_to_k'] = return_temp
    self.net.res_junction.at[to_j_id, 't_k'] = return_temp

    conn_p_name = self.net.pipe['name'].loc[self.net.pipe['from_junction'] == to_j_id].values.tolist()
    for pipe in conn_p_name:
        self.net.res_pipe.at[p.index(pipe), 't_from_k'] = return_temp

def _calc_backward_pipe_tempflow():
    for pipe in self.backward_pipe_list:
        _internal_tempflow_calc(pipe)
        _update_temperature_flow(pipe)

def _get_forward_pipe_stream():
    # TODO: Make this applicable to any network topology
    forwardpipes = ['l1s', 'l2s', 'l3s', 'l4s', 'l5s', 'l6s', 'l1s_tank']
    pipestream = _get_pipe_flow_direction_by_pressures()
    forwardpipestream = pipestream.loc[pipestream.isin(forwardpipes)]
    return (forwardpipestream.values)

def _get_backward_pipe_stream():
    # TODO: Make this applicable to any network topology
    backwardpipes = ['l1r', 'l2r', 'l3r', 'l4r', 'l5r', 'l6r', 'l1r_tank']
    pipestream = _get_pipe_flow_direction_by_pressures()
    backwardpipestream = pipestream.loc[pipestream.isin(backwardpipes)]
    return (backwardpipestream.values)

def _get_pipe_flow_direction_by_pressures():
    # Sort pipes according to their pressures
    index = net.res_pipe.sort_values('p_from_bar', ascending=False).index
    list = index.values

    # Reindex pipes according to pressure drop
    pipenames = net.pipe['name'].reindex(list)

    return pipenames

def _internal_tempflow_calc(pipe):
    # Set required input data
    p = self.pipe
    j = self.junction
    net = self.net
    mf = net.res_pipe.at[p.index(pipe), 'mdot_from_kg_per_s']
    Cp_w = self.CP_WATER
    dx = net.pipe.at[p.index(pipe), 'length_km'] * 1000
    v_mean = net.res_pipe.at[p.index(pipe), 'v_mean_m_per_s']
    alpha = net.pipe.at[p.index(pipe), 'alpha_w_per_m2k']
    dia = net.pipe.at[p.index(pipe), 'diameter_m']
    loss_coeff = alpha * math.pi * dia  # Heat loss coefficient in [W/mK]
    Ta = net.pipe.at[p.index(pipe), 'text_k']

    # Get junction connected to pipe inlet
    j_in_id = self.net.pipe.at[p.index(pipe), 'from_junction']
    j_in_name = self.net.junction.at[j_in_id, 'name']

    # Get historic inlet temperature
    df = pd.DataFrame.from_dict(self.store['dynamic'])

    # Get historic inlet temperature
    if not df.empty:
        dt = dx / v_mean
        delay_t = self.cur_t - dt
        Tin = np.interp(delay_t, df.index, df['temp_' + j_in_name]) + 273.15  # TODO: Reduce calls due to performance
    else:
        Tin = net.res_junction.at[j_in_id, 't_k']

    # Static temperature drop
    # Tin = net.res_junction.at[j_in_id, 't_k']

    # Set current inlet temperature of pipe
    net.res_pipe.at[p.index(pipe), 't_from_k'] = Tin

    # Dynamic temperature drop along a pipe
    exp = - (loss_coeff * dx) / (Cp_w * mf)
    Tout = Ta + (Tin - Ta) * math.exp(exp)

    # Set pipe outlet temperature
    net.res_pipe.at[p.index(pipe), 't_to_k'] = Tout

def _update_temperature_flow(act_pipe):
    p = self.pipe
    v = self.valve
    j = self.junction

    # Get connected junctions (direct and indirect)
    # Check direct connection via junction
    conn_j_id = []
    conn_j_id.append(self.net.pipe.at[p.index(act_pipe), 'to_junction'])
    # Check connection via valve
    conn_v_name = self.net.valve['name'].loc[self.net.valve['from_junction'].isin(conn_j_id)].values.tolist()
    for valve in conn_v_name:
        opened = self.net.valve.at[v.index(valve), 'opened']
        if opened:
            conn_j_id.append(self.net.valve.at[v.index(valve), 'to_junction'])

    # Set temperature at connected junctions
    conn_j_name = self.net.junction['name'].iloc[conn_j_id].values.tolist()
    for junction in conn_j_name:
        self._set_pipe_inlet_temperature_at_junction(junction)

    # Get connected hex consumer
    hex_name = self.net.heat_exchanger['name'].loc[self.net.heat_exchanger['from_junction'].isin(conn_j_id)].values.tolist()
    for hex in hex_name:
        # Set temperature at the return side of each hex consumer
        self._calc_consumer_return_temperature(hex)

def _set_pipe_inlet_temperature_at_junction(junction):
    j = self.junction
    p = self.pipe
    v = self.valve
    conn_j_id = [j.index(junction)]
    # Get number of incoming pipes
    # Check connection via valve
    conn_v_name = self.net.valve['name'].loc[self.net.valve['to_junction'].isin(conn_j_id)].values.tolist()
    for valve in conn_v_name:
        opened = self.net.valve.at[v.index(valve), 'opened']
        if opened:
            conn_j_id.append(self.net.valve.at[v.index(valve), 'from_junction'])
    pipes_in = self.net.pipe['name'].loc[self.net.pipe['to_junction'].isin(conn_j_id)].values.tolist()

    mfsum = []
    mtsum = []
    if pipes_in:
        for name in pipes_in:
            # Do temperature mix weighted by share of incoming mass flow
            mdot = self.net.res_pipe.at[p.index(name), 'mdot_from_kg_per_s']
            t_in = self.net.res_pipe.at[p.index(name), 't_to_k']
            mfsum.append(mdot)
            mtsum.append(mdot * t_in)
        Tset = (1 / sum(mfsum)) * sum(mtsum)
    else:
        raise AttributeError(f"Junction '{junction}' not connected to a network pipe.")

    self.net.res_junction.at[j.index(junction), 't_k'] = Tset


def _create_junctions(net):
    # create nodes (with initial pressure and temperature)
    pn_init = 6
    tfluid_init = 273.15 + 75
    pp.create_junction(net, pn_bar=pn_init, tfluid_k=tfluid_init, name="n1s", geodata=(0, 1))
    pp.create_junction(net, pn_bar=pn_init, tfluid_k=tfluid_init, name="n1r", geodata=(0, -2.1))
    pp.create_junction(net, pn_bar=pn_init, tfluid_k=tfluid_init, name="n2s", geodata=(3, 1))
    pp.create_junction(net, pn_bar=pn_init, tfluid_k=tfluid_init, name="n2r", geodata=(3, -2.1))
    pp.create_junction(net, pn_bar=pn_init, tfluid_k=tfluid_init, name="n3s", geodata=(6, 1))
    pp.create_junction(net, pn_bar=pn_init, tfluid_k=tfluid_init, name="n3s_tank", geodata=(6, 3))  # create hp+tank injection point
    pp.create_junction(net, pn_bar=pn_init, tfluid_k=tfluid_init, name="n3sv", geodata=(6, 1.4))  # create tank valve
    pp.create_junction(net, pn_bar=pn_init, tfluid_k=tfluid_init, name="n3r", geodata=(6, -2.1))
    pp.create_junction(net, pn_bar=pn_init, tfluid_k=tfluid_init, name="n3r_tank", geodata=(6, -4.1))
    pp.create_junction(net, pn_bar=pn_init, tfluid_k=tfluid_init, name="n4s", geodata=(10, 1))
    pp.create_junction(net, pn_bar=pn_init, tfluid_k=tfluid_init, name="n4r", geodata=(11, -2.1))
    pp.create_junction(net, pn_bar=pn_init, tfluid_k=tfluid_init, name="n5sv", geodata=(10, 1.5))
    pp.create_junction(net, pn_bar=pn_init, tfluid_k=tfluid_init, name="n5s", geodata=(10, 4))
    pp.create_junction(net, pn_bar=pn_init, tfluid_k=tfluid_init, name="n5r", geodata=(11, 4))
    pp.create_junction(net, pn_bar=pn_init, tfluid_k=tfluid_init, name="n6s", geodata=(15, 1))
    pp.create_junction(net, pn_bar=pn_init, tfluid_k=tfluid_init, name="n6r", geodata=(16, -2.1))
    pp.create_junction(net, pn_bar=pn_init, tfluid_k=tfluid_init, name="n7sv", geodata=(15, 1.5))
    pp.create_junction(net, pn_bar=pn_init, tfluid_k=tfluid_init, name="n7s", geodata=(15, 4))
    pp.create_junction(net, pn_bar=pn_init, tfluid_k=tfluid_init, name="n7r", geodata=(16, 4))
    pp.create_junction(net, pn_bar=pn_init, tfluid_k=tfluid_init, name="n8s", geodata=(19, 1))
    pp.create_junction(net, pn_bar=pn_init, tfluid_k=tfluid_init, name="n8r", geodata=(19, -2.1))