# Contributing to orhelper

Thanks for helping! Bug reports, examples and documentation fixes are as
welcome as code.

## Setup

```bash
git clone https://github.com/openrocket/orhelper.git
cd orhelper
python -m venv venv && source venv/bin/activate
pip install -e ".[examples]"
```

You also need OpenRocket (22.02 or newer) to run anything that simulates.

## Tests

```bash
python -m unittest discover -s tests -v
```

This runs the unit tests (no Java needed). The Java integration tests need an
OpenRocket jar and a JDK with `javac` on `PATH`:

```bash
OPENROCKET_JAR=/path/to/OpenRocket.jar python -m unittest discover -s tests -v
```

JPype can start the JVM only once per process, so run each OpenRocket version in
its own process.

CI runs the integration tests against the released 22.02, 23.09 and 24.12 jars
(one job per version). 26.xx has no stable release, so if you change anything
that touches OpenRocket's API, also run the integration tests against a 26.xx
snapshot jar locally and mention the result in your pull request. Release jars
are on the [OpenRocket releases page](https://github.com/openrocket/openrocket/releases)
(`OpenRocket-<version>.jar`).

## Examples and documentation

- Keep examples short, commented and runnable from any directory. Use
  `orhelper.sample_ork_path()` for the sample rocket, and start each script with a docstring
  that says what it shows.
- Every `examples/*.py` is run against the jar by `tests/test_examples.py` (when
  `OPENROCKET_JAR` is set), so a new example is tested automatically; it must exit
  with status 0 and must not need a display. Add any extra packages it needs to `REQUIREMENTS`
  in that file and to the `examples` extra in `pyproject.toml`.
- `examples/tour.ipynb` is stored with its outputs. After changing it, re-run all cells
  (restart the kernel first) so the committed outputs match.
- If you change behaviour, update the README and add a line to [CHANGELOG.md](CHANGELOG.md)
  under an "Unreleased" heading at the top (create it if it isn't there; maintainers
  rename it to the version number when they release).

## Pull requests

- Keep them focused; one topic per pull request.
- Add or update tests for behaviour changes.
- Don't commit `.jar` files or virtual environments.
