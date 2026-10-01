# Changelog

Notable changes to orhelper. Releases before this file was started are listed
on the [tags page](https://github.com/openrocket/orhelper/tags) and in the git history.

## Unreleased

### Added
- Exceptions for startup problems: `OrHelperError` (a `RuntimeError`) and its
  subclasses `OpenRocketNotFoundError`, `JVMNotFoundError` and `JVMAlreadyStartedError`.
  Messages say what was searched and how to fix it.
- `OpenRocketInstance(jvm_args=[...])` passes extra options to the JVM, for example
  `-Xmx4g` or `-Djava.awt.headless=true`.
- `orhelper.sample_ork_path()` returns the path of a sample rocket that is now
  bundled with the package, so examples and the quickstart work after `pip install`.
- `examples/quickstart.py`, a minimal example that needs no plotting libraries.
- Support for OpenRocket 24.12 and 26.xx, plus compatibility tests
  (`tests/test_compatibility.py`, and `tests/test_integration.py` with `OPENROCKET_JAR`).
- GitHub Actions workflow running the unit tests and checking the package build.
- CI job that runs the Java integration tests against the released OpenRocket 22.02,
  23.09 and 24.12 jars.
- `CONTRIBUTING.md` and this changelog.

### Changed
- **Behaviour change:** a missing OpenRocket installation, jar or JVM now raises
  `OpenRocketNotFoundError` / `JVMNotFoundError` instead of calling `sys.exit()`, so it can be
  caught with `except Exception` and no longer ends notebooks. Code that caught `SystemExit`
  should catch `orhelper.OrHelperError` instead.
- **Behaviour change:** starting a second JVM in one process raises `JVMAlreadyStartedError`
  instead of a bare `OSError`, and `Helper(...)` on a stopped instance raises `OrHelperError`
  instead of `Exception`.
- **Behaviour change:** unknown keyword arguments to `OpenRocketInstance` (for example a
  misspelt `jvm_path=`) raise `TypeError`; wrongly typed paths raise `TypeError` instead of
  being ignored. Log level names are case-insensitive and an unknown name raises `ValueError`.
- README rewritten with a quickstart, a "how it works" overview, common tasks and
  troubleshooting.
- Packaging moved from `setup.py` to `pyproject.toml`: corrected project URL, added
  classifiers, license and extras (`orhelper[examples]`, `orhelper[pandas]`). The
  minimum Python version is now 3.9 and the minimum JPype version 1.3.
- `examples/simple.ork` moved to `orhelper/data/simple.ork`.

### Fixed
- The integration test comparing `get_final_values` with the last time-series sample
  failed when that sample is NaN, as it is for motor mass in some OpenRocket
  development builds; it now compares NaN-aware.
- Fixed the typo in the `get_final_values` docstring and documented `branch_number`, the
  return value and that the final value can be NaN.
- `log_level` now works for Python logging: the enum's raw integers (1-7) were being passed
  to `logging` as levels, so everything was always logged, including other libraries' DEBUG
  messages. orhelper no longer calls `logging.basicConfig()` or touches the root logger; it
  sets the level of the `orhelper` logger only. As a result its messages are not printed
  unless the application configures logging.
- Startup no longer crashes on an unsupported platform or when `PROGRAMFILES` is unset.
- `package_data` pointed at a removed directory, so the examples were not
  installed. The sample rocket is now included correctly.
