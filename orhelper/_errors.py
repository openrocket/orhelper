__all__ = [
    'OrHelperError',
    'OpenRocketNotFoundError',
    'JVMNotFoundError',
    'JVMAlreadyStartedError',
]


class OrHelperError(RuntimeError):
    """Base class for errors raised by orhelper itself."""


class OpenRocketNotFoundError(OrHelperError):
    """The OpenRocket installation or jar file could not be found.

    Point orhelper at it with ``OpenRocketInstance(jar="/path/to/OpenRocket.jar")``
    or ``OpenRocketInstance(orhome="/path/to/OpenRocket")``.
    """


class JVMNotFoundError(OrHelperError):
    """No usable Java Virtual Machine could be found.

    Point orhelper at one with ``OpenRocketInstance(jvm="/path/to/libjvm.so")``,
    or install a Java runtime (Java 17 for OpenRocket 23.09 and newer).
    """


class JVMAlreadyStartedError(OrHelperError):
    """The JVM was already started in this Python process.

    JPype can start the JVM only once per process, even after it was shut down.
    Do all OpenRocket work inside a single ``with OpenRocketInstance()`` block,
    or use a new process.
    """
