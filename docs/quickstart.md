# Quickstart

This runs a simulation of the sample rocket that comes with orhelper and prints some results. It needs
only orhelper and OpenRocket (see [Installation](installation.md)).

```python title="examples/quickstart.py"
--8<-- "examples/quickstart.py"
```

Run it, and you get something like this (the numbers vary slightly from run to run):

```text
Rocket:       A simple model rocket
Apogee:       51 m
Max velocity: 29 m/s
Flight time:  16.0 s
  LAUNCH                       t = 0.0 s
  IGNITION                     t = 0.0 s
  LIFTOFF                      t = 0.1 s
  LAUNCHROD                    t = 0.2 s
  BURNOUT                      t = 0.7 s
  APOGEE                       t = 3.5 s
  EJECTION_CHARGE              t = 3.7 s
  RECOVERY_DEVICE_DEPLOYMENT   t = 3.7 s
  GROUND_HIT                   t = 16.0 s
  SIMULATION_END               t = 16.0 s
```

## What the script does

1. **`with orhelper.OpenRocketInstance(...) as instance:`** starts OpenRocket. Everything that uses
   OpenRocket goes inside this block. `log_level="ERROR"` hides OpenRocket's own, very chatty, logging.
2. **`orh.load_doc(...)`** loads a `.ork` file. Use `orhelper.sample_ork_path()` for the sample, or the path
   of your own file. You get a Java `OpenRocketDocument`.
3. **`doc.getSimulation(0)`** is the first simulation stored in the document. This is a Java call, as are
   `getRocket()` and `getName()`: see [How orhelper works](guide/concepts.md).
4. **`orh.run_simulation(sim)`** runs the simulation.
5. **`orh.get_timeseries(...)`** returns the values of the variables you ask for as NumPy arrays, one value
   per time step. **`orh.get_events(sim)`** returns when things like burnout and apogee happened.

!!! tip "`np.nanmax`, not `max`"
    Some series start with `nan`, for example velocity at the first time step, so `max()` would return
    `nan`. Use `numpy.nanmax` and `numpy.nanmin` for statistics.

## Next

- [Running simulations](guide/simulations.md): everything you can read from the results.
- [Changing the rocket and launch](guide/modify.md): wind, launch angle, component masses.
- [Examples](examples.md): scripts for parameter sweeps, multistage rockets, Monte Carlo studies and more.
