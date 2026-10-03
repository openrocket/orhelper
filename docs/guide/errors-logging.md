# Errors, logging and JVM options

## Exceptions

When orhelper can't start OpenRocket, it raises an exception. They all derive from
[`OrHelperError`][orhelper.OrHelperError], which is a `RuntimeError`, so you can catch them together:

| Exception | Meaning | What to do |
|---|---|---|
| [`OpenRocketNotFoundError`][orhelper.OpenRocketNotFoundError] | The installation or the jar was not found | Pass `jar=` or `orhome=` |
| [`JVMNotFoundError`][orhelper.JVMNotFoundError] | No Java was found | Install Java, set `JAVA_HOME`, or pass `jvm=` |
| [`JVMAlreadyStartedError`][orhelper.JVMAlreadyStartedError] | A second JVM in the same process | Use one `with` block, or separate processes |

A misspelt keyword argument (`jvm_path=`, for example) raises `TypeError`, and an unknown log level raises
`ValueError`.

Problems *inside* OpenRocket surface as the Java exception, raised by JPype, for example
`RocketLoadException` for a file that can't be loaded. Asking for a
[flight data variable](../reference/flight-data.md) that your OpenRocket version doesn't have raises an
`AttributeError`, and a component that doesn't exist in
[`get_component_named`][orhelper.Helper.get_component_named] raises a `ValueError`.

## Choosing which OpenRocket and Java

By default orhelper finds the installed OpenRocket. You can choose another with these keyword arguments
of [`OpenRocketInstance`][orhelper.OpenRocketInstance]:

| Argument | Meaning |
|---|---|
| `jar` | An OpenRocket jar file. It takes precedence over the installed one. |
| `orhome` | An OpenRocket installation folder, if it is not in the default location. |
| `jvm` | The Java library to use (`libjvm.so`, `libjvm.dylib` or `jvm.dll`). |
| `jvm_args` | A list of extra options for the JVM, for example `["-Xmx4g", "-Djava.awt.headless=true"]`. |

## Logging

`log_level` sets how much OpenRocket tells you. It takes `"OFF"`, `"ERROR"`, `"WARN"`, `"INFO"` (the
default), `"DEBUG"`, `"TRACE"` or `"ALL"`, in any case. At the default level OpenRocket prints a lot of
information while it loads files and simulates, so `log_level="ERROR"` is a good choice for scripts.

orhelper's own messages (which jar it found, for example) go through Python's `logging` module, in the
`orhelper` logger. orhelper doesn't configure logging for you; to see the messages:

```python
import logging
logging.basicConfig(level=logging.INFO)
```

## All of it together

```python title="examples/custom_setup.py"
--8<-- "examples/custom_setup.py"
```
