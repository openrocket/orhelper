import os
import contextlib
import platform
import logging
from copy import copy
from pathlib import Path
import shutil
import sys
from typing import Union, List, Iterable, Dict

import jpype
import jpype.imports
import numpy as np

from ._enums import *

logger = logging.getLogger(__name__)

__all__ = [
    'OpenRocketInstance',
    'AbstractSimulationListener',
    'Helper',
    'JIterator',
]

CLASSPATH = os.environ.get("CLASSPATH", "OpenRocket.jar")

class OpenRocketInstance:
    """ This class is designed to be called using the 'with' construct. This
        will ensure that no matter what happens within that context, the 
        JVM will always be shutdown.
    """

    def __init__(self, jar_path: str = CLASSPATH, log_level: Union[OrLogLevel, str] = OrLogLevel.INFO, **kwargs):
        """ keyword arguments:
            orhome: location of installed OpenRocket.  Default is
                platform-dependant default installation location.
            jar: location of OpenRocket .jar file.  Default is
                location in installed OpenRocket.
            jvm: location of Java Virtual Machine.  Default is
                location in installed OpenRocket.
            loglevel: log level.  Allowed values are 'OFF', 'ERROR',
                'WARN', 'INFO', 'DEBUG', 'TRACE', and 'ALL'. Default is 'INFO'
        legacy positional arguments:
            jar_path: location of OpenRocket .jar file, if not specified by
                keyword argument above.  Defaults are (1) value of CLASSPATH environment
                variable if any, or (2) 'OpenRocket.jar'
            log_level can be either 'OFF', 'ERROR', 'WARN', 'INFO', 'DEBUG', 'TRACE' and 'ALL',
                if not specified by keyword argument
        """

        # Get orhome, jar, jvm, and log level from kwargs
        orhome = None
        with contextlib.suppress(Exception) :
            orhome = Path(kwargs.get("orhome", None))
        if orhome is not None :
            if Path.exists(orhome) :
                installed = True
            else :
                sys.exit(f"Specified OpenRocket installation directory '{orhome}' not found")
            
        self.jar = None
        with contextlib.suppress(Exception) :
            self.jar = Path(kwargs.get("jar", None))
        if (self.jar is not None) and not Path.exists(self.jar) :
            sys.exit(f"Specified jar file '{self.jar}' not found")

        self.jvm = None
        with contextlib.suppress(Exception) :            
            self.jvm = Path(kwargs.get("jvm", None))
        if (self.jvm is not None) and not Path.exists(self.jvm) :
            sys.exit(f"Specified jvm file '{self.jvm}' not found")

        log_level = kwargs.get('loglevel', log_level)
        if isinstance(log_level, str):
            self.or_log_level = OrLogLevel[log_level]
        else:
            self.or_log_level = log_level

        logging.basicConfig(level=self.or_log_level.value)

        # if either jar or jvm is not specified, try to get them from
        # the installed OpenRocket.
        if (self.jar is None) or (self.jvm is None) :

            # if location of OR is not specified, look in
            # platform-specific default location
            if orhome is None :
                if platform.system() == 'Linux' :
                    orhome = Path(Path.home(), 'OpenRocket')
                elif platform.system() == 'Darwin' :
                    orhome = Path('/Applications', 'OpenRocket.app', 'Contents', 'Resources')
                elif platform.system() == 'Windows' :
                    orhome = Path(os.getenv('PROGRAMFILES'), 'OpenRocket')
                if Path.exists(orhome) :
                    installed = True
                else :
                    installed = False

            print(f'orhome is {orhome}')
            
            # if we found an installation, pull jar and/or jvm from it
            if installed :
                logger.info(f" OpenRocket installation found at '{orhome}'")
                if self.jar is None :
                    if platform.system() == 'Darwin' :
                        jarglob = list(Path(orhome, 'app', 'jar').glob('OpenRocket*.jar'))
                    else :
                        jarglob = list(Path(orhome, 'jar').glob('OpenRocket*.jar'))
                    if (jarglob is not None) and (len(jarglob)) > 0 :
                        self.jar = jarglob[0]
                    else :
                        sys.exit(f"No OpenRocket jar file found in installed OpenRocket at '{orhome}'")

                if self.jvm is None :
                    if platform.system() == 'Darwin' :
                        self.jvm = Path(orhome, 'jre.bundle', 'Contents', 'Home', 'lib', 'server', 'libjvm.dylib')
                    elif platform.system() =='Linux' :
                        self.jvm = Path(orhome, 'jre', 'lib', 'server', 'libjvm.so')
                    elif platform.system() == 'Windows' :
                        self.jvm = Path(orhome, 'jre', 'bin', 'server', 'jvm.dll')
                    if not Path.exists(self.jvm) :
                        sys.exit(f"No JVM found in installed OpenRocket at '{orhome}'")
                        
        # if we haven't found a jvm, use system default
        if self.jvm is None :
            self.jvm = Path(jpype.getDefaultJVMPath())

        # if we still haven't found a jar, we'll take it from the positional argument
        # (which in turn means the given argument, CLASSPATH, or OpenRocket.jar)
        if self.jar is None :
            self.jar = Path(jar_path)
            if not Path.exists(self.jar) :
                sys.exit(f"No jar file found at positional arg value, specified CLASSPATH, or default '{self.jar}'")

        logger.info(f" jar = '{self.jar}'")
        logger.info(f" jvm = '{self.jvm}'")

        self.openrocket_core = None
        self.openrocket_swing = None
        self.started = False

    def __enter__(self):
        jpype.startJVM(f'{self.jvm}', "-ea", f"-Djava.class.path={self.jar}")

        # ----- Java imports -----
        self.openrocket_core = jpype.JPackage("info").openrocket.core
        self.openrocket_swing = jpype.JPackage("info").openrocket.swing
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

        gui_module.startLoader()

        # Ensure that loaders are done loading before continuing
        # Without this there seems to be a race condition bug that leads to the whole thing freezing
        preset_loader = _get_private_field(gui_module, "presetLoader")
        preset_loader.blockUntilLoaded()
        motor_loader = _get_private_field(gui_module, "motorLoader")
        motor_loader.blockUntilLoaded()

        self.started = True

        return self

    def __exit__(self, ex, value, tb):

        # Dispose any open windows (usually just a loading screen) which can prevent the JVM from shutting down
        for window in jpype.java.awt.Window.getWindows():
            window.dispose()

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
        return jpype.JProxy((
            jpype.JPackage("info").openrocket.core.simulation.listeners.SimulationListener,
            jpype.JPackage("info").openrocket.core.simulation.listeners.SimulationEventListener,
            jpype.JPackage("info").openrocket.core.simulation.listeners.SimulationComputationListener,
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
            raise Exception("OpenRocketInstance not yet started")

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
        if isinstance(flight_data_type, FlightDataType):
            name = flight_data_type.name
        elif isinstance(flight_data_type, str):
            name = flight_data_type
        else:
            raise TypeError("Invalid type for flight_data_type")

        return getattr(self.openrocket_core.simulation.FlightDataType, name)

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
        return {getattr(self.openrocket_core.simulation.FlightEvent.Type, x.name): x for x in FlightEvent}[flight_event]

    def get_events(self, simulation) -> Dict[FlightEvent, float]:
        """Returns a dictionary of all the flight events in a given simulation.
           Key is FlightEvent and value is a list of all the times at which the event occurs.
        """
        branch = simulation.getSimulatedData().getBranch(0)

        output = dict()
        for ev in branch.getEvents():
            type = self.translate_flight_event(ev.getType())
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

def _get_private_field(obj, field_name):
    field = obj.getClass().getDeclaredField(field_name)
    field.setAccessible(True)
    ret = field.get(obj)
    field.setAccessible(False)
    return ret
