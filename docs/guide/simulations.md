# Running simulations

All snippets on this page go inside the `with orhelper.OpenRocketInstance() as instance:` block, with
`helper = orhelper.Helper(instance)`; see [How orhelper works](concepts.md).

## Load a document and pick a simulation

```python
document = helper.load_doc("my_rocket.ork")   # a str or a pathlib.Path
rocket = document.getRocket()
simulation = document.getSimulation(0)        # the first simulation in the file
```

A `.ork` file can hold several simulations: `document.getSimulationCount()` tells you how many, and
`document.getSimulation(n)` returns the `n`-th. For a missing or unreadable file, OpenRocket raises its Java
`RocketLoadException`.

## Run it

```python
helper.run_simulation(simulation)
```

The simulation uses the options it has at that moment (see
[Changing the rocket and launch](modify.md)). The results stay in the simulation object. Running it again
replaces them.

## Read the results as arrays

[`get_timeseries`][orhelper.Helper.get_timeseries] returns a NumPy array for each variable you ask for,
with one value for every time step:

```python
from orhelper import FlightDataType

data = helper.get_timeseries(simulation, [FlightDataType.TYPE_TIME,
                                          FlightDataType.TYPE_ALTITUDE,
                                          FlightDataType.TYPE_VELOCITY_TOTAL])
time = data[FlightDataType.TYPE_TIME]
altitude = data[FlightDataType.TYPE_ALTITUDE]
```

Choose variables from [`FlightDataType`][orhelper.FlightDataType]; the
[reference](../reference/flight-data.md) lists all of them, with their unit. You can also pass the name as
a string (`"TYPE_ALTITUDE"`). Asking for a variable that your OpenRocket version doesn't have raises an
`AttributeError`.

!!! tip "Statistics: `nan`"
    Some series contain `nan`, for example velocities at the first time step. Use `np.nanmax(...)` and
    `np.nanmin(...)`, because `max()` of an array with a `nan` is `nan`.

[`get_final_values`][orhelper.Helper.get_final_values] gives you just the last value of each variable,
for example where the rocket landed:

```python
landing = helper.get_final_values(simulation, [FlightDataType.TYPE_POSITION_X,
                                               FlightDataType.TYPE_POSITION_Y])
```

## Events

[`get_events`][orhelper.Helper.get_events] tells you when things happened. It returns a dictionary from
[`FlightEvent`][orhelper.FlightEvent] to the list of times, in seconds, at which the event occurred:

```python
from orhelper import FlightEvent

events = helper.get_events(simulation)
apogee_time = events[FlightEvent.APOGEE][0]
```

## OpenRocket's own statistics

The simulation holds the summary numbers that OpenRocket shows in its user interface. They are Java
methods of `simulation.getSimulatedData()`:

```python
flight = simulation.getSimulatedData()
flight.getMaxAltitude()          # m
flight.getMaxVelocity()          # m/s
flight.getMaxAcceleration()      # m/s²
flight.getTimeToApogee()         # s
flight.getFlightTime()           # s
flight.getLaunchRodVelocity()    # m/s
flight.getGroundHitVelocity()    # m/s
```

## A complete example

This script prints a table of events with the altitude at each, plus these statistics and the landing
distance:

```python title="examples/events_and_stats.py"
--8<-- "examples/events_and_stats.py"
```

## Multistage rockets

A multistage flight has one *branch* per separated part: branch 0 is the sustainer and the others are
boosters. [`get_timeseries`][orhelper.Helper.get_timeseries],
[`get_final_values`][orhelper.Helper.get_final_values] and
[`get_events`][orhelper.Helper.get_events] all take a `branch_number`:

```python
flight = simulation.getSimulatedData()
for branch_number in range(flight.getBranchCount()):
    data = helper.get_timeseries(simulation, [FlightDataType.TYPE_ALTITUDE], branch_number)
    events = helper.get_events(simulation, branch_number)
```

The full example below uses a two-stage rocket from the examples that come with OpenRocket:

```python title="examples/multistage.py"
--8<-- "examples/multistage.py"
```
