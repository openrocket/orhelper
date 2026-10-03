"""Make the examples run against a chosen jar in a headless, isolated JVM (used by test_examples.py).

Python imports this module automatically at start-up of every process that has this folder on
PYTHONPATH, including the worker processes of examples that use multiprocessing. It wraps
``OpenRocketInstance`` so the examples, which normally find the installed OpenRocket, use the jar in
ORHELPER_EXAMPLE_JAR and keep their Java preferences in ORHELPER_EXAMPLE_HOME.
"""
import os

jar = os.environ.get("ORHELPER_EXAMPLE_JAR")
home = os.environ.get("ORHELPER_EXAMPLE_HOME")

if jar and home:
    import jpype

    import orhelper

    _original_init = orhelper.OpenRocketInstance.__init__

    def _init(self, *args, **kwargs):
        if not args and kwargs.get("jar") is None:
            kwargs["jar"] = jar
        if kwargs.get("jvm") is None:
            kwargs["jvm"] = jpype.getDefaultJVMPath()
        kwargs["jvm_args"] = list(kwargs.get("jvm_args") or []) + [
            "-Djava.awt.headless=true",
            f"-Duser.home={home}",
            f"-Djava.util.prefs.userRoot={home}",
        ]
        _original_init(self, *args, **kwargs)

    orhelper.OpenRocketInstance.__init__ = _init
