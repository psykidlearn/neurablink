import os
import sys
import subprocess
import platform


def find_mediapipe_path(base_path):
    """
    Search for the mediapipe directory within the given base path.
    """
    for root, dirs, files in os.walk(base_path):
        if 'mediapipe' in dirs:
            return os.path.join(root, 'mediapipe')
    raise FileNotFoundError("Mediapipe directory not found in the specified path.")

def build_application():
    # Determine the base directory of the project
    base_dir = os.path.dirname(os.path.abspath(__file__))

    # Define the paths relative to the base directory
    exec_icon = os.path.join(base_dir, "assets", "icon.ico")
    assets_icon = os.path.join(base_dir, "assets", "icon.png")
    assets_landmarks = os.path.join(base_dir, "assets", "default_landmarks.pkl")
    configs_dir = os.path.join(base_dir, "configs")

    # Define the base path for the neurablink environment
    neurablink_env_path = sys.prefix

    # Find the mediapipe path within the neurablink environment
    mediapipe_path = find_mediapipe_path(neurablink_env_path)

    # Determine the operating system
    current_os = platform.system()

    # Construct the pyinstaller command based on the OS
    if current_os == "Windows":
        command = [
            "pyinstaller",
            "--onefile",
            "--noconsole",
            "--name=Neurablink",
            f"--icon={exec_icon}",  # Use .ico for Windows
            #"--clean", # To avoid caching issues
            f"--add-data={assets_icon};assets",
            f"--add-data={assets_landmarks};assets",
            f"--add-data={configs_dir};configs",
            f"--add-data={mediapipe_path};mediapipe",
            os.path.join(base_dir, "src", "dist.py")
        ]
    elif current_os == "Linux":
        command = [
            "pyinstaller",
            "--onefile",
            "--noconsole",
            "--name=Neurablink",
            #"--clean", # To avoid caching issues
            f"--add-data={assets_icon}:assets",
            f"--add-data={assets_landmarks}:assets",
            f"--add-data={configs_dir}:configs",
            f"--add-data={mediapipe_path}:mediapipe",
            os.path.join(base_dir, "src", "dist.py")
        ]
        # Note: Linux does not use the --icon option in the same way
    else:
        raise OSError("Unsupported operating system")
    # Run the command
    subprocess.run(command, check=True)

if __name__ == "__main__":
    build_application()