# Changelog

Notable changes to orhelper. Releases before this file was started are listed
on the [tags page](https://github.com/openrocket/orhelper/tags) and in the git history.

## Unreleased

### Added
- `orhelper.sample_ork_path()` returns the path of a sample rocket that is now
  bundled with the package, so examples and the quickstart work after `pip install`.
- `examples/quickstart.py`, a minimal example that needs no plotting libraries.
- Support for OpenRocket 24.12 and 26.xx, plus compatibility tests
  (`tests/test_compatibility.py`, and `tests/test_integration.py` with `OPENROCKET_JAR`).
- GitHub Actions workflow running the unit tests and checking the package build.
- `CONTRIBUTING.md` and this changelog.

### Changed
- README rewritten with a quickstart, a "how it works" overview, common tasks and
  troubleshooting.
- Packaging moved from `setup.py` to `pyproject.toml`: corrected project URL, added
  classifiers, license and extras (`orhelper[examples]`, `orhelper[pandas]`). The
  minimum Python version is now 3.9 and the minimum JPype version 1.3.
- `examples/simple.ork` moved to `orhelper/data/simple.ork`.

### Fixed
- `package_data` pointed at a removed directory, so the examples were not
  installed. The sample rocket is now included correctly.
