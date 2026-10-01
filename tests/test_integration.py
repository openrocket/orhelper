"""Run with OPENROCKET_JAR set; each JAR needs a separate Python process."""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch
from zipfile import ZipFile

import jpype
import numpy as np

from orhelper import AbstractSimulationListener, FlightDataType, FlightEvent, Helper, OpenRocketInstance, sample_ork_path


class RecordingListener(AbstractSimulationListener):
    def __init__(self):
        self.calls = []

    def startSimulation(self, status):
        self.calls.append("start")

    def endSimulation(self, status, exception):
        self.calls.append("end")

    def startSimulationBranch(self, status):
        self.calls.append("branch_start")

    def endSimulationBranch(self, status, exception):
        self.calls.append("branch_end")

    def postWindModel(self, status, wind):
        # Exercises the Coordinate -> CoordinateIF return type change in 26.x.
        return wind


@unittest.skipUnless(os.environ.get("OPENROCKET_JAR"), "set OPENROCKET_JAR to run Java integration tests")
class IntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.jar = Path(os.environ["OPENROCKET_JAR"]).resolve()
        cls.scratch = tempfile.TemporaryDirectory(prefix="orhelper-integration-")
        cls.directory = Path(cls.scratch.name)
        subprocess.run([
            "javac", "--release", "8", "-d", str(cls.directory),
            str(Path(__file__).with_name("MemoryPreferencesFactory.java")),
        ], check=True)
        original_start = jpype.startJVM

        def start_isolated(jvm, *args, **kwargs):
            args = tuple(
                arg + os.pathsep + str(cls.directory)
                if arg.startswith("-Djava.class.path=") else arg
                for arg in args
            )
            return original_start(
                jvm, *args, "-Djava.awt.headless=true",
                "-Djava.util.prefs.PreferencesFactory=MemoryPreferencesFactory",
                "-Duser.home=" + str(cls.directory), **kwargs
            )

        cls.start_patch = patch("jpype.startJVM", side_effect=start_isolated)
        cls.start_patch.start()
        cls.instance = OpenRocketInstance(jar=cls.jar, jvm=jpype.getDefaultJVMPath(), loglevel="ERROR")
        try:
            cls.instance.__enter__()
        except BaseException:
            cls.start_patch.stop()
            cls.scratch.cleanup()
            raise
        cls.helper = Helper(cls.instance)
        cls.core = cls.instance.openrocket_core

    @classmethod
    def tearDownClass(cls):
        try:
            cls.instance.__exit__(None, None, None)
        finally:
            cls.start_patch.stop()
            cls.scratch.cleanup()

    def load_simple(self):
        return self.helper.load_doc(sample_ork_path())

    def test_all_java_data_types_and_events_are_supported(self):
        types = self.core.simulation.FlightDataType
        for field in types.class_.getFields():
            name = str(field.getName())
            if name.startswith("TYPE_"):
                with self.subTest(variable=name):
                    variable = FlightDataType[name]
                    self.assertEqual(self.helper.translate_flight_data_type(variable), getattr(types, name))
                    self.assertEqual(self.helper.translate_flight_data_type(name), getattr(types, name))
        for event in self.core.simulation.FlightEvent.Type.values():
            with self.subTest(event=str(event.name())):
                self.assertIs(self.helper.translate_flight_event(event), FlightEvent[str(event.name())])
        self.assertEqual(
            self.helper.translate_flight_data_type(FlightDataType.TYPE_PROPELLANT_MASS),
            self.helper.translate_flight_data_type(FlightDataType.TYPE_MOTOR_MASS),
        )
        prefs = self.core.startup.Application.getPreferences()
        if hasattr(prefs, "getCheckMotorDatabaseUpdates"):
            self.assertTrue(prefs.getCheckMotorDatabaseUpdates())

    def test_simulation_data_events_and_save_reload(self):
        doc = self.load_simple()
        sim = doc.getSimulation(0)
        self.helper.run_simulation(sim)
        variables = [FlightDataType.TYPE_TIME, FlightDataType.TYPE_ALTITUDE,
                     FlightDataType.TYPE_MOTOR_MASS, FlightDataType.TYPE_PROPELLANT_MASS]
        data = self.helper.get_timeseries(sim, variables)
        time = data[FlightDataType.TYPE_TIME]
        altitude = data[FlightDataType.TYPE_ALTITUDE]
        self.assertGreater(len(time), 10)
        self.assertTrue(np.all(np.isfinite(time)))
        self.assertTrue(np.all(np.diff(time) >= 0))
        self.assertEqual(len(time), len(altitude))
        self.assertGreater(np.nanmax(altitude), 10)
        self.assertAlmostEqual(np.nanmax(altitude), sim.getSimulatedData().getMaxAltitude())
        np.testing.assert_equal(data[FlightDataType.TYPE_MOTOR_MASS], data[FlightDataType.TYPE_PROPELLANT_MASS])
        if hasattr(self.core.simulation.FlightDataType, "TYPE_ACCELERATION_BODYZ"):
            extra = self.helper.get_timeseries(sim, [FlightDataType.TYPE_ACCELERATION_BODYZ])
            acceleration = extra[FlightDataType.TYPE_ACCELERATION_BODYZ]
            self.assertEqual(len(acceleration), len(time))
            self.assertTrue(np.any(np.isfinite(acceleration)))
        final = self.helper.get_final_values(sim, variables)
        for variable in variables:
            self.assertAlmostEqual(float(final[variable]), data[variable][-1])
        events = self.helper.get_events(sim)
        self.assertIn(FlightEvent.APOGEE, events)
        self.assertIn(FlightEvent.GROUND_HIT, events)
        self.assertEqual(events[FlightEvent.LAUNCH], [0.0])
        self.assertEqual(str(self.helper.get_component_named(doc.getRocket(), "Body tube").getName()), "Body tube")
        destination = str(self.directory / "roundtrip.ork")
        self.helper.save_doc(destination, doc)
        loaded = self.helper.load_doc(destination)
        self.assertEqual(doc.getSimulationCount(), loaded.getSimulationCount())
        reloaded_sim = loaded.getSimulation(0)
        self.helper.run_simulation(reloaded_sim)
        self.assertIn(FlightEvent.APOGEE, self.helper.get_events(reloaded_sim))

    def test_listener_callbacks_and_clone(self):
        listener = RecordingListener()
        clone = jpype.JObject(listener.clone(), self.core.simulation.listeners.SimulationListener)
        clone.startSimulation(None)
        self.assertEqual(listener.calls, ["start"])
        listener.calls.clear()
        self.helper.run_simulation(self.load_simple().getSimulation(0), [listener])
        self.assertEqual(listener.calls[0], "start")
        self.assertEqual(listener.calls[-1], "end")
        has_branches = hasattr(self.core.simulation.listeners.SimulationListener, "startSimulationBranch")
        if has_branches:
            self.assertIn("branch_start", listener.calls)
            self.assertIn("branch_end", listener.calls)

    def test_multistage_simulation_branches(self):
        with ZipFile(str(self.jar)) as archive:
            example = next(
                name for name in archive.namelist()
                if name.startswith("datafiles/examples/") and name.endswith(".ork")
                and ("Two stage" in name or "Two-stage" in name)
            )
            destination = self.directory / "two-stage.ork"
            destination.write_bytes(archive.read(example))
        doc = self.helper.load_doc(str(destination))
        sim = doc.getSimulation(0)
        listener = RecordingListener()
        self.helper.run_simulation(sim, [listener])
        branch_count = sim.getSimulatedData().getBranchCount()
        self.assertGreater(branch_count, 1)
        for branch_number in range(branch_count):
            data = self.helper.get_timeseries(sim, [FlightDataType.TYPE_TIME], branch_number)
            self.assertGreater(len(data[FlightDataType.TYPE_TIME]), 1)
            self.assertTrue(self.helper.get_events(sim, branch_number))
        if hasattr(self.core.simulation.listeners.SimulationListener, "startSimulationBranch"):
            self.assertEqual(listener.calls.count("branch_start"), branch_count)
            self.assertEqual(listener.calls.count("branch_end"), branch_count)


if __name__ == "__main__":
    unittest.main()
