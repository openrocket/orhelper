# Installation

You need three things: Python, OpenRocket, and orhelper.

## 1. Python

orhelper needs **Python 3.9 or newer**.

## 2. OpenRocket

Install OpenRocket (version **22.02 or newer**) from
[openrocket.info/downloads](https://openrocket.info/downloads.html). orhelper runs OpenRocket's own code, so
it needs the program, not only your `.ork` files.

The OpenRocket installers include the Java runtime that orhelper uses. If you use a bare OpenRocket
`.jar` file instead, you need a Java runtime yourself: **Java 17** for OpenRocket 23.09 and newer; 22.02
also runs on Java 11.

orhelper looks for OpenRocket in the default location of your system:

| System | Default location |
|---|---|
| macOS | `/Applications/OpenRocket.app` |
| Linux | `~/OpenRocket` |
| Windows | `%PROGRAMFILES%\OpenRocket` |

If yours is somewhere else, tell orhelper where it is:

```python
orhelper.OpenRocketInstance(jar="/path/to/OpenRocket.jar")        # a jar file
orhelper.OpenRocketInstance(orhome="/path/to/OpenRocket")         # an installation folder
```

See [Errors, logging and JVM options](guide/errors-logging.md) for the full list of options.

## 3. orhelper

```bash
pip install orhelper
```

Some of the [examples](examples.md) also need plotting and optimisation libraries, which are optional:

```bash
pip install "orhelper[examples]"    # matplotlib and scipy
pip install "orhelper[pandas]"      # pandas, if you want DataFrames
```

## Check that it works

Save this as `check.py` and run it:

```python
import orhelper

with orhelper.OpenRocketInstance(log_level="ERROR") as instance:
    print("OpenRocket started")
```

If it prints `OpenRocket started`, you're ready for the [quickstart](quickstart.md). If it complains that it
cannot find OpenRocket or Java, see [Troubleshooting](troubleshooting.md).
