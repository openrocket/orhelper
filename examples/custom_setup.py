"""Start OpenRocket with explicit settings and handle startup problems.

By default orhelper finds the installed OpenRocket. To use a specific jar, set the
OPENROCKET_JAR environment variable (or pass ``jar=`` directly):

    OPENROCKET_JAR=/path/to/OpenRocket-24.12.jar python custom_setup.py

Besides ``jar``, you can pass ``orhome`` (an OpenRocket installation folder), ``jvm`` (the
Java runtime library) and ``jvm_args`` (options for the JVM, for example ``-Xmx2g``).
"""
import logging
import os
import sys

import jpype

import orhelper

# orhelper logs through the standard `logging` module and does not configure it for you.
logging.basicConfig(level=logging.INFO)

try:
    instance = orhelper.OpenRocketInstance(
        jar=os.environ.get("OPENROCKET_JAR"),  # None means: use the installed OpenRocket
        jvm_args=["-Xmx1g"],  # limit the Java heap to 1 GB
        log_level="ERROR",  # log level of OpenRocket itself: "ERROR" hides its warnings
    )
except (orhelper.OpenRocketNotFoundError, orhelper.JVMNotFoundError) as error:
    sys.exit(f"Could not start OpenRocket: {error}")

with instance:
    java = jpype.java.lang
    print(f"Java version: {java.System.getProperty('java.version')}")
    print(f"Java heap limit: {java.Runtime.getRuntime().maxMemory() // 2 ** 20} MB")

    orh = orhelper.Helper(instance)
    doc = orh.load_doc(orhelper.sample_ork_path())
    print(f"Loaded rocket '{doc.getRocket().getName()}' with {doc.getSimulationCount()} simulation(s)")
