# Pandapower electrical network model

## Installation

Required Python packages:

 * *matplotlib*: 3.3.4
 * *networkx*: 2.5
 * *numpy*: 1.19.5
 * *pandapower*: 2.5.0
 * *pandas*: 1.1.5

To install all required Python packages, run the following command:
```
> python -m pip install -r requirements.txt
```

## Running a simulation

To create the network model (``power_grid_model.json``), run the following command:
```
> python create_network.py
```

Then, to run a quasi-dynamic simulation, run the following command:
```
> python quasidyn_calc.py
```
