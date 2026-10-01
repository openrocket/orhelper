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
    """ This class is designed to be called using the 'with' construct. This
        will ensure that no matter what happens within that context, the 
        JVM will always be shutdown.

        JPype can start the JVM only once per Python process, so keep all
        OpenRocket work inside a single 'with' block.
    """

    def __init__(self, jar_path: str = None, log_level: Union[OrLogLevel, str] = OrLogLevel.INFO, **kwargs):
        """ keyword arguments:
            orhome: location of installed OpenRocket.  Default is
                platform-dependant default installation location.
            jar: location of OpenRocket .jar file.  Default is
                location in installed OpenRocket.
            jvm: location of Java Virtual Machine.  Default is
                location in installed OpenRocket.
            jvm_args: list of extra arguments for the JVM, for example
                ['-Xmx2g'] or ['-Djava.awt.headless=true'].
            loglevel: log level.  Allowed values (case-insensitive) are 'OFF',
                'ERROR', 'WARN', 'INFO', 'DEBUG', 'TRACE', and 'ALL'. Default is 'INFO'.
                This sets the level of OpenRocket's own (Java) logging, and of the
                'orhelper' Python logger. orhelper does not configure Python logging
                handlers; use logging.basicConfig() to see its messages.
        legacy positional arguments:
            jar_path: location of OpenRocket .jar file, if not specified by
                keyword argument above. An explicit path takes precedence over
                the installed jar. Without either, try the installation, then
                CLASSPATH or 'OpenRocket.jar'.
            log_level can be either 'OFF', 'ERROR', 'WARN', 'INFO', 'DEBUG', 'TRACE' and 'ALL',
                if not specified by keyword argument

        Raises:
            TypeError: for unknown keyword arguments or arguments of the wrong type.
            ValueError: for an unknown log level.
            OpenRocketNotFoundError: if the OpenRocket installation or jar can't be found.
            JVMNotFoundError: if no Java Virtual Machine can be found.
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
    """ This is a python implementation of openrocket.simulation.listeners.AbstractSimulationListener.
        Subclasses of this are suitable for passing to helper.run_simulation.
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
        pass

    def endSimulation(self, status, simulation_exception) -> None:
        pass

    def startSimulationBranch(self, status) ->  None :
        pass

    def endSimulationBranch(self, status, simulation_exception) -> None:
        pass

    def preStep(self, status) -> bool:
        return True

    def postStep(self, status) -> None:
        pass

    def isSystemListener(self) -> bool:
        return False

    # SimulationEventListener
    def addFlightEvent(self, status, flight_event) -> bool:
        return True

    def handleFlightEvent(self, status, flight_event) -> bool:
        return True

    def motorIgnition(self, status, motor_id, motor_mount, motor_instance) -> bool:
        return True

    def recoveryDeviceDeployment(self, status, recovery_device) -> bool:
        return True

    # SimulationComputationListener
    def preAccelerationCalculation(self, status):
        return None

    def preAerodynamicCalculation(self, status):
        return None

    def preAtmosphericModel(self, status):
        return None

    def preFlightConditions(self, status):
        return None

    def preGravityModel(self, status):
        return float("nan")

    def preMassCalculation(self, status):
        return None

    def preSimpleThrustCalculation(self, status):
        return float("nan")

    def preWindModel(self, status):
        return None

    def postAccelerationCalculation(self, status, acceleration_data):
        return None

    def postAerodynamicCalculation(self, status, aerodynamic_forces):
        return None

    def postAtmosphericModel(self, status, atmospheric_conditions):
        return None

    def postFlightConditions(self, status, flight_conditions):
        return None

    def postGravityModel(self, status, gravity):
        return float("nan")

    def postMassCalculation(self, status, mass_data):
        return None

    def postSimpleThrustCalculation(self, status, thrust):
        return float("nan")

    def postWindModel(self, status, wind):
        return None

    def clone(self):
        core, _ = _get_openrocket_packages()
        return jpype.JProxy((
            core.simulation.listeners.SimulationListener,
            core.simulation.listeners.SimulationEventListener,
            core.simulation.listeners.SimulationComputationListener,
            jpype.java.lang.Cloneable,),
            inst=copy(self))


class Helper:
    """ This class contains a variety of useful helper functions and wrapper for using
        openrocket via jpype. These are intended to take care of some of the more
        cumbersome aspects of calling methods, or provide more 'pythonic' data structures
        for general use.
    """

    def __init__(self, open_rocket_instance: OpenRocketInstance):
        if not open_rocket_instance.started:
            raise OrHelperError("OpenRocketInstance not yet started; use it inside a 'with OpenRocketInstance() as instance:' block")

        self.openrocket_core = open_rocket_instance.openrocket_core
        self.openrocket_swing = open_rocket_instance.openrocket_swing

    def load_doc(self, or_filename):
        """ Loads a .ork file and returns the corresponding openrocket document """

        or_java_file = jpype.java.io.File(or_filename)
        loader = self.openrocket_core.file.GeneralRocketLoader(or_java_file)
        doc = loader.load()
        return doc

    def save_doc(self, or_filename, doc):
        """ Saves an openrocket document to a .ork file """
        
        or_java_file = jpype.java.io.File(or_filename)
        saver = self.openrocket_core.file.GeneralRocketSaver()
        saver.save(or_java_file, doc)

    def run_simulation(self, sim, listeners: List[AbstractSimulationListener] = None):
        """ This is a wrapper to the Simulation.simulate() for running a simulation
            The optional listeners parameter is a sequence of objects which extend orh.AbstractSimulationListener.
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

    def translate_flight_data_type(self, flight_data_type:Union[FlightDataType, str]):
        """Resolve a variable available in the loaded OpenRocket version.

        TYPE_PROPELLANT_MASS is kept as a legacy name for TYPE_MOTOR_MASS.
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
            -> Dict[Union[FlightDataType, str], np.array]:
        """
        Gets a dictionary of timeseries data (as numpy arrays) from a simulation given specific variable names.

        :param simulation: An openrocket simulation object.
        :param variables: A sequence of FlightDataType or strings representing the desired variables
        :param branch_number:
        :return:
        """

        branch = simulation.getSimulatedData().getBranch(branch_number)
        output = dict()
        for v in variables:
            output[v] = np.array(branch.get(self.translate_flight_data_type(v)))

        return output

    def get_final_values(self, simulation, variables: Iterable[Union[FlightDataType, str]], branch_number=0) \
            -> Dict[Union[FlightDataType, str], float]:
        """
        Gets a the final value in the time series from a simulation given variable names.

        :param simulation: An openrocket simulation object.
        :param variables: A sequence of FlightDataType or strings representing the desired variables
        :param branch_number:
        :return:
        """

        branch = simulation.getSimulatedData().getBranch(branch_number)
        output = dict()
        for v in variables:
            output[v] = branch.get(self.translate_flight_data_type(v))[-1]

        return output

    def translate_flight_event(self, flight_event) -> FlightEvent:
        # Resolve only this event; older releases may lack newer Java constants.
        return FlightEvent[str(flight_event.name())]

    def get_events(self, simulation, branch_number=0) -> Dict[FlightEvent, List[float]]:
        """Returns a dictionary of all the flight events in a given simulation.
           Key is FlightEvent and value is a list of all the times at which the event occurs.
           branch_number selects the sustainer (0 by default) or a booster branch.
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
        """ Finds and returns the first rocket component with the given name.
            Requires a root RocketComponent, usually this will be a RocketComponent.rocket instance.
            Raises a ValueError if no component found.
        """

        for component in JIterator(root):
            if component.getName() == name:
                return component
        raise ValueError(root.toString() + " has no component named " + name)


class JIterator:
    """This class is a wrapper for java iterators to allow them to be used as python iterators"""

    def __init__(self, jit):
        """Give this any java object which implements iterable"""
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
