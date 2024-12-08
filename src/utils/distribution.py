import sys
import os


def bundled_path(relative_path):
    """Return the absolute path to a bundled resource or a regular path during development."""
    if hasattr(sys, '_MEIPASS'):
        # PyInstaller temporary unpack directory
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.abspath(relative_path)


def set_working_directory():
    """Set working directory to the PyInstaller temporary directory if running as a packaged executable."""
    if hasattr(sys, '_MEIPASS'):
        # Change working directory to the PyInstaller temporary directory
        os.chdir(sys._MEIPASS)

