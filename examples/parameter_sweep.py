"""Sweep the wind speed and launch angle and write the results to a CSV file.

Usage: python parameter_sweep.py [results.csv]    (default: a file in your temp directory)

Load the result with ``pandas.read_csv("results.csv")`` for further analysis.
"""
import csv
import math
import sys
import tempfile
from pathlib import Path

import numpy as np

import orhelper
from orhelper import FlightDataType

WIND_SPEEDS = [0, 2, 4, 6, 8, 10]  # m/s
LAUNCH_ANGLES = [0, 5, 10]  # degrees from vertical

output = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(tempfile.gettempdir()) / "parameter_sweep.csv"

rows = []
with orhelper.OpenRocketInstance(log_level="ERROR") as instance:
    orh = orhelper.Helper(instance)

    doc = orh.load_doc(orhelper.sample_ork_path())
    sim = doc.getSimulation(0)
    options = sim.getOptions()

    for wind in WIND_SPEEDS:
        for angle in LAUNCH_ANGLES:
            options.setWindSpeedAverage(wind)
            options.setLaunchRodAngle(math.radians(angle))
            orh.run_simulation(sim)

            data = orh.get_timeseries(sim, [FlightDataType.TYPE_TIME, FlightDataType.TYPE_ALTITUDE,
                                            FlightDataType.TYPE_POSITION_X, FlightDataType.TYPE_POSITION_Y])
            rows.append({
                "wind_speed_m_s": wind,
                "launch_angle_deg": angle,
                "apogee_m": round(float(np.max(data[FlightDataType.TYPE_ALTITUDE])), 1),
                "flight_time_s": round(float(data[FlightDataType.TYPE_TIME][-1]), 1),
                "landing_distance_m": round(float(np.hypot(data[FlightDataType.TYPE_POSITION_X][-1],
                                                           data[FlightDataType.TYPE_POSITION_Y][-1])), 1),
            })

with open(output, "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=list(rows[0]))
    writer.writeheader()
    writer.writerows(rows)

print(f"{'wind':>6}{'angle':>7}{'apogee':>8}{'time':>7}{'landing':>9}")
for row in rows:
    print(f"{row['wind_speed_m_s']:>6}{row['launch_angle_deg']:>7}{row['apogee_m']:>8}"
          f"{row['flight_time_s']:>7}{row['landing_distance_m']:>9}")
print(f"\nWrote {len(rows)} simulations to {output}")
