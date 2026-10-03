"""Run every script in examples/ against a real OpenRocket jar to make sure they keep working.

Skipped unless OPENROCKET_JAR is set. Each example runs in its own process (the JVM can only start once
per process) with a headless JVM and isolated Java preferences; see example_env/sitecustomize.py.
"""
import importlib.util
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = sorted((ROOT / "examples").glob("*.py"))

# Third-party packages (besides numpy and jpype) that examples need.
REQUIREMENTS = {
    "simple_plot.py": ["matplotlib"],
    "lazy.py": ["matplotlib", "scipy"],
}


@unittest.skipUnless(os.environ.get("OPENROCKET_JAR"), "set OPENROCKET_JAR to run the examples")
class ExampleTests(unittest.TestCase):
    def test_examples_were_found(self):
        self.assertGreaterEqual(len(EXAMPLES), 8)

    def run_example(self, path):
        missing = [name for name in REQUIREMENTS.get(path.name, []) if importlib.util.find_spec(name) is None]
        if missing:
            self.skipTest(f"needs {', '.join(missing)}")
        with tempfile.TemporaryDirectory(prefix="orhelper-examples-") as home:
            env = dict(
                os.environ,
                ORHELPER_EXAMPLE_JAR=str(Path(os.environ["OPENROCKET_JAR"]).resolve()),
                ORHELPER_EXAMPLE_HOME=home,
                OPENROCKET_JAR=str(Path(os.environ["OPENROCKET_JAR"]).resolve()),
                MPLBACKEND="Agg",  # never open plot windows
                PYTHONPATH=os.pathsep.join([str(Path(__file__).with_name("example_env")), str(ROOT),
                                            os.environ.get("PYTHONPATH", "")]),
            )
            result = subprocess.run([sys.executable, str(path)], cwd=home, env=env, capture_output=True,
                                    text=True, timeout=600)
        self.assertEqual(result.returncode, 0, f"{path.name} failed:\n{result.stdout}\n{result.stderr}")


def _add_test(path):
    def test(self):
        self.run_example(path)
    test.__name__ = f"test_{path.stem}"
    setattr(ExampleTests, test.__name__, test)


for _path in EXAMPLES:
    _add_test(_path)


if __name__ == "__main__":
    unittest.main()
