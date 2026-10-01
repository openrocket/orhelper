from pathlib import Path

__all__ = ["sample_ork_path"]


def sample_ork_path() -> str:
    """Return the path of the sample rocket (``simple.ork``) bundled with orhelper.

    Handy for trying the library without a rocket file of your own::

        doc = helper.load_doc(orhelper.sample_ork_path())
    """
    return str(Path(__file__).resolve().parent / "data" / "simple.ork")
