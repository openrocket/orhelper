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
its own process. If you change anything that touches OpenRocket's API, run the
integration tests against as many supported versions (22.02, 23.09, 24.12, 26.xx)
as you can and mention which ones in your pull request.

## Examples and documentation

- Keep examples short, commented and runnable from any directory. Use
  `orhelper.sample_ork_path()` for the sample rocket.
- If you change behaviour, update the README and add a line under "Unreleased"
  in [CHANGELOG.md](CHANGELOG.md).

## Pull requests

- Keep them focused; one topic per pull request.
- Add or update tests for behaviour changes.
- Don't commit `.jar` files or virtual environments.
