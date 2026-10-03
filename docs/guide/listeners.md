# Listeners

A **listener** is Python code that OpenRocket calls *while it simulates*. With a listener you can
record what happens at every step, change the starting conditions, or override a model such as the wind or
the thrust. This is how the [Monte Carlo example](https://github.com/openrocket/orhelper/blob/master/examples/monte_carlo.py)
drops a rocket from a random altitude.

## The basics

Subclass [`AbstractSimulationListener`][orhelper.AbstractSimulationListener], override the hooks you need,
and pass instances to [`run_simulation`][orhelper.Helper.run_simulation]:

```python title="examples/custom_listener.py"
--8<-- "examples/custom_listener.py"
```

Every hook does nothing unless you override it. Their names are the Java ones (camelCase), and the
arguments are Java objects: `status`, for example, is OpenRocket's `SimulationStatus`, with methods such
as `getSimulationTime()` and `getRocketPosition()`.

## The hooks

| Group | Hooks | What you return |
|---|---|---|
| **Lifecycle** | `startSimulation`, `endSimulation`, `postStep`, and `startSimulationBranch`, `endSimulationBranch` | nothing |
| **Lifecycle** | `preStep` | `True` to take the step (the default), `False` to skip it |
| **Events** | `addFlightEvent`, `handleFlightEvent`, `motorIgnition`, `recoveryDeviceDeployment` | `True` to let it happen (the default), `False` to prevent it |
| **Computation** | `preWindModel`, `preGravityModel`, `preSimpleThrustCalculation`, `preAtmosphericModel`, `preFlightConditions`, `preAerodynamicCalculation`, `preMassCalculation`, `preAccelerationCalculation` | a replacement value, or `None` (`nan` for numbers) to leave it alone |
| **Computation** | the matching `post...` hooks | a replacement for the computed value, or `None` (`nan` for numbers) |

The [API reference][orhelper.AbstractSimulationListener] documents each hook. Two things are worth knowing:

- The branch hooks (`startSimulationBranch` and `endSimulationBranch`) exist only in OpenRocket 26.xx. In
  22.02, 23.09 and 24.12, they are never called.
- `preStep` returning `False` skips that simulation step, which does not advance the simulation, so don't
  return `False` on every call.

## Overriding a model

A computation hook that returns a value replaces what OpenRocket would use. For example, this
listener blows a constant 10 m/s wind along the x axis, whatever the simulation's settings say:

```python
Coordinate = instance.openrocket_core.util.Coordinate

class Gust(orhelper.AbstractSimulationListener):
    def preWindModel(self, status):
        return Coordinate(10.0, 0.0, 0.0)

helper.run_simulation(simulation, listeners=[Gust()])
```

With the wind set to 0 and the turbulence off, the sample rocket lands about 90 to 100 metres from the
pad with this listener, and on the pad without it. A hook that returns a number works the same way: a
`preGravityModel` that returns `3.0` lifts the sample rocket's apogee from about 51 m to about 94 m.

!!! tip "Return `nan`, not `0`, to leave a number alone"
    The numeric hooks (gravity and thrust) use `float("nan")` for "no change". Returning `0.0` would set the
    value to zero.

## Keep your results in a list or dict

!!! warning "Numbers you assign in a hook are lost"
    OpenRocket doesn't run the listener object you pass in: it **clones** it, with a shallow copy. Lists
    and dicts you create in `__init__` are shared with the copy, so you can read them after the run. A
    number or string that a hook *assigns* is changed on the copy only.

```python
class Counter(orhelper.AbstractSimulationListener):
    def __init__(self):
        self.count = 0          # an int
        self.calls = []         # a list

    def preStep(self, status):
        self.count += 1         # changes the copy only
        self.calls.append(1)    # the list is shared
        return True

counter = Counter()
helper.run_simulation(simulation, listeners=[counter])
print(counter.count)        # 0     (the copy was changed, not this object)
print(len(counter.calls))   # about 200 (the number of steps)
```

If you want a counter, keep it in a list or a dict (`self.stats = {"steps": 0}`), or a NumPy array.

## Starting the rocket somewhere else

`startSimulation` can change the state of the simulation. This listener starts the rocket 1000 m above the
pad, like a drop test from a balloon:

```python
class AirStart(orhelper.AbstractSimulationListener):
    def __init__(self, altitude):
        self.start_altitude = altitude

    def startSimulation(self, status):
        position = status.getRocketPosition()
        status.setRocketPosition(position.add(0.0, 0.0, self.start_altitude))
```
