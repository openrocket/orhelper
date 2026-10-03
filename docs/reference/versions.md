# OpenRocket versions

orhelper supports OpenRocket **22.02, 23.09, 24.12 and 26.xx** (the development version, for which there is
no stable release yet). The integration tests, and every example, run against each of them. orhelper
detects the Java package layout of the version it loads, so the same script works with all of them.

For 26.xx the tests were run on a snapshot build. For the other three, on the official releases.

## What differs between versions

Most things are the same. These are the differences you may run into.

| | 22.02 | 23.09 | 24.12 | 26.xx |
|---|:---:|:---:|:---:|:---:|
| Members of [`FlightDataType`][orhelper.FlightDataType] you can request | 56 | 56 | 60 | 73 |
| Latitude and longitude in the results are in | radians | radians | **degrees** | **degrees** |
| `SIM_WARN` and `SIM_ABORT` events | no | no | yes | yes |
| Listener hooks `startSimulationBranch` and `endSimulationBranch` | no | no | no | yes |
| Java package of the classes | `net.sf.openrocket` | `net.sf.openrocket` | `info.openrocket.core` | `info.openrocket.core` |
| Java method of a flight branch that returns its name | `getBranchName()` | `getBranchName()` | `getName()` | `getName()` |

!!! warning "Latitude and longitude change unit in 24.12"
    The same simulation, from a launch site at 45°N 10°E, gives `0.7854` and `0.1745` for
    `TYPE_LATITUDE` and `TYPE_LONGITUDE` in OpenRocket 22.02 and 23.09, and `45.0` and `10.0` in 24.12 and
    26.xx. There is no error. If your script reads them, check the version, or convert with `numpy.degrees`.

Asking for a variable that your version doesn't have, for example `TYPE_CNA` (26.xx only), raises an
`AttributeError`; the [flight data reference](flight-data.md) shows where each is available.
`TYPE_PROPELLANT_MASS` is a legacy name of `TYPE_MOTOR_MASS`, and both work with every version.

## Picking a version

By default orhelper uses the installed OpenRocket. To use another one, pass its jar:

```python
orhelper.OpenRocketInstance(jar="/path/to/OpenRocket-23.09.jar")
```

You can download every release from the
[OpenRocket releases page](https://github.com/openrocket/openrocket/releases) (`OpenRocket-<version>.jar`).
A Python process can start only one JVM, so to compare versions, run each in its own process.

## Java

OpenRocket 23.09 and newer need **Java 17**. 22.02 also runs on Java 11. The OpenRocket installers include
a Java runtime that orhelper uses.
