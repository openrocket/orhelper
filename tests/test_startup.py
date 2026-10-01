"""Tests for OpenRocketInstance construction, error handling and logging (no JVM needed)."""
import logging
import tempfile
from pathlib import Path
import unittest
from unittest.mock import patch

import jpype

import orhelper
from orhelper import (Helper, JVMAlreadyStartedError, JVMNotFoundError, OpenRocketInstance,
                      OpenRocketNotFoundError, OrHelperError, OrLogLevel)


class ErrorTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.dir = Path(self.tmp.name)
        self.jar = self.dir / "OpenRocket.jar"
        self.jar.touch()
        self.jvm = self.dir / "libjvm.so"
        self.jvm.touch()

    def test_errors_are_regular_exceptions_not_system_exit(self):
        for error in (OpenRocketNotFoundError, JVMNotFoundError, JVMAlreadyStartedError):
            self.assertTrue(issubclass(error, OrHelperError))
        self.assertTrue(issubclass(OrHelperError, RuntimeError))
        self.assertFalse(issubclass(OrHelperError, SystemExit))

    def test_missing_jar_raises(self):
        with self.assertRaisesRegex(OpenRocketNotFoundError, "Specified jar file .* not found"):
            OpenRocketInstance(jar=self.dir / "missing.jar", jvm=self.jvm)

    def test_missing_positional_jar_raises(self):
        with self.assertRaises(OpenRocketNotFoundError):
            OpenRocketInstance(str(self.dir / "missing.jar"), jvm=self.jvm)

    def test_missing_orhome_raises(self):
        with self.assertRaisesRegex(OpenRocketNotFoundError, "installation directory"):
            OpenRocketInstance(orhome=self.dir / "missing", jar=self.jar, jvm=self.jvm)

    def test_missing_jvm_raises(self):
        with self.assertRaisesRegex(JVMNotFoundError, "Specified jvm file .* not found"):
            OpenRocketInstance(jar=self.jar, jvm=self.dir / "missing.so")

    def test_installation_without_jar_raises_with_hint(self):
        with patch("orhelper._orhelper.platform.system", return_value="Linux"):
            with self.assertRaisesRegex(OpenRocketNotFoundError, "jar="):
                OpenRocketInstance(orhome=self.dir, jvm=self.jvm)

    def test_installation_without_jvm_raises_with_hint(self):
        (self.dir / "jar").mkdir()
        (self.dir / "jar" / "OpenRocket-1.jar").touch()
        with patch("orhelper._orhelper.platform.system", return_value="Linux"):
            with self.assertRaisesRegex(JVMNotFoundError, "jvm="):
                OpenRocketInstance(orhome=self.dir)

    def test_no_installation_and_no_classpath_jar_raises(self):
        with patch("orhelper._orhelper._default_orhome", return_value=None), \
                patch("orhelper._orhelper.CLASSPATH", str(self.dir / "nope.jar")):
            with self.assertRaisesRegex(OpenRocketNotFoundError, "jar="):
                OpenRocketInstance(jvm=self.jvm)

    def test_unsupported_platform_has_no_default_installation(self):
        with patch("orhelper._orhelper.platform.system", return_value="Plan9"):
            self.assertIsNone(orhelper._orhelper._default_orhome())
            self.assertIsNone(orhelper._orhelper._installed_jvm(self.dir))

    def test_windows_without_program_files_has_no_default_installation(self):
        with patch("orhelper._orhelper.platform.system", return_value="Windows"), \
                patch.dict("os.environ", {}, clear=True):
            self.assertIsNone(orhelper._orhelper._default_orhome())

    def test_no_java_raises_jvm_not_found(self):
        with patch("orhelper._orhelper._default_orhome", return_value=None), \
                patch("orhelper._orhelper.jpype.getDefaultJVMPath", side_effect=jpype.JVMNotFoundException("no java")):
            with self.assertRaisesRegex(JVMNotFoundError, "JAVA_HOME"):
                OpenRocketInstance(jar=self.jar)

    def test_unknown_keyword_argument_raises(self):
        with self.assertRaisesRegex(TypeError, "jvm_path"):
            OpenRocketInstance(jar=self.jar, jvm=self.jvm, jvm_path="/typo")

    def test_wrong_argument_type_raises(self):
        with self.assertRaisesRegex(TypeError, "'jar'"):
            OpenRocketInstance(jar=123, jvm=self.jvm)

    def test_helper_requires_started_instance(self):
        instance = OpenRocketInstance(jar=self.jar, jvm=self.jvm)
        with self.assertRaisesRegex(OrHelperError, "not yet started"):
            Helper(instance)


class StartTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.jar = Path(tmp.name) / "OpenRocket.jar"
        self.jar.touch()
        self.jvm = Path(tmp.name) / "libjvm.so"
        self.jvm.touch()

    def test_jvm_args_are_passed_to_the_jvm(self):
        instance = OpenRocketInstance(jar=self.jar, jvm=self.jvm, jvm_args=["-Xmx2g", "-Dfoo=bar"])
        with patch("orhelper._orhelper.jpype.startJVM") as start, \
                patch("orhelper._orhelper.jpype.isJVMStarted", return_value=False), \
                patch.object(instance, "_initialize"):
            instance.__enter__()
        start.assert_called_once_with(str(self.jvm), "-ea", f"-Djava.class.path={self.jar}", "-Xmx2g", "-Dfoo=bar")

    def test_jvm_args_must_be_a_list_of_strings(self):
        with self.assertRaises(TypeError):
            OpenRocketInstance(jar=self.jar, jvm=self.jvm, jvm_args="-Xmx2g")
        with self.assertRaises(TypeError):
            OpenRocketInstance(jar=self.jar, jvm=self.jvm, jvm_args=[1])

    def test_running_jvm_raises_already_started(self):
        instance = OpenRocketInstance(jar=self.jar, jvm=self.jvm)
        with patch("orhelper._orhelper.jpype.isJVMStarted", return_value=True), \
                patch("orhelper._orhelper.jpype.startJVM") as start:
            with self.assertRaises(JVMAlreadyStartedError):
                instance.__enter__()
        start.assert_not_called()

    def test_restarting_a_stopped_jvm_raises_already_started(self):
        instance = OpenRocketInstance(jar=self.jar, jvm=self.jvm)
        with patch("orhelper._orhelper.jpype.isJVMStarted", return_value=False), \
                patch("orhelper._orhelper.jpype.startJVM", side_effect=OSError("JVM cannot be restarted")):
            with self.assertRaisesRegex(JVMAlreadyStartedError, "single 'with"):
                instance.__enter__()

    def test_other_os_errors_are_not_translated(self):
        instance = OpenRocketInstance(jar=self.jar, jvm=self.jvm)
        with patch("orhelper._orhelper.jpype.isJVMStarted", return_value=False), \
                patch("orhelper._orhelper.jpype.startJVM", side_effect=OSError("JVM DLL not found")):
            with self.assertRaisesRegex(OSError, "DLL"):
                instance.__enter__()


class LoggingTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.kwargs = {"jar": Path(tmp.name) / "OpenRocket.jar", "jvm": Path(tmp.name) / "libjvm.so"}
        for path in self.kwargs.values():
            path.touch()
        self.logger = logging.getLogger("orhelper")
        original = self.logger.level
        self.addCleanup(self.logger.setLevel, original)

    def test_levels_map_to_python_logging_levels(self):
        expected = {"OFF": logging.CRITICAL + 1, "ERROR": logging.ERROR, "WARN": logging.WARNING,
                    "INFO": logging.INFO, "DEBUG": logging.DEBUG, "TRACE": 5, "ALL": 1}
        for name, level in expected.items():
            OpenRocketInstance(log_level=name, **self.kwargs)
            self.assertEqual(self.logger.level, level, name)

    def test_error_level_suppresses_info_messages(self):
        OpenRocketInstance(log_level=OrLogLevel.ERROR, **self.kwargs)
        self.assertFalse(self.logger.isEnabledFor(logging.INFO))
        self.assertTrue(self.logger.isEnabledFor(logging.ERROR))

    def test_level_names_are_case_insensitive(self):
        self.assertIs(OpenRocketInstance(log_level="error", **self.kwargs).or_log_level, OrLogLevel.ERROR)
        self.assertIs(OpenRocketInstance(loglevel="Debug", **self.kwargs).or_log_level, OrLogLevel.DEBUG)

    def test_unknown_level_raises_value_error_listing_choices(self):
        with self.assertRaisesRegex(ValueError, "Allowed values are: OFF, ERROR"):
            OpenRocketInstance(log_level="LOUD", **self.kwargs)

    def test_wrong_level_type_raises_type_error(self):
        with self.assertRaises(TypeError):
            OpenRocketInstance(log_level=3, **self.kwargs)

    def test_root_logger_is_not_configured(self):
        root = logging.getLogger()
        handlers, level = list(root.handlers), root.level
        OpenRocketInstance(log_level="ALL", **self.kwargs)
        self.assertEqual(root.handlers, handlers)
        self.assertEqual(root.level, level)


if __name__ == "__main__":
    unittest.main()
