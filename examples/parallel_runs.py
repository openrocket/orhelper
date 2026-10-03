"""Run simulations in parallel: one OpenRocket JVM per worker process.

JPype can start the JVM only once per Python process, so threads can't help and a
worker process can't be reused for a second ``OpenRocketInstance``. Instead, each
worker is a fresh process (``maxtasksperchild=1``) that starts its own JVM, runs a
whole batch of simulations and returns plain Python results.

Pass a number to choose the number of workers: python parallel_runs.py 4
"""
import math
import multiprocessing
import sys

import numpy as np

import orhelper
from orhelper import FlightDataType

WIND_SPEEDS = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]  # m/s


def run_batch(wind_speeds):
    """Runs in a worker process: start a JVM, simulate every wind speed, return the results."""
    with orhelper.OpenRocketInstance(log_level="ERROR") as instance:
        orh = orhelper.Helper(instance)
        doc = orh.load_doc(orhelper.sample_ork_path())
        sim = doc.getSimulation(0)

        results = []
        for wind in wind_speeds:
            sim.getOptions().setWindSpeedAverage(wind)
            orh.run_simulation(sim)
            data = orh.get_timeseries(sim, [FlightDataType.TYPE_ALTITUDE, FlightDataType.TYPE_POSITION_X,
                                            FlightDataType.TYPE_POSITION_Y])
            drift = math.hypot(data[FlightDataType.TYPE_POSITION_X][-1], data[FlightDataType.TYPE_POSITION_Y][-1])
            results.append((wind, float(np.max(data[FlightDataType.TYPE_ALTITUDE])), drift))
        return results


if __name__ == "__main__":  # required: the worker processes import this file
    workers = int(sys.argv[1]) if len(sys.argv) > 1 else 3
    batches = [WIND_SPEEDS[i::workers] for i in range(workers)]

    # "spawn" gives every worker a clean interpreter, which is what a JVM needs.
    with multiprocessing.get_context("spawn").Pool(processes=workers, maxtasksperchild=1) as pool:
        batch_results = pool.map(run_batch, batches, chunksize=1)

    print(f"{'wind (m/s)':>11}{'apogee (m)':>12}{'drift (m)':>11}")
    for wind, apogee, drift in sorted(row for batch in batch_results for row in batch):
        print(f"{wind:>11}{apogee:>12.1f}{drift:>11.1f}")
