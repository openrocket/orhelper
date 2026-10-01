# orhelper
orhelper is a module which aims to facilitate interacting and scripting with OpenRocket from Python.

## Prerequisites
- OpenRocket version 22.02 or above.  Ideally it will be installed in
  its default location, but running from non-default locations or from
  the .jar file are also supported.

- A compatible Java runtime: Java 17 for OpenRocket 23.09 and newer;
  OpenRocket 22.02 also works with Java 11. Installed OpenRocket bundles
  include their own runtime.
  
- Python >= 3.6

- jpype1 >= 0.6.3

- numpy

The examples may have additional prerequites, for instance lazy.py
requires scipy and matplotlib

## Installing

- Install orhelper from pip
    ```bash
    pip install orhelper
    ```

- See `examples/` for usage examples

- See [the OpenRocket wiki](https://github.com/openrocket/openrocket/wiki/Scripting-with-Python-and-JPype) for more info on usage and the examples 

## OpenRocket compatibility

The helpers and Python simulation listeners support OpenRocket 22.02, 23.09,
24.12, and the 26.xx development code. orhelper detects the Java package layout
used by the loaded version. Startup loads the local motor and component
databases; interactive motor-database updates belong in the OpenRocket application.

The compatibility tests passed on macOS with Python 3.10, JPype 1.5, and Java 17
for all four versions, and with Java 11 for 22.02. The 26.xx run used snapshot
`1f317c066`; the relevant APIs were also compared with upstream `259ba462a`.

To select a specific version, pass its JAR explicitly:

```python
import orhelper

with orhelper.OpenRocketInstance(jar="/path/to/OpenRocket.jar") as instance:
    helper = orhelper.Helper(instance)
    document = helper.load_doc("examples/simple.ork")
    simulation = document.getSimulation(0)
    helper.run_simulation(simulation)
    data = helper.get_timeseries(simulation, [orhelper.FlightDataType.TYPE_ALTITUDE])
```

Both `jar=...` and the legacy positional JAR argument take precedence over
the automatically discovered installation. `jvm=...` selects a different JVM
when needed. JPype can start the JVM only once per Python process; use a new
process to switch OpenRocket versions or start another instance after shutdown.

`FlightDataType` includes the variables introduced in 24.12 and 26.xx.
Requesting a variable unavailable in an older OpenRocket version raises
`AttributeError`. Both enum members and their names as strings are accepted.
`TYPE_PROPELLANT_MASS` remains supported as a legacy name for `TYPE_MOTOR_MASS`,
which measures total motor mass, including the casing. Existing enum numeric
values are preserved.

`get_events()` handles simulation warnings (`SIM_WARN`) and aborts (`SIM_ABORT`).
For multistage rockets, `get_events(simulation, branch_number=1)` selects a booster
branch, matching the branch selection in `get_timeseries()` and `get_final_values()`.

## Testing

Run the Python regression tests with:

```bash
python -m unittest discover -s tests -v
```

The Java integration tests are skipped unless `OPENROCKET_JAR` is set. They require
a JDK with `javac` on `PATH`, run without a display, and isolate Java preferences
and the motor database from your normal OpenRocket settings. Run each version in
a separate Python process:

```bash
OPENROCKET_JAR=/path/to/OpenRocket.jar python -m unittest discover -s tests -v
```

These tests check every built-in flight-data type and event, actual simulation
results, saving and reloading, listener cloning, and multistage branches.

## Credits
- Richard Graham for the original script: [Source](https://sourceforge.net/p/openrocket/mailman/openrocket-devel/thread/4F17AA0C.1040002@rdg.cc/)
- @not7cd for some initial organization and clean-up: [Source](https://github.com/not7cd/orhelper)
- And of course everyone who has contributed to OpenRocket over the years.
