# Troubleshooting

## OpenRocket or Java is not found

**`OpenRocketNotFoundError`** means orhelper couldn't find OpenRocket, **`JVMNotFoundError`** that it
couldn't find Java. The message says what is missing. Tell orhelper where OpenRocket is:

```python
orhelper.OpenRocketInstance(jar="/path/to/OpenRocket.jar")
orhelper.OpenRocketInstance(orhome="/path/to/OpenRocket")            # an installation folder
orhelper.OpenRocketInstance(jar="...", jvm="/path/to/libjvm.so")     # and a Java runtime
```

By default orhelper looks in `/Applications/OpenRocket.app` (macOS), `~/OpenRocket` (Linux) and
`%PROGRAMFILES%\OpenRocket` (Windows), and uses the Java runtime inside that installation. Without an
installation, it uses the jar in the `CLASSPATH` environment variable or `./OpenRocket.jar`, and the Java
that JPype finds (set `JAVA_HOME` to choose it). See [Installation](installation.md).

## `JVMAlreadyStartedError`

A JVM can be started only once per Python process, even after it was shut down. Put all your OpenRocket
code in one `with orhelper.OpenRocketInstance() as instance:` block and copy the results out of it. In a
notebook, see [Notebooks and parallel runs](guide/notebooks-parallel.md); restarting the kernel always
helps. To run several simulations at once, or several OpenRocket versions, use separate processes.

## The wrong Java version, or Java doesn't load

OpenRocket 23.09 and newer need **Java 17**; 22.02 also runs on Java 11. The OpenRocket installers include a
suitable runtime. If the JVM fails to load on an Apple Silicon Mac or another system with several
architectures, Python and Java must have the same one (both `arm64`, or both `x86_64`).

## A result is `nan`

Some series are `nan` at some time steps, for example velocities at the first one. Use `np.nanmax` and
`np.nanmin`, or drop the first sample. `get_final_values` gives the last sample, which can also be `nan` for
variables that some OpenRocket versions don't record on the last data point.

## Latitude and longitude look wrong

They are in radians in OpenRocket 22.02 and 23.09, and in degrees in 24.12 and later. See
[OpenRocket versions](reference/versions.md).

## `AttributeError: Flight data type '...' is not available in this OpenRocket version`

You asked for a variable that was introduced after the version you run. The
[flight data reference](reference/flight-data.md) shows which versions have each variable.

## Too much output

OpenRocket logs a lot at the default level. Pass `log_level="ERROR"`:

```python
orhelper.OpenRocketInstance(log_level="ERROR")
```

To see orhelper's own messages, configure Python logging:
`logging.basicConfig(level=logging.INFO)`. See [Errors, logging and JVM options](guide/errors-logging.md).

## `TypeError: ... unexpected keyword argument`

[`OpenRocketInstance`][orhelper.OpenRocketInstance] accepts only `orhelper`'s documented options: `jar`,
`orhome`, `jvm`, `jvm_args` and `loglevel`, plus the positional `jar_path` and `log_level`. A misspelt option
is an error, not ignored.

## My changes to a listener's variables disappear

OpenRocket runs a copy of your listener. Keep results in a list or a dict, not in a number. See
[Listeners](guide/listeners.md#keep-your-results-in-a-list-or-dict).

## Showing matplotlib plots

If you use matplotlib, leave the `with orhelper.OpenRocketInstance()` block before calling `plt.show()`, so the
JVM is shut down first. This is what [`simple_plot.py`](https://github.com/openrocket/orhelper/blob/master/examples/simple_plot.py) does.

## Still stuck?

Open an [issue](https://github.com/openrocket/orhelper/issues) and include your operating system, Python
and OpenRocket versions, and the full error message.
