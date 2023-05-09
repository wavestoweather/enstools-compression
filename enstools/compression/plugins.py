import sys


def load_plugins() -> None:
    """

    Function to print the instructions to set the environment variable HDF5_PLUGIN_PATH.

    """

    import hdf5plugin
    from pathlib import Path
    hdf5plugin_folder = Path(hdf5plugin.__file__).parent
    plugins_folder = hdf5plugin_folder / "plugins"

    load_plugins_comment = """
# You can just execute this command within $() -> $(enstools-compression load-plugins)
# or just execute the following line in your terminal:
"""
    print(load_plugins_comment, file=sys.stderr)
    print(f"export HDF5_PLUGIN_PATH={plugins_folder.as_posix()}")


def unload_plugins():
    unload_plugins_comment = """
# You can just execute this command within $() -> $(enstools-compression unload-plugins)
# or just execute the following line in your terminal:
"""
    print(unload_plugins_comment, file=sys.stderr)
    print("unset HDF5_PLUGIN_PATH")
