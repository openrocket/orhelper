"""Change the rocket and the launch conditions, compare the results, and save a new .ork file.

Usage: python edit_and_save.py [output.ork]    (default: a file in your temp directory)

OpenRocket objects are Java objects: ``get_component_named`` finds a component and you
call its Java getters and setters directly. Angles are in radians, masses in kg.
"""
import math
import sys
import tempfile
from pathlib import Path

import numpy as np

import orhelper
from orhelper import FlightDataType

output = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(tempfile.gettempdir()) / "simple_edited.ork"

with orhelper.OpenRocketInstance(log_level="ERROR") as instance:
    orh = orhelper.Helper(instance)

    doc = orh.load_doc(orhelper.sample_ork_path())
    sim = doc.getSimulation(0)
    rocket = doc.getRocket()


    def apogee():
        orh.run_simulation(sim)
        altitude = orh.get_timeseries(sim, [FlightDataType.TYPE_ALTITUDE])[FlightDataType.TYPE_ALTITUDE]
        return np.max(altitude)


    print(f"Original rocket:           apogee {apogee():.1f} m")

    # Make the nose cone 20 g heavier by overriding its computed mass.
    nose = orh.get_component_named(rocket, "Nose cone")
    nose.setOverrideMass(nose.getMass() + 0.020)
    nose.setMassOverridden(True)
    print(f"With a heavier nose cone:  apogee {apogee():.1f} m")

    # Launch 10 degrees off vertical into a 5 m/s wind.
    options = sim.getOptions()
    options.setLaunchRodAngle(math.radians(10))
    options.setWindSpeedAverage(5.0)
    print(f"Tilted launch, 5 m/s wind: apogee {apogee():.1f} m")

    # Save the modified document and load it back to check that the changes were kept.
    orh.save_doc(str(output), doc)
    reloaded = orh.load_doc(str(output))
    reloaded_nose = orh.get_component_named(reloaded.getRocket(), "Nose cone")
    print(f"Saved to {output}; nose cone mass in the saved file: {reloaded_nose.getMass() * 1000:.0f} g")
