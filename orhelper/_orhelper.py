import os
import platform
import logging
from copy import copy
from pathlib import Path
import shutil
from typing import Union, List, Iterable, Dict, Optional

import jpype
import jpype.imports
import numpy as np

from ._enums import *
from ._errors import *

logger = logging.getLogger(__name__)

__all__ = [
    'OpenRocketInstance',
    'AbstractSimulationListener',
    'Helper',
    'JIterator',
]

CLASSPATH = os.environ.get("CLASSPATH", "OpenRocket.jar")

# Python has no OFF/TRACE/ALL levels, so map the OrLogLevel names onto the closest ones.
_PYTHON_LOG_LEVELS = {
    OrLogLevel.OFF: logging.CRITICAL + 1,
    OrLogLevel.ERROR: logging.ERROR,
    OrLogLevel.WARN: logging.WARNING,
    OrLogLevel.INFO: logging.INFO,
    OrLogLevel.DEBUG: logging.DEBUG,
    OrLogLevel.TRACE: 5,
    OrLogLevel.ALL: 1,
}

_KEYWORD_ARGUMENTS = ("orhome", "jar", "jvm", "jvm_args", "loglevel")


def _to_path(value, name: str) -> Optional[Path]:
    if value is None:
        return None
    try:
        return Path(value)
    except TypeError:
        raise TypeError(f"'{name}' must be a path (str or os.PathLike), not {type(value).__name__}") from None


def _parse_log_level(level) -> OrLogLevel:
    if isinstance(level, OrLogLevel):
        return level
    if isinstance(level, str):
        try:
            return OrLogLevel[level.upper()]
        except KeyError:
            pass
        raise ValueError(f"Unknown log level '{level}'. Allowed values are: "
                         f"{', '.join(member.name for member in OrLogLevel)}")
    raise TypeError(f"log level must be an OrLogLevel or a string, not {type(level).__name__}")


def _parse_jvm_args(value) -> tuple:
    if value is None:
        return ()
    if isinstance(value, (str, bytes)):
        raise TypeError("'jvm_args' must be a list of strings, for example ['-Xmx2g'], not a single string")
    try:
        args = tuple(value)
    except TypeError:
        raise TypeError("'jvm_args' must be a list of strings, for example ['-Xmx2g']") from None
    if not all(isinstance(arg, str) for arg in args):
        raise TypeError("'jvm_args' must be a list of strings, for example ['-Xmx2g']")
    return args


def _default_orhome() -> Optional[Path]:
    """Default location of an installed OpenRocket on this platform, if known."""
    system = platform.system()
    if system == 'Linux':
        return Path(Path.home(), 'OpenRocket')
    if system == 'Darwin':
        return Path('/Applications', 'OpenRocket.app', 'Contents', 'Resources')
    if system == 'Windows':
        program_files = os.getenv('PROGRAMFILES')
        if program_files:
            return Path(program_files, 'OpenRocket')
    return None


def _installed_jvm(orhome: Path) -> Optional[Path]:
    system = platform.system()
    if system == 'Darwin':
        return Path(orhome, 'jre.bundle', 'Contents', 'Home', 'lib', 'server', 'libjvm.dylib')
    if system == 'Linux':
        return Path(orhome, 'jre', 'lib', 'server', 'libjvm.so')
    if system == 'Windows':
        return Path(orhome, 'jre', 'bin', 'server', 'jvm.dll')
    return None


class OpenRocketInstance:
    """Starts OpenRocket (a Java virtual machine) for the duration of a `with` block.

    Everything that talks to OpenRocket has to happen inside the block; leaving it shuts the JVM down.
    Java can be started only **once per Python process**, so keep all OpenRocket work in a single block
    (a second block, even after the first one ended, raises [`JVMAlreadyStartedError`][orhelper.JVMAlreadyStartedError]).

    By default the installed OpenRocket is used. Pass `jar`, `jvm` or `orhome` to choose another one.

    Example:
        ```python
        import orhelper

        with orhelper.OpenRocketInstance() as instance:
            helper = orhelper.Helper(instance)
            ...
        ```

    Attributes:
        jar (pathlib.Path): The OpenRocket jar that is used.
        jvm (pathlib.Path): The Java virtual machine library that is used.
        jvm_args (tuple[str, ...]): Extra arguments given to the JVM.
        or_log_level (OrLogLevel): The log level.
        started (bool): True while the JVM is running.
        openrocket_core: The Java package that holds OpenRocket's core classes, for example
            `instance.openrocket_core.simulation.FlightDataType`. This is `info.openrocket.core`, or
            `net.sf.openrocket` in OpenRocket 22.02 and 23.09. `None` until the JVM has started.
        openrocket_swing: The Java package with OpenRocket's user interface classes (the same package as
            `openrocket_core` in 22.02 and 23.09). `None` until the JVM has started.
    """

    def __init__(self, jar_path: Optional[Union[str, os.PathLike]] = None,
                 log_level: Union[OrLogLevel, str] = OrLogLevel.INFO, **kwargs):
        """Prepare to start OpenRocket. The JVM itself starts when the `with` block is entered.

        Where to find OpenRocket is decided in this order: an explicit `jar` (or `jar_path`), then the
        installation given by `orhome`, then the default installation location of your platform
        (`~/OpenRocket` on Linux, `/Applications/OpenRocket.app` on macOS, `%PROGRAMFILES%\\OpenRocket` on
        Windows), then the `CLASSPATH` environment variable or `./OpenRocket.jar`. The Java runtime is taken
        from the installation when there is one, else the system default.

        Args:
            jar_path: Location of the OpenRocket jar file; the same as the `jar` keyword argument (which wins
                if both are given). An explicit jar always takes precedence over the installed one.
            log_level: Log level, as an [`OrLogLevel`][orhelper.OrLogLevel] or its name (case-insensitive):
                `OFF`, `ERROR`, `WARN`, `INFO` (the default), `DEBUG`, `TRACE` or `ALL`. This sets the
                level of OpenRocket's own Java logging and of the `orhelper` Python logger. orhelper does not
                configure Python logging handlers; call `logging.basicConfig()` to see its messages.
            **kwargs: Keyword arguments, all optional:

                - `orhome`: location of an installed OpenRocket.
                - `jar`: location of the OpenRocket jar file.
                - `jvm`: location of the Java virtual machine library (`libjvm.so`, `libjvm.dylib` or
                  `jvm.dll`).
                - `jvm_args`: list of extra arguments for the JVM, for example `["-Xmx2g"]` or
                  `["-Djava.awt.headless=true"]`.
                - `loglevel`: the same as `log_level`; takes precedence over it.

        Raises:
            TypeError: For an unknown keyword argument or an argument of the wrong type.
            ValueError: For an unknown log level.
            OpenRocketNotFoundError: If the installation or the jar can't be found.
            JVMNotFoundError: If no Java virtual machine can be found.
        """

        unknown = sorted(set(kwargs) - set(_KEYWORD_ARGUMENTS))
        if unknown:
            raise TypeError(f"OpenRocketInstance() got unexpected keyword argument(s): {', '.join(unknown)}. "
                            f"Valid keyword arguments are: {', '.join(_KEYWORD_ARGUMENTS)}")

        # Get orhome, jar, jvm, and log level from kwargs
        orhome = _to_path(kwargs.get("orhome"), "orhome")
        installed = False
        if orhome is not None:
            if not orhome.exists():
                raise OpenRocketNotFoundError(f"Specified OpenRocket installation directory '{orhome}' not found")
            installed = True

        jar = kwargs.get("jar")
        self.jar = _to_path(jar if jar is not None else jar_path, "jar")
        if self.jar is not None and not self.jar.exists():
            raise OpenRocketNotFoundError(f"Specified jar file '{self.jar}' not found")

        self.jvm = _to_path(kwargs.get("jvm"), "jvm")
        if self.jvm is not None and not self.jvm.exists():
            raise JVMNotFoundError(f"Specified jvm file '{self.jvm}' not found")

        self.jvm_args = _parse_jvm_args(kwargs.get("jvm_args"))

        self.or_log_level = _parse_log_level(kwargs.get('loglevel', log_level))
        # Only touch our own logger: a library must not configure the root logger.
        logging.getLogger(__name__.partition('.')[0]).setLevel(_PYTHON_LOG_LEVELS[self.or_log_level])

        # if either jar or jvm is not specified, try to get them from
        # the installed OpenRocket.
        if (self.jar is None) or (self.jvm is None) :

            # if location of OR is not specified, look in
            # platform-specific default location
            if orhome is None :
                orhome = _default_orhome()
                installed = orhome is not None and orhome.exists()

            # if we found an installation, pull jar and/or jvm from it
            if installed :
                logger.info(f" OpenRocket installation found at '{orhome}'")
                if self.jar is None :
                    if platform.system() == 'Darwin' :
                        jarglob = sorted(Path(orhome, 'app', 'jar').glob('OpenRocket*.jar'))
                    else :
                        jarglob = sorted(Path(orhome, 'jar').glob('OpenRocket*.jar'))
                    if len(jarglob) > 0 :
                        self.jar = jarglob[0]
                    else :
                        raise OpenRocketNotFoundError(
                            f"No OpenRocket jar file found in installed OpenRocket at '{orhome}'. "
                            f"Pass jar='/path/to/OpenRocket.jar' to select one.")

                if self.jvm is None :
                    self.jvm = _installed_jvm(orhome)
                    if self.jvm is not None and not self.jvm.exists() :
                        raise JVMNotFoundError(
                            f"No JVM found in installed OpenRocket at '{orhome}'. "
                            f"Pass jvm='/path/to/libjvm' to use a different Java runtime.")

        # if we haven't found a jvm, use system default
        if self.jvm is None :
            try :
                self.jvm = Path(jpype.getDefaultJVMPath())
            except jpype.JVMNotFoundException as e :
                raise JVMNotFoundError(
                    "No Java Virtual Machine found. Install Java (17 for OpenRocket 23.09 and newer), "
                    "set JAVA_HOME, or pass jvm='/path/to/libjvm'.") from e

        # If no jar was selected, fall back to CLASSPATH or OpenRocket.jar.
        if self.jar is None :
            self.jar = Path(CLASSPATH)
            if not self.jar.exists() :
                raise OpenRocketNotFoundError(
                    "No OpenRocket jar file found: there is no installed OpenRocket in the default location, "
                    f"and '{self.jar}' (from CLASSPATH or the default 'OpenRocket.jar') does not exist. "
                    "Pass jar='/path/to/OpenRocket.jar' or orhome='/path/to/OpenRocket'.")

        logger.info(f" jar = '{self.jar}'")
        logger.info(f" jvm = '{self.jvm}'")

        self.openrocket_core = None
        self.openrocket_swing = None
        self.started = False

    def __enter__(self):
        """Start the JVM and initialise OpenRocket.

        Returns:
            This instance.

        Raises:
            JVMAlreadyStartedError: If a JVM is running in this process, or one was started and shut down
                before: JPype can't restart it.
        """
        if jpype.isJVMStarted():
            raise JVMAlreadyStartedError(
                "A JVM is already running in this Python process. Use a single 'with OpenRocketInstance()' "
                "block for all OpenRocket work.")
        try:
            jpype.startJVM(f'{self.jvm}', "-ea", f"-Djava.class.path={self.jar}", *self.jvm_args)
        except OSError as e:
            if "restart" in str(e).lower():
                raise JVMAlreadyStartedError(
                    "The JVM was already started and shut down in this Python process, and JPype cannot "
                    "restart it. Do all OpenRocket work in a single 'with OpenRocketInstance()' block, "
                    "or use a new process.") from e
            raise

        try:
            self._initialize()
        except BaseException:
            # A failed __enter__ does not call __exit__.
            self._dispose_windows()
            jpype.shutdownJVM()
            raise

        self.started = True
        return self

    def _initialize(self):

        # ----- Java imports -----
        self.openrocket_core, self.openrocket_swing = _get_openrocket_packages()
        guice = jpype.JPackage("com").google.inject.Guice
        LoggerFactory = jpype.JPackage("org").slf4j.LoggerFactory
        Logger = jpype.JPackage("ch").qos.logback.classic.Logger

        or_logger = LoggerFactory.getLogger(Logger.ROOT_LOGGER_NAME)
        or_logger.setLevel(self._translate_log_level())
        # -----

        # Effectively a minimally viable translation of openrocket.startup.SwingStartup
        gui_module = self.openrocket_swing.startup.GuiModule()
        plugin_module = self.openrocket_core.plugin.PluginModule()

        injector = guice.createInjector(gui_module, plugin_module)

        app = self.openrocket_core.startup.Application
        app.setInjector(injector)

        # 26.x preferences initialize Swing's look and feel. Do this on the
        # calling thread before either database loader requests preferences.
        app.getPreferences()

        # Ensure that loaders are done loading before continuing
        # Without this there seems to be a race condition bug that leads to the whole thing freezing
        preset_loader = _get_private_field(gui_module, "presetLoader")
        motor_loader = _get_private_field(gui_module, "motorLoader")

        # Start the databases directly: 26.x GuiModule.startLoader() also opens
        # motor update dialogs, which fail headless and can block Python scripts.
        system = jpype.java.lang.System
        if hasattr(preset_loader, "markAsLoaded") and system.getProperty("openrocket.bypass.presets") is not None:
            preset_loader.markAsLoaded()
        else:
            preset_loader.startLoading()
        if hasattr(motor_loader, "markAsLoaded") and system.getProperty("openrocket.bypass.motors") is not None:
            motor_loader.markAsLoaded()
        else:
            initializer = getattr(self.openrocket_core.database, "MotorDatabaseInitializer", None)
            if initializer is not None:
                initializer.initialize()
            motor_loader.startLoading()

        preset_loader.blockUntilLoaded()
        motor_loader.blockUntilLoaded()

    @staticmethod
    def _dispose_windows():
        # Dispose any open windows (usually just a loading screen) which can prevent the JVM from shutting down
        for window in jpype.java.awt.Window.getWindows():
            window.dispose()

    def __exit__(self, ex, value, tb):
        """Shut the JVM down. An exception raised in the `with` block is logged and then propagates."""

        self._dispose_windows()

        jpype.shutdownJVM()
        logger.info("JVM shut down")
        self.started = False

        if ex is not None:
            logger.exception("Exception while calling OpenRocket", exc_info=(ex, value, tb))

    def _translate_log_level(self):
        # ----- Java imports -----
        Level = jpype.JPackage("ch").qos.logback.classic.Level
        # -----

        return getattr(Level, self.or_log_level.name)


class AbstractSimulationListener:
    """Base class for Python code that runs *during* an OpenRocket simulation.

    Subclass it, override the hooks you need and pass instances to
    [`Helper.run_simulation`][orhelper.Helper.run_simulation]. This is a Python version of OpenRocket's
    `AbstractSimulationListener`, so the hook names are the Java ones (camelCase) and the arguments are
    **Java objects**; `status`, for example, is a `SimulationStatus`. Every hook does nothing by default,
    so the simulation is only affected by the hooks you override.

    There are three groups of hooks:

    * **Lifecycle hooks:** [`startSimulation`][orhelper.AbstractSimulationListener.startSimulation],
      [`endSimulation`][orhelper.AbstractSimulationListener.endSimulation], their `...Branch` versions,
      [`preStep`][orhelper.AbstractSimulationListener.preStep] and
      [`postStep`][orhelper.AbstractSimulationListener.postStep].
    * **Event hooks** (`addFlightEvent`, `handleFlightEvent`, `motorIgnition`, `recoveryDeviceDeployment`):
      return `True` to let things happen normally (the default) or `False` to prevent it.
    * **Computation hooks** (`pre...` and `post...`): called around the models OpenRocket evaluates in each
      step. Return `None` (for the hooks that return a number: `float("nan")`) to leave the simulation
      alone, which is the default. Return a value of the type OpenRocket expects to replace the result:
      the `pre...` hooks replace the value before it is computed, the `post...` hooks replace the value that
      was computed.

    Warning: Keep results in a list or dict, not in a number
        OpenRocket doesn't use the object you pass in: it clones it (shallow copy) for the simulation.
        Lists and dicts created in `__init__` are shared with the copy, so you can read them afterwards.
        A number or string that a hook assigns (`self.count += 1`) is changed on the copy only, and the
        object you hold still has the old value.

    Example:
        ```python
        class AltitudeTracker(orhelper.AbstractSimulationListener):
            def __init__(self):
                self.altitudes = []          # shared with the copy that OpenRocket runs

            def postStep(self, status):
                self.altitudes.append(status.getRocketPosition().z)

        tracker = AltitudeTracker()
        helper.run_simulation(simulation, listeners=[tracker])
        print(max(tracker.altitudes))
        ```
    """

    def __str__(self):
        return (
                "'"
                + "Python simulation listener proxy : "
                + str(self.__class__.__name__)
                + "'"
        )

    def toString(self):
        return str(self)

    # SimulationListener
    def startSimulation(self, status) -> None:
        """Called when the simulation starts.

        Args:
            status: The Java `SimulationStatus`. You can change it, for example to start the rocket at another
                position.
        """

    def endSimulation(self, status, simulation_exception) -> None:
        """Called when the simulation ends, normally or because of an error.

        Args:
            status: The Java `SimulationStatus`.
            simulation_exception: The Java `SimulationException` that ended the simulation, or `None`
                if it ended normally.
        """

    def startSimulationBranch(self, status) ->  None :
        """Called when a branch starts: the sustainer, and each booster created at stage separation.

        This hook exists only in OpenRocket 26.xx; in 22.02, 23.09 and 24.12 it is never called.

        Args:
            status: The Java `SimulationStatus` of the branch.
        """

    def endSimulationBranch(self, status, simulation_exception) -> None:
        """Called when a branch ends, normally or because of an error. Like `startSimulationBranch`, only
        OpenRocket 26.xx calls it.

        Args:
            status: The Java `SimulationStatus` of the branch.
            simulation_exception: The Java `SimulationException` that ended the branch, or `None`.
        """

    def preStep(self, status) -> bool:
        """Called before every simulation step.

        Args:
            status: The Java `SimulationStatus`.

        Returns:
            `True` to take the step (the default), `False` to skip it. A skipped step does not advance the
            simulation, so don't return `False` on every call.
        """
        return True

    def postStep(self, status) -> None:
        """Called after every simulation step, also when `preStep` skipped it.

        Args:
            status: The Java `SimulationStatus`, for example `status.getSimulationTime()` or
                `status.getRocketPosition()`.
        """

    def isSystemListener(self) -> bool:
        """Whether this is one of OpenRocket's own listeners. Leave this as `False` for your own code."""
        return False

    # SimulationEventListener
    def addFlightEvent(self, status, flight_event) -> bool:
        """Called before an event is added to the event queue.

        Args:
            status: The Java `SimulationStatus`.
            flight_event: The Java `FlightEvent` that is about to be added.

        Returns:
            `True` to add the event (the default), `False` to leave it out.
        """
        return True

    def handleFlightEvent(self, status, flight_event) -> bool:
        """Called before an event is handled.

        Args:
            status: The Java `SimulationStatus`.
            flight_event: The Java `FlightEvent` that is taking place.

        Returns:
            `True` to handle the event (the default), `False` to ignore it.
        """
        return True

    def motorIgnition(self, status, motor_id, motor_mount, motor_instance) -> bool:
        """Called when a motor is about to ignite.

        Args:
            status: The Java `SimulationStatus`.
            motor_id: The id of the motor configuration.
            motor_mount: The Java motor mount that holds the motor.
            motor_instance: The motor that is being ignited.

        Returns:
            `True` to ignite the motor (the default), `False` to prevent it.
        """
        return True

    def recoveryDeviceDeployment(self, status, recovery_device) -> bool:
        """Called when a recovery device (a parachute, for example) is about to deploy.

        Args:
            status: The Java `SimulationStatus`.
            recovery_device: The Java recovery device.

        Returns:
            `True` to deploy it (the default), `False` to prevent it.
        """
        return True

    # SimulationComputationListener
    # The pre... hooks replace a value before OpenRocket computes it; the post... hooks replace the computed
    # value. None (or nan for numbers) means: leave it alone.
    def preAccelerationCalculation(self, status):
        """Replace the acceleration before it is computed. Return a Java `AccelerationData`, or `None`."""
        return None

    def preAerodynamicCalculation(self, status):
        """Replace the aerodynamic forces before they are computed. Return a Java `AerodynamicForces`, or `None`."""
        return None

    def preAtmosphericModel(self, status):
        """Replace the atmospheric conditions before they are computed. Return Java `AtmosphericConditions`, or `None`."""
        return None

    def preFlightConditions(self, status):
        """Replace the flight conditions before they are computed. Return a Java `FlightConditions`, or `None`."""
        return None

    def preGravityModel(self, status):
        """Replace the gravitational acceleration (m/s²) before it is computed. Return a number, or `nan`."""
        return float("nan")

    def preMassCalculation(self, status):
        """Replace the mass properties before they are computed. Return a Java `RigidBody`, or `None`."""
        return None

    def preSimpleThrustCalculation(self, status):
        """Replace the thrust (N) before it is computed. Return a number, or `nan`."""
        return float("nan")

    def preWindModel(self, status):
        """Replace the wind velocity before it is computed. Return a Java `Coordinate` (m/s), or `None`.

        For example, `return instance.openrocket_core.util.Coordinate(10.0, 0.0, 0.0)` gives a constant
        10 m/s wind along the x axis.
        """
        return None

    def postAccelerationCalculation(self, status, acceleration_data):
        """Replace the computed acceleration. Return a Java `AccelerationData`, or `None` to keep it."""
        return None

    def postAerodynamicCalculation(self, status, aerodynamic_forces):
        """Replace the computed aerodynamic forces. Return a Java `AerodynamicForces`, or `None` to keep them."""
        return None

    def postAtmosphericModel(self, status, atmospheric_conditions):
        """Replace the computed atmospheric conditions. Return Java `AtmosphericConditions`, or `None`."""
        return None

    def postFlightConditions(self, status, flight_conditions):
        """Replace the computed flight conditions. Return a Java `FlightConditions`, or `None` to keep them."""
        return None

    def postGravityModel(self, status, gravity):
        """Replace the computed gravitational acceleration (m/s²). Return a number, or `nan` to keep it."""
        return float("nan")

    def postMassCalculation(self, status, mass_data):
        """Replace the computed mass properties. Return a Java `RigidBody`, or `None` to keep them."""
        return None

    def postSimpleThrustCalculation(self, status, thrust):
        """Replace the computed thrust (N). Return a number, or `nan` to keep it."""
        return float("nan")

    def postWindModel(self, status, wind):
        """Replace the computed wind velocity. Return a Java `Coordinate` (m/s), or `None` to keep it."""
        return None

    def clone(self):
        """Called by OpenRocket to copy the listener. This is a shallow copy; see the warning above."""
        core, _ = _get_openrocket_packages()
        return jpype.JProxy((
            core.simulation.listeners.SimulationListener,
            core.simulation.listeners.SimulationEventListener,
            core.simulation.listeners.SimulationComputationListener,
            jpype.java.lang.Cloneable,),
            inst=copy(self))


class Helper:
    """Python-friendly operations on OpenRocket documents and simulations.

    Load and save `.ork` files, run simulations (optionally with Python
    [listeners][orhelper.AbstractSimulationListener]), and read the results as NumPy arrays.
    Everything else in OpenRocket is reached by calling the Java objects that these methods return and
    accept: documents, simulations, rockets and components are plain
    [JPype](https://jpype.readthedocs.io) Java objects.

    Example:
        ```python
        with orhelper.OpenRocketInstance() as instance:
            helper = orhelper.Helper(instance)
            document = helper.load_doc("my_rocket.ork")
            simulation = document.getSimulation(0)
            helper.run_simulation(simulation)
            data = helper.get_timeseries(simulation, [orhelper.FlightDataType.TYPE_ALTITUDE])
        ```

    Attributes:
        openrocket_core: The Java package with OpenRocket's core classes (see
            [`OpenRocketInstance`][orhelper.OpenRocketInstance]).
        openrocket_swing: The Java package with OpenRocket's user interface classes.
    """

    def __init__(self, open_rocket_instance: OpenRocketInstance):
        """Create a helper for a started OpenRocket.

        Args:
            open_rocket_instance: The instance from `with OpenRocketInstance() as instance`.

        Raises:
            OrHelperError: If the instance has not been started, that is, when it is used outside its
                `with` block.
        """
        if not open_rocket_instance.started:
            raise OrHelperError("OpenRocketInstance not yet started; use it inside a 'with OpenRocketInstance() as instance:' block")

        self.openrocket_core = open_rocket_instance.openrocket_core
        self.openrocket_swing = open_rocket_instance.openrocket_swing

    def load_doc(self, or_filename: Union[str, os.PathLike]):
        """Load an OpenRocket (`.ork`) file.

        Args:
            or_filename: Path of the file.

        Returns:
            The Java `OpenRocketDocument`. Use `document.getRocket()` for the rocket and
            `document.getSimulation(0)` (or `getSimulations()`) for its simulations.

        Raises:
            info.openrocket.core.file.RocketLoadException: (a Java exception) If the file is missing or can't
                be read.
        """

        or_java_file = jpype.java.io.File(os.fspath(or_filename))
        loader = self.openrocket_core.file.GeneralRocketLoader(or_java_file)
        doc = loader.load()
        return doc

    def save_doc(self, or_filename: Union[str, os.PathLike], doc):
        """Save an OpenRocket document, with the changes you made to it, to an `.ork` file.

        Args:
            or_filename: Path of the file to write. It is overwritten if it exists.
            doc: The Java `OpenRocketDocument`, as returned by [`load_doc`][orhelper.Helper.load_doc].
        """

        or_java_file = jpype.java.io.File(os.fspath(or_filename))
        saver = self.openrocket_core.file.GeneralRocketSaver()
        saver.save(or_java_file, doc)

    def run_simulation(self, sim, listeners: Optional[Iterable[AbstractSimulationListener]] = None):
        """Run a simulation. This wraps Java's `Simulation.simulate()`.

        The results are stored in the simulation; read them with
        [`get_timeseries`][orhelper.Helper.get_timeseries],
        [`get_final_values`][orhelper.Helper.get_final_values] and
        [`get_events`][orhelper.Helper.get_events], or from Java with `sim.getSimulatedData()`.

        Note:
            Each run starts by drawing a new random seed (`sim.getOptions().randomizeSeed()`), so repeated
            runs of identical settings give slightly different results when turbulence is on. This also
            changes the seed stored in the simulation's options.

        Args:
            sim: The Java `Simulation`, for example `document.getSimulation(0)`.
            listeners: Optional [`AbstractSimulationListener`][orhelper.AbstractSimulationListener]
                instances to call during the simulation.
        """

        if listeners is None:
            # this method takes in a vararg of SimulationListeners, which is just a fancy way of passing in an array, so
            # we have to pass in an array of length 0 ..
            listener_array = jpype.JArray(
                self.openrocket_core.simulation.listeners.AbstractSimulationListener, 1
            )(0)
        else:
            listener_array = [
                jpype.JProxy(
                    (
                        self.openrocket_core.simulation.listeners.SimulationListener,
                        self.openrocket_core.simulation.listeners.SimulationEventListener,
                        self.openrocket_core.simulation.listeners.SimulationComputationListener,
                        jpype.java.lang.Cloneable,
                    ),
                    inst=c,
                )
                for c in listeners
            ]

        sim.getOptions().randomizeSeed()  # Need to do this otherwise exact same numbers will be generated for each identical run
        sim.simulate(listener_array)

    def translate_flight_data_type(self, flight_data_type: Union[FlightDataType, str]):
        """Look up the Java flight data type of the OpenRocket version that is running.

        `TYPE_PROPELLANT_MASS` is a legacy name of `TYPE_MOTOR_MASS`; either works in every version.

        Args:
            flight_data_type: A [`FlightDataType`][orhelper.FlightDataType] member or its name.

        Returns:
            The Java `FlightDataType` constant.

        Raises:
            TypeError: If the argument is neither a `FlightDataType` nor a string.
            AttributeError: If this OpenRocket version doesn't have the variable.
        """
        if isinstance(flight_data_type, FlightDataType):
            name = flight_data_type.name
        elif isinstance(flight_data_type, str):
            name = flight_data_type
        else:
            raise TypeError("Invalid type for flight_data_type")

        types = self.openrocket_core.simulation.FlightDataType
        aliases = {
            "TYPE_PROPELLANT_MASS": "TYPE_MOTOR_MASS",
            "TYPE_MOTOR_MASS": "TYPE_PROPELLANT_MASS",
        }
        try:
            return getattr(types, name)
        except AttributeError:
            if name in aliases:
                return getattr(types, aliases[name])
            raise AttributeError(
                f"Flight data type '{name}' is not available in this OpenRocket version"
            ) from None

    def get_timeseries(self, simulation, variables: Iterable[Union[FlightDataType, str]], branch_number=0) \
            -> Dict[Union[FlightDataType, str], np.ndarray]:
        """Get the values of variables at every time step of a simulation.

        The values are in SI units (see [Flight data variables](flight-data.md)). Some
        variables are `nan` at some time steps, for example at the first one, so use `numpy.nanmax` and
        friends for statistics. Request [`TYPE_TIME`][orhelper.FlightDataType] to get the matching times.

        Args:
            simulation: The Java `Simulation`, after [`run_simulation`][orhelper.Helper.run_simulation].
            variables: The [`FlightDataType`][orhelper.FlightDataType] members, or their names, to get.
            branch_number: The flight branch to read: 0 is the sustainer, 1 and up are boosters.

        Returns:
            A dictionary with one NumPy array per variable, under the same key you asked with.

        Raises:
            AttributeError: If a variable doesn't exist in this OpenRocket version.
            java.lang.IndexOutOfBoundsException: (a Java exception) If the simulation has no such branch.
        """

        branch = simulation.getSimulatedData().getBranch(branch_number)
        output = dict()
        for v in variables:
            output[v] = np.array(branch.get(self.translate_flight_data_type(v)))

        return output

    def get_final_values(self, simulation, variables: Iterable[Union[FlightDataType, str]], branch_number=0) \
            -> Dict[Union[FlightDataType, str], float]:
        """Get the last value of variables in a simulation, for example where the rocket landed.

        This is the last sample of the time series, which can be `nan` for variables that are not
        recorded on the last data point (this depends on the OpenRocket version).

        Args:
            simulation: The Java `Simulation`, after [`run_simulation`][orhelper.Helper.run_simulation].
            variables: The [`FlightDataType`][orhelper.FlightDataType] members, or their names, to get.
            branch_number: The flight branch to read: 0 is the sustainer, 1 and up are boosters.

        Returns:
            A dictionary that maps each variable to its final value, in SI units.

        Raises:
            AttributeError: If a variable doesn't exist in this OpenRocket version.
        """

        branch = simulation.getSimulatedData().getBranch(branch_number)
        output = dict()
        for v in variables:
            output[v] = branch.get(self.translate_flight_data_type(v))[-1]

        return output

    def translate_flight_event(self, flight_event) -> FlightEvent:
        """Convert a Java `FlightEvent.Type` to the [`FlightEvent`][orhelper.FlightEvent] enum.

        Raises:
            KeyError: If the event type is not in the `FlightEvent` enum, for example one added by a newer
                OpenRocket.
        """
        # Resolve only this event; older releases may lack newer Java constants.
        return FlightEvent[str(flight_event.name())]

    def get_events(self, simulation, branch_number=0) -> Dict[FlightEvent, List[float]]:
        """Get the events that happened during a simulated flight, and when.

        Events that the [`FlightEvent`][orhelper.FlightEvent] enum doesn't know, from a newer OpenRocket, are
        skipped with a warning in the log.

        Args:
            simulation: The Java `Simulation`, after [`run_simulation`][orhelper.Helper.run_simulation].
            branch_number: The flight branch to read: 0 is the sustainer, 1 and up are boosters.

        Returns:
            A dictionary that maps each [`FlightEvent`][orhelper.FlightEvent] that occurred to the list of
            times, in seconds, at which it did. Most events occur once.
        """
        branch = simulation.getSimulatedData().getBranch(branch_number)

        output = dict()
        for ev in branch.getEvents():
            try:
                type = self.translate_flight_event(ev.getType())
            except KeyError:
                # Event type added by a newer OpenRocket than this enum knows about
                logger.warning(f"Skipping unknown flight event '{ev.getType().name()}'")
                continue
            if type in output:
                output[type].append(float(ev.getTime()))
            else:
                output[type] = [float(ev.getTime())]

        return output

    def get_component_named(self, root, name):
        """Find a part of the rocket by its name.

        Args:
            root: The Java component to search from, usually the rocket: `document.getRocket()`. Its
                sub-components are searched too.
            name: The name of the component, as shown in OpenRocket.

        Returns:
            The first Java `RocketComponent` with that name. Change it with its Java setters, for
            example `setLength(...)` or `setOverrideMass(...)`.

        Raises:
            ValueError: If there is no component with that name.
        """

        for component in JIterator(root):
            if component.getName() == name:
                return component
        raise ValueError(root.toString() + " has no component named " + name)


class JIterator:
    """Wraps a Java rocket component so that you can walk its tree of sub-components in a `for` loop.

    Example:
        ```python
        for component in orhelper.JIterator(document.getRocket()):
            print(component.getName())
        ```
    """

    def __init__(self, jit):
        """Wrap a component.

        Args:
            jit: A Java object that has an `iterator(True)` method, such as a `RocketComponent`.
        """
        self.jit = jit.iterator(True)

    def __iter__(self):
        return self

    def __next__(self):
        if not self.jit.hasNext():
            raise StopIteration()
        else:
            return next(self.jit)

def _get_openrocket_packages():
    try:
        jpype.JClass("info.openrocket.core.startup.Application")
    except TypeError:
        # OpenRocket 22.02/23.09 used one package before the core/Swing split.
        jpype.JClass("net.sf.openrocket.startup.Application")
        package = jpype.JPackage("net").sf.openrocket
        return package, package
    package = jpype.JPackage("info").openrocket
    return package.core, package.swing


def _get_private_field(obj, field_name):
    field = obj.getClass().getDeclaredField(field_name)
    field.setAccessible(True)
    ret = field.get(obj)
    field.setAccessible(False)
    return ret
