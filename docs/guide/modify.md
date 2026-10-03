# Changing the rocket and launch

You change a simulation by calling the setters of its Java objects, and then run it again.
All snippets go inside the `with orhelper.OpenRocketInstance() as instance:` block, with
`helper = orhelper.Helper(instance)`, a loaded `document` and `simulation`.

## Launch conditions

The conditions live in the simulation's options:

```python
import math

options = simulation.getOptions()
options.setLaunchRodAngle(math.radians(5))        # radians from vertical
options.setLaunchRodDirection(math.radians(90))   # radians
options.setWindSpeedAverage(4.0)                  # m/s
options.setWindDirection(math.radians(90))        # radians
options.setWindTurbulenceIntensity(0.1)           # 0 is no turbulence
options.setLaunchLatitude(45.0)                   # degrees
options.setLaunchLongitude(10.0)                  # degrees
```

Remember: **angles are in radians**, except latitude and longitude, whose setters take degrees. Use
`dir(options)` to see everything else you can set, or read the OpenRocket source (see
[How orhelper works](concepts.md)).

The options stay as you set them. The next [`run_simulation`][orhelper.Helper.run_simulation] uses them, so a
loop that changes one option and runs the simulation is a parameter sweep.

## Components of the rocket

[`get_component_named`][orhelper.Helper.get_component_named] finds a part of the rocket by its name, and
then you use its Java getters and setters, for example to override its mass (in kg):

```python
rocket = document.getRocket()
nose = helper.get_component_named(rocket, "Nose cone")
nose.setOverrideMass(nose.getMass() + 0.020)   # 20 g heavier
nose.setMassOverridden(True)
```

To go through every component, use [`JIterator`][orhelper.JIterator]:

```python
for component in orhelper.JIterator(rocket):
    print(component.getName())
```

## Save your changes

The changes are made to the document in memory. To keep them, save it:

```python
helper.save_doc("modified.ork", document)
```

## A complete example

This script runs the sample rocket, makes the nose cone heavier, changes the launch conditions, and saves
the result. After each change it prints the apogee:

```python title="examples/edit_and_save.py"
--8<-- "examples/edit_and_save.py"
```

## Parameter sweeps

To explore a range of conditions, change an option in a loop and collect the results. This example sweeps
the wind speed and the launch angle, and writes the results to a CSV file you can open in a spreadsheet or
with `pandas.read_csv`:

```python title="examples/parameter_sweep.py"
--8<-- "examples/parameter_sweep.py"
```
