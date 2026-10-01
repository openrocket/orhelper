"""Minimal orhelper example: run a simulation and print a few results.

Needs only orhelper (and its numpy dependency) plus an OpenRocket install.
"""
import numpy as np

import orhelper
from orhelper import FlightDataType

# The JVM can only be started once per Python process, so keep everything that
# talks to OpenRocket inside this `with` block.
with orhelper.OpenRocketInstance(log_level="ERROR") as instance:
    orh = orhelper.Helper(instance)

    doc = orh.load_doc(orhelper.sample_ork_path())  # or "/path/to/your.ork"
    sim = doc.getSimulation(0)
    orh.run_simulation(sim)

    data = orh.get_timeseries(sim, [FlightDataType.TYPE_TIME,
                                    FlightDataType.TYPE_ALTITUDE,
                                    FlightDataType.TYPE_VELOCITY_TOTAL])
    events = orh.get_events(sim)

    print(f"Rocket:       {doc.getRocket().getName()}")
    print(f"Apogee:       {np.max(data[FlightDataType.TYPE_ALTITUDE]):.0f} m")
    # Some series start with NaN (no velocity at t=0), so use nanmax, not max.
    print(f"Max velocity: {np.nanmax(data[FlightDataType.TYPE_VELOCITY_TOTAL]):.0f} m/s")
    print(f"Flight time:  {data[FlightDataType.TYPE_TIME][-1]:.1f} s")
    for event, times in events.items():
        print(f"  {event.name:<28} t = {times[0]:.1f} s")
