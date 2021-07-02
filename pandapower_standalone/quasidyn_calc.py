import tempfile
import os
import matplotlib.pyplot as mpl
import numpy as np

import pandas as pd
from pandapower.timeseries import DFData
from pandapower.timeseries import OutputWriter
from pandapower.timeseries.run_time_series import run_timeseries
from pandapower.control import ConstControl


def quasidyn(output_dir, net, n_timesteps, data_subfolder, data_filename):

    dirname = os.path.dirname(__file__)
    data_file = os.path.join(dirname, data_subfolder, data_filename)
    profiles, ds = create_data_source(data_file)

    #create controllers (to control P values of the load and the sgen)
    create_controllers(net, ds)

    #time steps to be calculated. Could also be a list with non-consecutive time steps
    time_steps = range(0, n_timesteps)

    #the output writer with the desired results to be stored to files.
    ow = create_output_writer(net, time_steps, output_dir=output_dir)

    #the main time series function
    run_timeseries(net, time_steps, run_controller=True)

def create_data_source(data_file):
    profiles = pd.read_csv(data_file, header=0, decimal=".", sep=",")
    ds = DFData(profiles)

    return profiles, ds


def create_controllers(net, ds):

    for _, element in net.sgen.iterrows():
        ConstControl(net, element='sgen', variable='p_mw', element_index=[element.name],
                     data_source=ds, profile_name=[element['name']])

    for _, element in net.load.iterrows():
        ConstControl(net, element='load', variable='p_mw', element_index=[element.name],
                 data_source=ds, profile_name=[element['name']])


def create_output_writer(net, time_steps, output_dir):
    ow = OutputWriter(net, time_steps, output_path=output_dir, output_file_type=".csv", log_variables=list())
    ow.log_variable('res_load', 'p_mw')
    ow.log_variable('res_sgen', 'p_mw')
    ow.log_variable('res_bus', 'vm_pu')
    ow.log_variable('res_line', 'loading_percent')
    ow.log_variable('res_line', 'i_ka')
    return ow

def plot_quasi_res(dirname, subfolder, filename, net, n_timesteps, stepsize):
    info_file = os.path.join(dirname, subfolder, filename)
    info = pd.read_csv(info_file, header=0, sep=";", decimal=".", index_col=0)
    for i in range(len(info.index)):
        data_dirname = os.path.join(dirname, subfolder)
        data_file = os.path.join(data_dirname, info.iloc[i]['subfolder'], info.iloc[i]['filename'])
        data = pd.read_csv(data_file, header=0, sep=";", decimal=".", index_col=0)
        time = pd.DataFrame({'time': range(0, n_timesteps*stepsize, stepsize)})
        data['time'] = pd.to_datetime(time.time, unit='m').dt.strftime('%H:%M')
        data.set_index('time', inplace=True)
        data.plot(label="data", use_index=True, marker='o', markersize=3, linestyle='dashed', linewidth=1)
        if i == 0:
            mpl.legend(net.bus['name'])
        elif i == 1:
            mpl.legend(net.line['name'])
        elif i == 2:
            mpl.legend(net.load['name'])
        elif i == 3:
            mpl.legend(net.sgen['name'])

        mpl.xlabel(info.iloc[i]['xlabel'])
        mpl.ylabel(info.iloc[i]['ylabel'])
        mpl.title(info.iloc[i]['title'])
        mpl.grid()
        #mpl.show()
        mpl.savefig(info.iloc[i]['component']+'.png')


if __name__ == '__main__':

    import pandapower as pp
    net = pp.from_json('power_grid_model.json')

    # import plot_network
    # plot_network.plot_overview(net)

    #create heat pump controller
    import DiscreteHPControl
    hp_controller = DiscreteHPControl.DiscreteHPControl(
        net=net, hid=1, delta_vm_pu=0.1, deadband=0.01,
        delta_vm_lower_pu=-0.1, delta_vm_upper_pu=0.1
        )

    dirname = os.path.dirname(__file__)
    output_dir_quasi = os.path.join(dirname, "QuasiDynamic_Results")

    print("Results can be found in your local temp folder: {}".format(output_dir_quasi))
    if not os.path.exists(output_dir_quasi):
        os.mkdir(output_dir_quasi)

    quasidyn(
        output_dir_quasi, net, n_timesteps=96, data_subfolder="netw_params",
        data_filename="load_gen_profiles_15p.csv"
        )

    plot_quasi_res(
        dirname, "QuasiDynamic_Results", 'plot_info.csv', net, n_timesteps=96, stepsize=15
        )
