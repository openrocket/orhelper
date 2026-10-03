# Notebooks and parallel runs

Both come from the same limit: **a JVM can be started only once per Python process.** See
[How orhelper works](concepts.md).

## Jupyter notebooks

A notebook cell is not a good place for a `with` block: when you run the cell again, the JVM can't be
started again and you get [`JVMAlreadyStartedError`][orhelper.JVMAlreadyStartedError]. Instead, start
OpenRocket once and keep it for the whole session. The JVM stops when the kernel does.

```python
import orhelper

if "instance" not in globals():          # makes this cell safe to run twice
    instance = orhelper.OpenRocketInstance(log_level="ERROR")
    instance.__enter__()

helper = orhelper.Helper(instance)
```

From then on, use `helper` in any cell. If you do get `JVMAlreadyStartedError`, restart the kernel.

The [guided notebook](https://github.com/openrocket/orhelper/blob/master/examples/tour.ipynb) in the
repository walks through the whole workflow this way, with plots.

## Parallel runs

Threads don't help, because there is a single JVM. Use **processes**, and let each one start its own JVM,
run a batch of simulations, and return plain Python results. A worker process can't be reused for a
second `OpenRocketInstance`, so give every worker one task: `multiprocessing.Pool(maxtasksperchild=1)`
does that. Start the workers with the `spawn` method so each gets a clean interpreter:

```python title="examples/parallel_runs.py"
--8<-- "examples/parallel_runs.py"
```

Notes:

- Return numbers, strings and NumPy arrays from the workers. Java objects can't be sent between
  processes.
- Each process loads OpenRocket and its motor database, which takes a second or two, so give each worker a
  batch of simulations, not just one.
- The `if __name__ == "__main__":` guard is required: the spawned workers import your script.
- The same approach lets you test several OpenRocket versions: give each process a different
  `jar=` argument.
