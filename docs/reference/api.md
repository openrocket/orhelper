# API reference

Everything below is importable from the top level: `import orhelper`.

## Starting OpenRocket

::: orhelper.OpenRocketInstance

::: orhelper.OrLogLevel
    options:
      members: false

## Working with simulations

::: orhelper.Helper

::: orhelper.JIterator

## Listeners

::: orhelper.AbstractSimulationListener

## Flight data and events

The two enums mirror OpenRocket's own. All their members are listed, with their units and the versions
that have them, in [Flight data variables](flight-data.md) and [Flight events](flight-events.md).

::: orhelper.FlightDataType
    options:
      members: false

::: orhelper.FlightEvent
    options:
      members: false

## Sample data

::: orhelper.sample_ork_path

## Exceptions

All of orhelper's own errors derive from `OrHelperError`, which is a `RuntimeError`. Errors from OpenRocket
itself are Java exceptions raised by JPype.

::: orhelper.OrHelperError

::: orhelper.OpenRocketNotFoundError

::: orhelper.JVMNotFoundError

::: orhelper.JVMAlreadyStartedError
