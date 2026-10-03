# Examples

The [`examples/`](https://github.com/openrocket/orhelper/tree/master/examples) folder of the repository has
runnable scripts. Each starts with a docstring that says what it shows. They all use the sample rocket
that comes with orhelper, so they run as they are. A script that needs extra packages says so
in the table below; `pip install "orhelper[examples]"` installs matplotlib and scipy.

All of them are run against real OpenRocket versions by the project's tests, so they keep working.

| Example | What it shows | Extra packages |
|---|---|---|
| [`tour.ipynb`](https://github.com/openrocket/orhelper/blob/master/examples/tour.ipynb) | A guided notebook: run, plot, change launch conditions and components, pandas, listeners | jupyter, matplotlib |
| [`quickstart.py`](https://github.com/openrocket/orhelper/blob/master/examples/quickstart.py) | Run a simulation, print apogee, max velocity and events. [Walkthrough](quickstart.md) | none |
| [`events_and_stats.py`](https://github.com/openrocket/orhelper/blob/master/examples/events_and_stats.py) | An event table with altitudes, OpenRocket's summary statistics, the landing distance. [Guide](guide/simulations.md) | none |
| [`edit_and_save.py`](https://github.com/openrocket/orhelper/blob/master/examples/edit_and_save.py) | Change a component and the launch conditions, compare, save a new `.ork`. [Guide](guide/modify.md) | none |
| [`parameter_sweep.py`](https://github.com/openrocket/orhelper/blob/master/examples/parameter_sweep.py) | Sweep the wind speed and the launch angle and write a CSV file | none |
| [`multistage.py`](https://github.com/openrocket/orhelper/blob/master/examples/multistage.py) | Read the data and events of each branch of a multistage rocket | none |
| [`custom_listener.py`](https://github.com/openrocket/orhelper/blob/master/examples/custom_listener.py) | Run Python code at every simulation step. [Guide](guide/listeners.md) | none |
| [`parallel_runs.py`](https://github.com/openrocket/orhelper/blob/master/examples/parallel_runs.py) | Run simulations in parallel, one JVM per worker process. [Guide](guide/notebooks-parallel.md) | none |
| [`custom_setup.py`](https://github.com/openrocket/orhelper/blob/master/examples/custom_setup.py) | Explicit `jar`, `jvm_args` and log settings; handling startup errors. [Guide](guide/errors-logging.md) | none |
| [`simple_plot.py`](https://github.com/openrocket/orhelper/blob/master/examples/simple_plot.py) | Plot altitude and velocity with annotated events | matplotlib |
| [`lazy.py`](https://github.com/openrocket/orhelper/blob/master/examples/lazy.py) | Find the launch angle that minimises drift with `scipy.optimize` | matplotlib, scipy |
| [`monte_carlo.py`](https://github.com/openrocket/orhelper/blob/master/examples/monte_carlo.py) | Randomise launch angle, wind and masses; custom listeners; landing-zone statistics | none |

## A plot

`simple_plot.py` plots the altitude and the vertical velocity of a flight and marks the events:

![Altitude and vertical velocity of a simulated flight, with burnout and apogee annotated](img/simple_plot.png){ width="520" }

```python title="examples/simple_plot.py"
--8<-- "examples/simple_plot.py"
```

## More

More background, from the community, is on the
[OpenRocket wiki](https://github.com/openrocket/openrocket/wiki/Scripting-with-Python-and-JPype).
