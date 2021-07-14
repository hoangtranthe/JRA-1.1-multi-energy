from dataclasses import dataclass, field
import pandapipes as pp
import pandapipes.plotting as plot
from pandapipes.pandapipes_net import pandapipesNet
from .dh_network_simulator_core import *
from .io.import_export import *
# Do not print python UserWarnings
import sys

if not sys.warnoptions:
    import warnings


@dataclass
class DHNetworkSimulator():
    """
        District Heating Network Simulator class.
    """

    logging: str = 'default'  # Logging modes: 'default', 'all'
    net: pandapipesNet = field(init=False)

    def __init__(self):
        self._set_logging()

    def _set_logging(self):
        if self.logging is 'default':
            warnings.filterwarnings("ignore", message="Pipeflow converged, however, the results are phyisically incorrect as pressure is negative at nodes*")
        elif self.logging is 'all':
            pass
        else:
            warnings.warn(f"Logging mode '{self.logging}' does not exist. Logging mode set to 'all'.")

    def load_network(self, from_file=False, path='', format='json_default', net=pandapipesNet):
        if from_file is True:
            # create empty network
            net = pp.create_empty_network("net", add_stdtypes=False)

            # create fluid
            pp.create_fluid_from_lib(net, "water", overwrite=True)

            # import network components
            self.net = import_network_components(net, format=format, path=path)
            # export_network_components(net, format=format, path='./resources/dh_network/export/')

        self.net = net

    def run_simulation(self, sim_mode='static'):
        # Run hydraulic flow (steady-state)
        self.run_hydraulic_control(self.net)

        if sim_mode is 'static':
            self._run_static_pipeflow(self.net)
        elif sim_mode is 'dynamic':
            self._run_dynamic_pipeflow(self.net)
        else:
            warnings.warn(f"Simulation mode '{sim_mode}' does not exist. Simulation has stopped.")

    def update_network_component(self, type, name, parameter, value):
        if type is 'sink':
            component = self.net.sink
        elif type is 'source':
            component = self.net.source
        elif type is 'junction':
            component = self.net.junction
        elif type is 'valve':
            component = self.net.valve
        elif type is 'ext_grid':
            component = self.net.ext_grid
        elif type is 'heat_exchanger':
            component = self.net.heat_exchanger

        else:
            warnings.warn(f"Component {name} cannot be found. Update not successful.")

        # Search for component index by name
        index = component.name.to_list().index(name)
        # Set new value
        component.at[index, parameter] = value

    def update_network_controller(self, name, parameter, value):
        pass

    def _add_to_component_list(self, df):
        if not self.componentList:
            self.componentList = [df]
        else:
            self.componentList.append(df)

    def _create_external_grid(self):
        net = self.net
        j = self.junction
        t_supply_grid_k = 273.15 + self.T_supply_grid
        mdot_init = self.mdot_grid

        # create external grid
        pp.create_ext_grid(net, junction=j.index('n1s'), p_bar=self.P_grid_bar, t_k=t_supply_grid_k, name="ext_grid", type="pt")
        self.componentList.append(self.net.ext_grid)

        # create sink and source
        pp.create_sink(net, junction=j.index('n1r'), mdot_kg_per_s=mdot_init, name="sink_grid")
        pp.create_source(net, junction=j.index('n1r'), mdot_kg_per_s=0, name='source_grid')

        self.sink = net.sink['name'].tolist()
        self.componentList.append(self.net.sink)

        self.source = net.ext_grid['name'].tolist()
        self._add_to_component_list(self.net.source)

    def _create_pipes(self):
        net = self.net
        j = self.junction

        l01 = 0.5

        # supply pipes
        pp.create_pipe_from_parameters(net, from_junction=j.index('n1s'), to_junction=j.index('n2s'), length_km=l01,
                                       diameter_m=0.1, k_mm=0.01, sections=1, alpha_w_per_m2k=1.5,
                                       text_k=273.15 + 8, name="l1s")
        pp.create_pipe_from_parameters(net, from_junction=j.index('n3sv'), to_junction=j.index('n3s'), length_km=0.01,
                                       diameter_m=0.1, k_mm=0.01, sections=1, alpha_w_per_m2k=1.5,
                                       text_k=273.15 + 8, name="l1s_tank")  # create tank pipe connection
        pp.create_pipe_from_parameters(net, from_junction=j.index('n3s'), to_junction=j.index('n4s'), length_km=0.01,
                                       diameter_m=0.1, k_mm=0.01, sections=1, alpha_w_per_m2k=1.5,
                                       text_k=273.15 + 8, name="l2s")
        pp.create_pipe_from_parameters(net, from_junction=j.index('n4s'), to_junction=j.index('n5sv'), length_km=0.01,
                                       diameter_m=0.1, k_mm=0.01, sections=1, alpha_w_per_m2k=1.5,
                                       text_k=273.15 + 8, name="l3s")
        pp.create_pipe_from_parameters(net, from_junction=j.index('n4s'), to_junction=j.index('n6s'), length_km=0.5,
                                       diameter_m=0.1, k_mm=0.01, sections=1, alpha_w_per_m2k=1.5,
                                       text_k=273.15 + 8, name="l4s")
        pp.create_pipe_from_parameters(net, from_junction=j.index('n6s'), to_junction=j.index('n7sv'), length_km=0.01,
                                       diameter_m=0.1, k_mm=0.01, sections=1, alpha_w_per_m2k=1.5,
                                       text_k=273.15 + 8, name="l5s")
        pp.create_pipe_from_parameters(net, from_junction=j.index('n6s'), to_junction=j.index('n8s'), length_km=0.01,
                                       diameter_m=0.1, k_mm=0.01, sections=1, alpha_w_per_m2k=1.5,
                                       text_k=273.15 + 8, name="l6s")

        # return pipes
        pp.create_pipe_from_parameters(net, from_junction=j.index('n2r'), to_junction=j.index('n1r'), length_km=l01,
                                       diameter_m=0.1, k_mm=0.01, sections=1, alpha_w_per_m2k=1.5,
                                       text_k=273.15 + 8, name="l1r")
        pp.create_pipe_from_parameters(net, from_junction=j.index('n3r'), to_junction=j.index('n3r_tank'), length_km=0.01,
                                       diameter_m=0.1, k_mm=0.01, sections=1, alpha_w_per_m2k=1.5,
                                       text_k=273.15 + 8, name="l1r_tank")  # create tank pipe connection
        pp.create_pipe_from_parameters(net, from_junction=j.index('n4r'), to_junction=j.index('n3r'), length_km=0.5,
                                       diameter_m=0.1, k_mm=0.01, sections=1, alpha_w_per_m2k=1.5,
                                       text_k=273.15 + 8, name="l2r")
        pp.create_pipe_from_parameters(net, from_junction=j.index('n5r'), to_junction=j.index('n4r'), length_km=0.01,
                                       diameter_m=0.1, k_mm=0.01, sections=1, alpha_w_per_m2k=1.5,
                                       text_k=273.15 + 8, name="l3r")
        pp.create_pipe_from_parameters(net, from_junction=j.index('n6r'), to_junction=j.index('n4r'), length_km=0.5,
                                       diameter_m=0.1, k_mm=0.01, sections=5, alpha_w_per_m2k=1.5,
                                       text_k=273.15 + 8, name="l4r")
        pp.create_pipe_from_parameters(net, from_junction=j.index('n7r'), to_junction=j.index('n6r'), length_km=0.01,
                                       diameter_m=0.1, k_mm=0.01, sections=1, alpha_w_per_m2k=1.5,
                                       text_k=273.15 + 8, name="l5r")
        pp.create_pipe_from_parameters(net, from_junction=j.index('n8r'), to_junction=j.index('n6r'), length_km=0.01,
                                       diameter_m=0.1, k_mm=0.01, sections=1, alpha_w_per_m2k=1.5,
                                       text_k=273.15 + 8, name="l6r")

        # create grid connector valves
        pp.create_valve(net, j.index('n2s'), j.index('n3s'), diameter_m=0.1, loss_coefficient=1000, opened=True, name="grid_v1")

        self.pipe = net.pipe['name'].tolist()
        self.valve = net.valve['name'].tolist()
        self._add_to_component_list(self.net.pipe)
        self._add_to_component_list(self.net.valve)

    def _create_controllers(self, net):
        v = self.net.valve['name'].to_list()

        # create supply flow control
        CtrlValve(net=net, valve_id=v.index('tank_v1'), gain=-3000,
                  # data_source=data_source, profile_name='tank',
                  level=0, order=1, tol=0.25, name='tank_ctrl')

        CtrlValve(net=net, valve_id=v.index('grid_v1'), gain=-3000,
                  # data_source=data_source, profile_name='tank',
                  level=0, order=2, tol=0.25, name='grid_ctrl')

        # create load flow control
        CtrlValve(net=net, valve_id=v.index('bypass'), gain=-2000,
                  # data_source=data_source, profile_name='bypass',
                  level=1, order=1, tol=0.25, name='bypass_ctrl')
        CtrlValve(net=net, valve_id=v.index('sub_v1'), gain=-100,
                  # data_source=data_source, profile_name='hex1',
                  level=1, order=2, tol=0.1, name='hex1_ctrl')
        CtrlValve(net=net, valve_id=v.index('sub_v2'), gain=-100,
                  # data_source=data_source, profile_name='hex2',
                  level=1, order=3, tol=0.1, name='hex2_ctrl')

        self.controller = ['tank_ctrl1', 'grid_ctrl', 'bypass_ctrl', 'hex1_ctrl', 'hex2_ctrl']

    def _create_substations(self):
        net = self.net
        j = self.net.junction['name'].to_list()
        q_hex1 = 500 * 1000
        q_hex2 = 500 * 1000

        # create control valves
        #pp.create_valve(net, j.index('n5sv'), j.index('n5s'), diameter_m=0.1, opened=True, loss_coefficient=1000, name="sub_v1")
        #pp.create_valve(net, j.index('n7sv'), j.index('n7s'), diameter_m=0.1, opened=True, loss_coefficient=1000, name="sub_v2")

        # create heat exchanger
        pp.create_heat_exchanger(net, from_junction=j.index('n5s'), to_junction=j.index('n5r'), diameter_m=0.1,
                                 qext_w=q_hex1, name="hex1")
        pp.create_heat_exchanger(net, from_junction=j.index('n7s'), to_junction=j.index('n7r'), diameter_m=0.1,
                                 qext_w=q_hex2, name="hex2")

        self.heat_exchanger = net.heat_exchanger['name'].tolist()
        self.valve = net.valve['name'].tolist()


    def _create_heatpump(self):
        net = self.net
        j = self.junction
        mdot_tank_init = self.mdot_tank_out
        t_supply_tank_k = self.T_tank_forward + 273.15
        p_bar_set = self.P_hp_bar
        q_hp_evap = self.Qdot_evap * 1000

        # create hp evaporator
        pp.create_heat_exchanger(net, from_junction=j.index('n3r'), to_junction=j.index('n2r'), diameter_m=0.1,
                                 qext_w=q_hp_evap, name="hp_evap")

        # create tank supply
        pp.create_ext_grid(net, junction=j.index('n3s_tank'), p_bar=p_bar_set, t_k=t_supply_tank_k, name="supply_tank", type="pt")

        # create tank mass flow sink
        pp.create_sink(net, junction=j.index('n3r_tank'), mdot_kg_per_s=mdot_tank_init, name="sink_tank")

        # create valves
        pp.create_valve(net, j.index('n3s_tank'), j.index('n3sv'), diameter_m=0.1, opened=True, loss_coefficient=1000, name="tank_v1")

        self.heat_exchanger = net.heat_exchanger['name'].tolist()
        self.valve = net.valve['name'].tolist()
        self.sink = net.sink['name'].tolist()
        self.source = net.ext_grid['name'].tolist()

    def _create_bypass(self):
        net = self.net
        j = self.junction

        # create bypass valve
        pp.create_valve(net, j.index('n8s'), j.index('n8r'), diameter_m=0.1, opened=True, loss_coefficient=1000, name="bypass")

        self.valve = net.valve['name'].tolist()


    def _plot(self):
        # plot network
        plot.simple_plot(self.net, plot_sinks=True, plot_sources=True, sink_size=4.0, source_size=4.0)

    def load_data(self):
        file = ''
        profiles_source = pd.read_csv(file, index_col=0)
        data_source = DFData(profiles_source)
        return data_source
