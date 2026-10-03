"""Monte Carlo study of the landing zone: randomise the launch and the rocket, run many simulations.

Each run draws the launch rod angle and direction, the wind speed and the mass of two components
at random, and drops the rocket from a random starting altitude using a custom simulation listener
(``AirStart``). A second listener (``LandingPoint``) records where the rocket lands. The script prints
the mean landing distance and bearing with their standard deviations.

The distance and bearing use a flat-earth approximation, so the simulation must use OpenRocket's
"flat" geodetic computation (the default for the sample rocket). Component names ('Nose cone', 'Body
tube') are those of the sample rocket: change them to match your own.
"""
import numpy as np
import orhelper
from random import gauss
import math


class LandingPoints(list):
    "A list of landing points with ability to run simulations and populate itself"

    def __init__(self):
        self.ranges = []
        self.bearings = []

    def add_simulations(self, num):
        with orhelper.OpenRocketInstance() as instance:

            # Load the document and get simulation
            orh = orhelper.Helper(instance)
            doc = orh.load_doc(orhelper.sample_ork_path())
            sim = doc.getSimulation(0)

            # Randomize various parameters
            opts = sim.getOptions()
            rocket = sim.getRocket()

            # Run num simulations and add to self
            for p in range(num):
                print('Running simulation ', p)

                opts.setLaunchRodAngle(math.radians(gauss(45, 5)))  # 45 +- 5 deg in direction
                opts.setLaunchRodDirection(math.radians(gauss(0, 5)))  # 0 +- 5 deg in direction
                opts.setWindSpeedAverage(gauss(15, 5))  # 15 +- 5 m/s in wind
                for component_name in ('Nose cone', 'Body tube'):  # 5% in the mass of various components
                    component = orh.get_component_named(rocket, component_name)
                    mass = component.getMass()
                    component.setMassOverridden(True)
                    component.setOverrideMass(mass * gauss(1.0, 0.05))

                airstarter = AirStart(gauss(1000, 50))  # simulation listener to drop from 1000 m +- 50
                lp = LandingPoint(self.ranges, self.bearings)
                orh.run_simulation(sim, listeners=(airstarter, lp))
                self.append(lp)

    def print_stats(self):
        print(
            'Rocket landing zone %3.2f m +- %3.2f m bearing %3.2f deg +- %3.4f deg from launch site. Based on %i simulations.' % \
            (np.mean(self.ranges), np.std(self.ranges), np.degrees(np.mean(self.bearings)) % 360,
             np.degrees(np.std(self.bearings)), len(self)))


class LandingPoint(orhelper.AbstractSimulationListener):
    def __init__(self, ranges, bearings):
        self.ranges = ranges
        self.bearings = bearings

    def endSimulation(self, status, simulation_exception):
        worldpos = status.getRocketWorldPosition()
        conditions = status.getSimulationConditions()
        launchpos = conditions.getLaunchSite()
        geodetic_computation = conditions.getGeodeticComputation()

        if geodetic_computation != geodetic_computation.FLAT:
            raise Exception("GeodeticComputationStrategy type not supported")

        self.ranges.append(range_flat(launchpos, worldpos))
        self.bearings.append(bearing_flat(launchpos, worldpos))


class AirStart(orhelper.AbstractSimulationListener):

    def __init__(self, altitude):
        self.start_altitude = altitude

    def startSimulation(self, status):
        position = status.getRocketPosition()
        position = position.add(0.0, 0.0, self.start_altitude)
        status.setRocketPosition(position)


# OpenRocket's flat-earth conversion from degrees to metres. A degree of longitude is this long at the
# equator and shrinks with the cosine of the latitude.
METERS_PER_DEGREE_LATITUDE = 111325
METERS_PER_DEGREE_LONGITUDE_EQUATOR = 111050


def flat_offsets(start, end):
    """Return how far `end` is north and east of `start`, in metres (flat-earth approximation)."""
    north = (end.getLatitudeDeg() - start.getLatitudeDeg()) * METERS_PER_DEGREE_LATITUDE
    east = ((end.getLongitudeDeg() - start.getLongitudeDeg()) * METERS_PER_DEGREE_LONGITUDE_EQUATOR
            * math.cos(math.radians(start.getLatitudeDeg())))
    return north, east


def range_flat(start, end):
    north, east = flat_offsets(start, end)
    return math.hypot(north, east)


def bearing_flat(start, end):
    """Bearing of `end` from `start` in radians, measured clockwise from north."""
    north, east = flat_offsets(start, end)
    return math.atan2(east, north)


if __name__ == '__main__':
    points = LandingPoints()
    points.add_simulations(20)
    points.print_stats()
