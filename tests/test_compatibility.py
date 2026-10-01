import tempfile
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from orhelper import FlightDataType, FlightEvent, Helper, OpenRocketInstance


def make_helper(types):
    core = SimpleNamespace(simulation=SimpleNamespace(FlightDataType=types))
    return Helper(SimpleNamespace(started=True, openrocket_core=core, openrocket_swing=None))


class CompatibilityTests(unittest.TestCase):
    def test_existing_enum_values_are_preserved(self):
        self.assertEqual(FlightDataType.TYPE_TIME.value, 1)
        self.assertEqual(FlightDataType.TYPE_PROPELLANT_MASS.value, 21)
        self.assertEqual(FlightDataType.TYPE_COMPUTATION_TIME.value, 55)
        self.assertEqual(FlightEvent.LAUNCH.value, 1)
        self.assertEqual(FlightEvent.EXCEPTION.value, 14)

    def test_legacy_mass_name_resolves_to_motor_mass(self):
        motor_mass = object()
        helper = make_helper(SimpleNamespace(TYPE_MOTOR_MASS=motor_mass))
        self.assertIs(helper.translate_flight_data_type(FlightDataType.TYPE_PROPELLANT_MASS), motor_mass)
        self.assertIs(helper.translate_flight_data_type("TYPE_PROPELLANT_MASS"), motor_mass)

    def test_modern_mass_name_resolves_on_older_api(self):
        propellant_mass = object()
        helper = make_helper(SimpleNamespace(TYPE_PROPELLANT_MASS=propellant_mass))
        self.assertIs(helper.translate_flight_data_type(FlightDataType.TYPE_MOTOR_MASS), propellant_mass)

    def test_native_mass_fields_take_precedence(self):
        types = SimpleNamespace(TYPE_PROPELLANT_MASS=object(), TYPE_MOTOR_MASS=object())
        helper = make_helper(types)
        for name in ("TYPE_PROPELLANT_MASS", "TYPE_MOTOR_MASS"):
            self.assertIs(helper.translate_flight_data_type(name), getattr(types, name))

    def test_unavailable_variable_has_a_clear_error(self):
        helper = make_helper(SimpleNamespace())
        with self.assertRaisesRegex(AttributeError, "TYPE_ACCELERATION_BODYX.*not available"):
            helper.translate_flight_data_type(FlightDataType.TYPE_ACCELERATION_BODYX)

    def test_invalid_variable_type_is_rejected(self):
        with self.assertRaises(TypeError):
            make_helper(SimpleNamespace()).translate_flight_data_type(42)

    def test_events_do_not_require_new_java_constants(self):
        helper = make_helper(SimpleNamespace())
        for name in ("LAUNCH", "EXCEPTION", "SIM_WARN", "SIM_ABORT"):
            event = SimpleNamespace(name=lambda: name)
            self.assertIs(helper.translate_flight_event(event), FlightEvent[name])

    def test_events_can_be_read_from_a_booster_branch(self):
        helper = make_helper(SimpleNamespace())
        event = SimpleNamespace(
            getType=lambda: SimpleNamespace(name=lambda: "STAGE_SEPARATION"),
            getTime=lambda: 2.5,
        )
        branch = SimpleNamespace(getEvents=lambda: [event, event])
        data = Mock()
        data.getBranch.return_value = branch
        simulation = SimpleNamespace(getSimulatedData=lambda: data)
        self.assertEqual(helper.get_events(simulation, 1), {FlightEvent.STAGE_SEPARATION: [2.5, 2.5]})
        data.getBranch.assert_called_once_with(1)

    def test_explicit_jar_paths_override_the_installation(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            (home / "jar").mkdir()
            installed = home / "jar" / "OpenRocket-installed.jar"
            installed.touch()
            custom = home / "OpenRocket-custom.jar"
            custom.touch()
            jvm = home / "libjvm.so"
            jvm.touch()
            with patch("orhelper._orhelper.platform.system", return_value="Linux"):
                positional = OpenRocketInstance(str(custom), orhome=home, jvm=jvm)
                keyword = OpenRocketInstance(orhome=home, jar=custom, jvm=jvm)
                overridden = OpenRocketInstance(str(installed), orhome=home, jar=custom, jvm=jvm)
                default = OpenRocketInstance(orhome=home, jvm=jvm)
            self.assertEqual(positional.jar, custom)
            self.assertEqual(keyword.jar, custom)
            self.assertEqual(overridden.jar, custom)
            self.assertEqual(default.jar, installed)

    def test_failed_initialization_shuts_down_the_jvm(self):
        instance = OpenRocketInstance.__new__(OpenRocketInstance)
        instance.jvm = "test-jvm"
        instance.jar = "test.jar"
        instance.started = False
        with patch("orhelper._orhelper.jpype.startJVM"), \
                patch("orhelper._orhelper.jpype.shutdownJVM") as shutdown, \
                patch.object(instance, "_dispose_windows") as dispose, \
                patch.object(instance, "_initialize", side_effect=RuntimeError("startup failed")):
            with self.assertRaisesRegex(RuntimeError, "startup failed"):
                instance.__enter__()
            dispose.assert_called_once_with()
            shutdown.assert_called_once_with()
        self.assertFalse(instance.started)


if __name__ == "__main__":
    unittest.main()
