"""Simulate a multistage rocket and read the data of each flight branch.

A multistage simulation has one *branch* per separated part: branch 0 is the sustainer,
the others are boosters. ``get_timeseries``, ``get_final_values`` and ``get_events`` all
take a ``branch_number``.

The example rocket is one of the examples bundled inside the OpenRocket jar. Use your
own multistage .ork file with ``orh.load_doc("my_rocket.ork")``.
"""
import tempfile
from pathlib import Path
from zipfile import ZipFile

import numpy as np

import orhelper
from orhelper import FlightDataType


def extract_two_stage_example(jar, directory):
    """Copy the 'Two stage' example rocket out of the OpenRocket jar and return its path."""
    with ZipFile(str(jar)) as archive:
        name = next(n for n in archive.namelist()
                    if n.startswith("datafiles/examples/") and n.endswith(".ork")
                    and ("Two stage" in n or "Two-stage" in n))
        path = Path(directory) / "two_stage.ork"
        path.write_bytes(archive.read(name))
    return path


def branch_name(branch):
    # The Java method was renamed from getBranchName() to getName() in OpenRocket 24.12.
    getter = getattr(branch, "getName", None) or branch.getBranchName
    return str(getter())


with orhelper.OpenRocketInstance(log_level="ERROR") as instance:
    orh = orhelper.Helper(instance)

    with tempfile.TemporaryDirectory() as directory:
        doc = orh.load_doc(str(extract_two_stage_example(instance.jar, directory)))
    sim = doc.getSimulation(0)
    orh.run_simulation(sim)

    flight = sim.getSimulatedData()
    for branch_number in range(flight.getBranchCount()):
        data = orh.get_timeseries(sim, [FlightDataType.TYPE_ALTITUDE], branch_number)
        events = orh.get_events(sim, branch_number)
        print(f"Branch {branch_number} ({branch_name(flight.getBranch(branch_number))}): "
              f"apogee {np.nanmax(data[FlightDataType.TYPE_ALTITUDE]):.0f} m")
        for event, times in events.items():
            print(f"    {event.name:<28} t = {times[0]:.1f} s")
