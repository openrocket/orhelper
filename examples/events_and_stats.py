"""Print the flight events and a few summary numbers for a simulation.

Shows how to read the events (``get_events``), look up a value at a given time, and
use OpenRocket's own summary statistics from the Java ``FlightData`` object.
"""
import numpy as np

import orhelper
from orhelper import FlightDataType

TIME = FlightDataType.TYPE_TIME
ALTITUDE = FlightDataType.TYPE_ALTITUDE

with orhelper.OpenRocketInstance(log_level="ERROR") as instance:
    orh = orhelper.Helper(instance)

    doc = orh.load_doc(orhelper.sample_ork_path())
    sim = doc.getSimulation(0)
    orh.run_simulation(sim)

    data = orh.get_timeseries(sim, [TIME, ALTITUDE])
    events = orh.get_events(sim)  # {FlightEvent: [time in s, ...]}; an event can happen more than once

    # One row per event occurrence, in chronological order, with the altitude at that time.
    occurrences = sorted(((t, event) for event, times in events.items() for t in times), key=lambda row: row[0])
    print(f"{'Event':<28}{'Time (s)':>9}{'Altitude (m)':>14}")
    for t, event in occurrences:
        altitude = np.interp(t, data[TIME], data[ALTITUDE])
        print(f"{event.name:<28}{t:>9.2f}{altitude:>14.1f}")

    # OpenRocket's own summary statistics, straight from the Java FlightData object.
    flight = sim.getSimulatedData()
    print()
    print(f"Max altitude:        {flight.getMaxAltitude():.1f} m")
    print(f"Max velocity:        {flight.getMaxVelocity():.1f} m/s")
    print(f"Max acceleration:    {flight.getMaxAcceleration():.1f} m/s^2")
    print(f"Time to apogee:      {flight.getTimeToApogee():.2f} s")
    print(f"Ground hit velocity: {flight.getGroundHitVelocity():.2f} m/s")

    # Where did it land? The final value of the position series.
    landing = orh.get_final_values(sim, [FlightDataType.TYPE_POSITION_X, FlightDataType.TYPE_POSITION_Y])
    distance = np.hypot(landing[FlightDataType.TYPE_POSITION_X], landing[FlightDataType.TYPE_POSITION_Y])
    print(f"Landing distance:    {distance:.1f} m from the launch pad")
