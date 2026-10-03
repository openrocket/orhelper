# How orhelper works

A few ideas explain nearly everything about orhelper. Read this page once and the rest will make sense.

## OpenRocket runs inside your Python process

OpenRocket is a Java program. orhelper uses [JPype](https://jpype.readthedocs.io) to start a Java virtual
machine (JVM) inside your Python process and to load OpenRocket's classes into it. Nothing is
translated or re-implemented: when you run a simulation, it is OpenRocket's own simulation engine that
runs.

That has three consequences.

### 1. Start OpenRocket once, in a `with` block

[`OpenRocketInstance`][orhelper.OpenRocketInstance] starts the JVM when you enter the `with` block and shuts
it down when you leave it. Everything that uses OpenRocket goes inside:

```python
with orhelper.OpenRocketInstance() as instance:
    helper = orhelper.Helper(instance)
    ...   # load, simulate, read results
```

**A JVM can be started only once per Python process**, even after it was shut down. A second `with`
block raises [`JVMAlreadyStartedError`][orhelper.JVMAlreadyStartedError]. Do all the OpenRocket work in one
block, and copy the results you need (NumPy arrays and numbers) out of it. To run several OpenRocket
versions, or to run in parallel, use several processes: see
[Notebooks and parallel runs](notebooks-parallel.md).

### 2. Most objects are Java objects

[`Helper`][orhelper.Helper] has the Python-friendly operations: loading and saving files, running
simulations, and reading results as NumPy arrays. Everything else you get back is a Java object:

```python
document = helper.load_doc("my_rocket.ork")   # Java: OpenRocketDocument
rocket = document.getRocket()                 # Java: Rocket
simulation = document.getSimulation(0)        # Java: Simulation
options = simulation.getOptions()             # Java: SimulationOptions
options.setWindSpeedAverage(5.0)              # a Java method call
```

You call their Java methods (`getFoo()`, `setFoo(value)`) directly. Python numbers, strings and booleans are
converted automatically, and Java numbers come back as Python numbers.

### 3. Units are SI, and angles are in radians

OpenRocket works in SI units internally, and so do the Java methods and the arrays that orhelper returns:
metres, kilograms, seconds, newtons, and **radians** for angles (so a 45 degree launch rod angle is
`math.radians(45)`). OpenRocket's user interface shows nicer units such as grams, but those don't reach
your script. The [flight data reference](../reference/flight-data.md) lists the unit of every variable.

!!! warning "A few exceptions"
    A few values do depend on the OpenRocket version. Latitude and longitude in the results are in radians
    in OpenRocket 22.02 and 23.09, and in degrees in 24.12 and later. See
    [OpenRocket versions](../reference/versions.md).

## Finding out what a Java object can do

You can use `dir()` in a Python session to list the methods of a Java object:

```python
print([name for name in dir(options) if name.startswith("set")])
```

OpenRocket's own source code is the full documentation: browse the
[`info.openrocket.core`](https://github.com/openrocket/openrocket/tree/master/core/src/main/java/info/openrocket/core)
package on GitHub. In OpenRocket 22.02 and 23.09 the same classes are in the package `net.sf.openrocket`.

To write code that works with all versions, reach the classes through the instance rather than by their
package name:

```python
Coordinate = instance.openrocket_core.util.Coordinate   # info.openrocket.core, or net.sf.openrocket
```

## The pieces

| You use | For |
|---|---|
| [`OpenRocketInstance`][orhelper.OpenRocketInstance] | starting and stopping OpenRocket, choosing which one |
| [`Helper`][orhelper.Helper] | loading and saving files, running simulations, reading results |
| [`FlightDataType`][orhelper.FlightDataType] | naming the variables you want from a simulation |
| [`FlightEvent`][orhelper.FlightEvent] | the events (burnout, apogee, ...) a flight consists of |
| [`AbstractSimulationListener`][orhelper.AbstractSimulationListener] | running your own Python code during a simulation |
| the Java objects | everything else: rocket components, simulation settings, ... |
