"""Run your own Python code during a simulation with a simulation listener.

Subclass ``orhelper.AbstractSimulationListener``, override only the hooks you need and
pass instances to ``run_simulation``. The hooks are called from OpenRocket with Java
objects: here ``status`` is a Java ``SimulationStatus``.

OpenRocket may *clone* a listener (once per branch or run). The clone is a shallow copy,
so lists and dicts you create in ``__init__`` are shared with the original: read your
results from the instance you passed in, as done below.
"""
import numpy as np

import orhelper
from orhelper import FlightDataType


class AltitudeTracker(orhelper.AbstractSimulationListener):
    """Record the time and altitude after every simulation step."""

    def __init__(self):
        self.times = []
        self.altitudes = []

    def postStep(self, status):
        self.times.append(status.getSimulationTime())
        self.altitudes.append(status.getRocketPosition().z)  # z is up

    def endSimulation(self, status, simulation_exception):
        print(f"Simulation ended after {status.getSimulationTime():.1f} s")


with orhelper.OpenRocketInstance(log_level="ERROR") as instance:
    orh = orhelper.Helper(instance)

    doc = orh.load_doc(orhelper.sample_ork_path())
    sim = doc.getSimulation(0)

    tracker = AltitudeTracker()
    orh.run_simulation(sim, listeners=[tracker])

    data = orh.get_timeseries(sim, [FlightDataType.TYPE_ALTITUDE])
    print(f"The listener saw {len(tracker.times)} simulation steps")
    print(f"Apogee seen by the listener:  {max(tracker.altitudes):.1f} m")
    print(f"Apogee in the stored data:    {np.max(data[FlightDataType.TYPE_ALTITUDE]):.1f} m")
