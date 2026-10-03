from enum import Enum, auto

__all__ = [
    'OrLogLevel',
    'FlightDataType',
    'FlightEvent',
]

class OrLogLevel(Enum):
    """Log levels for [`OpenRocketInstance`][orhelper.OpenRocketInstance].

    Instead of a member you can pass its name as a string, in any case, for example `log_level="error"`.
    From quiet to chatty: `OFF`, `ERROR`, `WARN`, `INFO` (the default), `DEBUG`, `TRACE`, `ALL`.
    """
    OFF = auto()
    ERROR = auto()
    WARN = auto()
    INFO = auto()
    DEBUG = auto()
    TRACE = auto()
    ALL = auto()

# Mirrors info.openrocket.core.simulation.FlightDataType
class FlightDataType(Enum):
    """The variables OpenRocket records during a simulation, for example `TYPE_ALTITUDE`.

    Pass members, or their names as strings, to [`Helper.get_timeseries`][orhelper.Helper.get_timeseries]
    and [`Helper.get_final_values`][orhelper.Helper.get_final_values]. Values are in SI units. See
    [Flight data variables](flight-data.md) for every member, with its unit and the OpenRocket versions
    that have it.
    """
    TYPE_TIME = auto()
    TYPE_ALTITUDE = auto()
    TYPE_VELOCITY_Z = auto()
    TYPE_ACCELERATION_Z = auto()
    TYPE_VELOCITY_TOTAL = auto()
    TYPE_ACCELERATION_TOTAL = auto()
    TYPE_POSITION_X = auto()
    TYPE_POSITION_Y = auto()
    TYPE_POSITION_XY = auto()
    TYPE_POSITION_DIRECTION = auto()
    TYPE_VELOCITY_XY = auto()
    TYPE_ACCELERATION_XY = auto()
    TYPE_LATITUDE = auto()
    TYPE_LONGITUDE = auto()
    TYPE_GRAVITY = auto()
    TYPE_AOA = auto()
    TYPE_ROLL_RATE = auto()
    TYPE_PITCH_RATE = auto()
    TYPE_YAW_RATE = auto()
    TYPE_MASS = auto()
    TYPE_PROPELLANT_MASS = auto()
    TYPE_LONGITUDINAL_INERTIA = auto()
    TYPE_ROTATIONAL_INERTIA = auto()
    TYPE_CP_LOCATION = auto()
    TYPE_CG_LOCATION = auto()
    TYPE_STABILITY = auto()
    TYPE_MACH_NUMBER = auto()
    TYPE_REYNOLDS_NUMBER = auto()
    TYPE_THRUST_FORCE = auto()
    TYPE_DRAG_FORCE = auto()
    TYPE_DRAG_COEFF = auto()
    TYPE_AXIAL_DRAG_COEFF = auto()
    TYPE_FRICTION_DRAG_COEFF = auto()
    TYPE_PRESSURE_DRAG_COEFF = auto()
    TYPE_BASE_DRAG_COEFF = auto()
    TYPE_NORMAL_FORCE_COEFF = auto()
    TYPE_PITCH_MOMENT_COEFF = auto()
    TYPE_YAW_MOMENT_COEFF = auto()
    TYPE_SIDE_FORCE_COEFF = auto()
    TYPE_ROLL_MOMENT_COEFF = auto()
    TYPE_ROLL_FORCING_COEFF = auto()
    TYPE_ROLL_DAMPING_COEFF = auto()
    TYPE_PITCH_DAMPING_MOMENT_COEFF = auto()
    TYPE_YAW_DAMPING_MOMENT_COEFF = auto()
    TYPE_CORIOLIS_ACCELERATION = auto()
    TYPE_REFERENCE_LENGTH = auto()
    TYPE_REFERENCE_AREA = auto()
    TYPE_ORIENTATION_THETA = auto()
    TYPE_ORIENTATION_PHI = auto()
    TYPE_WIND_VELOCITY = auto()
    TYPE_AIR_TEMPERATURE = auto()
    TYPE_AIR_PRESSURE = auto()
    TYPE_SPEED_OF_SOUND = auto()
    TYPE_TIME_STEP = auto()
    TYPE_COMPUTATION_TIME = auto()

    # Append new members so existing numeric values remain unchanged.
    TYPE_ALTITUDE_ABOVE_SEA = auto()
    TYPE_MOTOR_MASS = auto()
    TYPE_THRUST_WEIGHT_RATIO = auto()
    TYPE_WIND_DIRECTION = auto()
    TYPE_AIR_DENSITY = auto()
    TYPE_ACCELERATION_X = auto()
    TYPE_ACCELERATION_Y = auto()
    TYPE_ACCELERATION_BODYX = auto()
    TYPE_ACCELERATION_BODYY = auto()
    TYPE_ACCELERATION_BODYZ = auto()
    TYPE_DAMPING_RATIO = auto()
    TYPE_NATURAL_FREQUENCY = auto()
    TYPE_THRUST_CORRECTION = auto()
    TYPE_CNA = auto()
    TYPE_DAMPING_MOMENT_COEFF = auto()
    TYPE_DAMPING_MOMENT_COEFF_AERODYNAMIC = auto()
    TYPE_DAMPING_MOMENT_COEFF_PROPULSIVE = auto()
    TYPE_CORRECTIVE_MOMENT_COEFF = auto()

# Mirrors info.openrocket.core.simulation.FlightEvent
class FlightEvent(Enum):
    """The kinds of event OpenRocket records during a flight, for example `APOGEE` or `BURNOUT`.

    [`Helper.get_events`][orhelper.Helper.get_events] returns them as dictionary keys. See
    [Flight events](flight-events.md) for every member.
    """
    LAUNCH = auto()
    IGNITION = auto()
    LIFTOFF = auto()
    LAUNCHROD = auto()
    BURNOUT = auto()
    EJECTION_CHARGE = auto()
    STAGE_SEPARATION = auto()
    APOGEE = auto()
    RECOVERY_DEVICE_DEPLOYMENT = auto()
    GROUND_HIT = auto()
    SIMULATION_END = auto()
    ALTITUDE = auto()
    TUMBLE = auto()
    EXCEPTION = auto()
    SIM_WARN = auto()
    SIM_ABORT = auto()
