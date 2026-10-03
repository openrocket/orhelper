# orhelper

[![PyPI](https://img.shields.io/pypi/v/orhelper)](https://pypi.org/project/orhelper/)
[![Python](https://img.shields.io/pypi/pyversions/orhelper)](https://pypi.org/project/orhelper/)
[![License: GPL v2](https://img.shields.io/badge/license-GPL%20v2-blue)](https://github.com/openrocket/orhelper/blob/master/LICENSE)
[![Tests](https://github.com/openrocket/orhelper/actions/workflows/tests.yml/badge.svg)](https://github.com/openrocket/orhelper/actions/workflows/tests.yml)

**Script and automate [OpenRocket](https://openrocket.info) from Python.**
Load a `.ork` file, tweak the rocket or launch conditions, run simulations, and
get the results back as NumPy arrays: for parameter sweeps, optimisation, Monte
Carlo landing-zone studies, or your own plots.

<p align="center">
  <img src="https://raw.githubusercontent.com/openrocket/orhelper/master/docs/img/simple_plot.png" alt="Altitude and vertical velocity of a simulated flight, with burnout and apogee annotated" width="520">
  <br>
  <em>Output of <a href="https://github.com/openrocket/orhelper/blob/master/examples/simple_plot.py"><code>examples/simple_plot.py</code></a></em>
</p>

## Quickstart

1. **Install OpenRocket** from [openrocket.info/downloads](https://openrocket.info/downloads.html)
   (22.02 or newer). The installer bundles the Java runtime that orhelper uses.
2. **Install orhelper:**
   ```bash
   pip install orhelper
   ```
3. **Run a simulation** (this uses the sample rocket that ships with orhelper):

   ```python
   import numpy as np

   import orhelper
   from orhelper import FlightDataType

   with orhelper.OpenRocketInstance(log_level="ERROR") as instance:
       orh = orhelper.Helper(instance)

       doc = orh.load_doc(orhelper.sample_ork_path())  # or "/path/to/your.ork"
       sim = doc.getSimulation(0)
       orh.run_simulation(sim)

       data = orh.get_timeseries(sim, [FlightDataType.TYPE_TIME,
                                       FlightDataType.TYPE_ALTITUDE,
                                       FlightDataType.TYPE_VELOCITY_TOTAL])

       print(f"Apogee:       {np.max(data[FlightDataType.TYPE_ALTITUDE]):.0f} m")
       print(f"Max velocity: {np.nanmax(data[FlightDataType.TYPE_VELOCITY_TOTAL]):.0f} m/s")
       print(f"Flight time:  {data[FlightDataType.TYPE_TIME][-1]:.1f} s")
   ```

   ```text
   Apogee:       51 m
   Max velocity: 29 m/s
   Flight time:  15.9 s
   ```

   (Exact numbers vary slightly from run to run, because `run_simulation`
   randomizes the simulation's random seed.)

   The complete script is [`examples/quickstart.py`](https://github.com/openrocket/orhelper/blob/master/examples/quickstart.py).
   If OpenRocket isn't in its default location, or it can't be found, pass the
   jar explicitly: `OpenRocketInstance(jar="/path/to/OpenRocket.jar")`.

## How it works

orhelper starts OpenRocket's Java code inside your Python process using
[JPype](https://jpype.readthedocs.io). It adds a small layer of helpers on top,
and everything else is OpenRocket's own Java API.

- **`OpenRocketInstance`** starts (and on exit shuts down) the JVM and
  initialises OpenRocket. Use it as a context manager; everything that touches
  OpenRocket must happen inside the `with` block.
- **`Helper`** has the Python-friendly operations: `load_doc`, `save_doc`,
  `run_simulation`, `get_timeseries`, `get_final_values`, `get_events`,
  `get_component_named`.
- **`FlightDataType`** and **`FlightEvent`** are Python enums for the variables
  and events OpenRocket records. Pass members (or their names as strings) to the
  helpers above.
- **`AbstractSimulationListener`** lets you hook into a simulation from Python
  (see [`examples/monte_carlo.py`](https://github.com/openrocket/orhelper/blob/master/examples/monte_carlo.py)).
- **Everything else is a raw Java object.** `load_doc` returns an
  `OpenRocketDocument`, `doc.getSimulation(0)` a `Simulation`,
  `sim.getOptions()` a `SimulationOptions`, and so on. Call their Java methods
  directly (`getFoo()`, `setFoo(value)`). To find out what's available, browse
  the [OpenRocket source](https://github.com/openrocket/openrocket) (the
  `info.openrocket.core` package; in 22.02 and 23.09 it is `net.sf.openrocket`
  instead) or use `dir(obj)` in a Python session.
  Java methods take SI units, and angles are in **radians**.

## Common tasks

All snippets assume the `with orhelper.OpenRocketInstance() as instance:` block and
`orh = orhelper.Helper(instance)` from the quickstart, and `doc`/`sim` loaded as there.

**Change launch conditions** (angles in radians, speeds in m/s):

```python
opts = sim.getOptions()
opts.setLaunchRodAngle(math.radians(5))
opts.setLaunchRodDirection(math.radians(90))
opts.setWindSpeedAverage(4.0)
```

**Modify a component**, for example override a mass:

```python
body = orh.get_component_named(sim.getRocket(), "Body tube")
body.setMassOverridden(True)
body.setOverrideMass(0.120)  # kg
```

**Get just the final value of a variable:**

```python
orh.get_final_values(sim, [FlightDataType.TYPE_POSITION_X])
```

**Save your changes:** `orh.save_doc("modified.ork", doc)`.

**Multistage rockets:** `get_timeseries`, `get_final_values` and `get_events`
take `branch_number` (0 is the sustainer; 1, 2, ... are booster branches).

**Run Python code during a simulation** by subclassing
`orhelper.AbstractSimulationListener` and passing instances via
`run_simulation(sim, listeners=[...])`. Override only the hooks you need
(`postStep`, `endSimulation`, ...); see `examples/monte_carlo.py`.

## Examples

Examples live in [`examples/`](https://github.com/openrocket/orhelper/tree/master/examples). Start with the notebook
[`tour.ipynb`](https://github.com/openrocket/orhelper/blob/master/examples/tour.ipynb) (needs `pip install jupyter matplotlib`), or run
any script, for example `python examples/quickstart.py`. Some need extra packages:
`pip install matplotlib scipy` (or `pip install "orhelper[examples]"`).

| Example | What it shows | Extra packages |
|---|---|---|
| [`tour.ipynb`](https://github.com/openrocket/orhelper/blob/master/examples/tour.ipynb) | Guided notebook: run, plot, change launch conditions and components, pandas, listeners | jupyter, matplotlib |
| [`quickstart.py`](https://github.com/openrocket/orhelper/blob/master/examples/quickstart.py) | Run a simulation, print apogee, max velocity and events | none |
| [`events_and_stats.py`](https://github.com/openrocket/orhelper/blob/master/examples/events_and_stats.py) | Event table with altitudes, OpenRocket's summary statistics, landing distance | none |
| [`edit_and_save.py`](https://github.com/openrocket/orhelper/blob/master/examples/edit_and_save.py) | Change a component and the launch conditions, compare, save a new `.ork` | none |
| [`parameter_sweep.py`](https://github.com/openrocket/orhelper/blob/master/examples/parameter_sweep.py) | Sweep wind speed and launch angle and write a CSV file | none |
| [`multistage.py`](https://github.com/openrocket/orhelper/blob/master/examples/multistage.py) | Read the data and events of each branch of a multistage rocket | none |
| [`custom_listener.py`](https://github.com/openrocket/orhelper/blob/master/examples/custom_listener.py) | Run Python code at every simulation step with a listener | none |
| [`parallel_runs.py`](https://github.com/openrocket/orhelper/blob/master/examples/parallel_runs.py) | Run simulations in parallel, one JVM per worker process | none |
| [`custom_setup.py`](https://github.com/openrocket/orhelper/blob/master/examples/custom_setup.py) | Explicit `jar`, `jvm_args` and log settings; handling startup errors | none |
| [`simple_plot.py`](https://github.com/openrocket/orhelper/blob/master/examples/simple_plot.py) | Plot altitude and velocity with annotated events | matplotlib |
| [`lazy.py`](https://github.com/openrocket/orhelper/blob/master/examples/lazy.py) | Find the launch angle that minimises drift with `scipy.optimize` | matplotlib, scipy |
| [`monte_carlo.py`](https://github.com/openrocket/orhelper/blob/master/examples/monte_carlo.py) | Randomise launch angle, wind and masses; custom listeners; landing-zone statistics | none |

More background is on the
[OpenRocket wiki](https://github.com/openrocket/openrocket/wiki/Scripting-with-Python-and-JPype).

## Troubleshooting

- **`OpenRocketNotFoundError` / `JVMNotFoundError` when starting.** orhelper couldn't
  find OpenRocket or its Java runtime. The message says what was missing. Pass
  `jar="…/OpenRocket.jar"` (and `jvm="…/libjvm.*"` if no Java runtime is found), or
  `orhome="…"` for an installation in a non-default place. The default install
  locations it looks in are `~/OpenRocket` (Linux),
  `/Applications/OpenRocket.app` (macOS) and `%PROGRAMFILES%\OpenRocket` (Windows).
  Both are subclasses of `orhelper.OrHelperError` (a `RuntimeError`).
- **`JVMAlreadyStartedError`.** JPype starts the JVM once per Python process, so a
  second `OpenRocketInstance` (even after the first one closed) fails.
  Do all OpenRocket work in a single `with` block,
  and use a new process to switch OpenRocket versions (for example with
  `multiprocessing` using the `spawn` start method).
- **Wrong Java version.** OpenRocket 23.09 and newer need Java 17; 22.02 also
  works with Java 11. The OpenRocket installers bundle a suitable runtime.
- **JVM fails to load on Apple Silicon or with a mixed 32/64-bit setup.** The Python
  interpreter and the Java runtime must have the same CPU architecture.
- **A result contains `nan`.** Some series are `nan` at the first time step (for
  example velocities at t=0). Use `np.nanmax`/`np.nanmin`, or drop the first sample.
- **Lots of log output.** Pass `log_level="ERROR"` to silence OpenRocket's Java logging.
  orhelper's own Python messages go through the `orhelper` logger and are only shown
  if you configure logging (for example `logging.basicConfig(level=logging.INFO)`).
- **Need more memory, or a headless JVM?** Pass JVM options with
  `OpenRocketInstance(jvm_args=["-Xmx4g", "-Djava.awt.headless=true"])`.
- **`TypeError: … unexpected keyword argument`.** Only `orhome`, `jar`, `jvm`, `jvm_args`
  and `loglevel` (plus the positional `jar_path` and `log_level`) are accepted; a
  misspelt option is an error rather than being ignored.
- **`AttributeError: … not available in this OpenRocket version`.** You asked for a
  `FlightDataType` introduced after the OpenRocket version you're running.
- **Showing plots.** Leave the `with OpenRocketInstance()` block before calling
  `plt.show()`, so the JVM is shut down first, as `simple_plot.py` does.

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
    document = helper.load_doc(orhelper.sample_ork_path())
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

## Development and testing

```bash
git clone https://github.com/openrocket/orhelper.git
cd orhelper
pip install -e ".[examples]"
```

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
results, saving and reloading, listener cloning, and multistage branches. A second
test module runs every script in `examples/` against the jar, so the examples can't
silently break. CI runs both against the released OpenRocket 22.02, 23.09 and 24.12 jars.
See [CONTRIBUTING.md](https://github.com/openrocket/orhelper/blob/master/CONTRIBUTING.md) for more, and [CHANGELOG.md](https://github.com/openrocket/orhelper/blob/master/CHANGELOG.md)
for release notes.

## License

orhelper is released under the [GNU General Public License v2](https://github.com/openrocket/orhelper/blob/master/LICENSE).

## Credits
- Richard Graham for the original script: [Source](https://sourceforge.net/p/openrocket/mailman/openrocket-devel/thread/4F17AA0C.1040002@rdg.cc/)
- @not7cd for some initial organization and clean-up: [Source](https://github.com/not7cd/orhelper)
- And of course everyone who has contributed to OpenRocket over the years.
