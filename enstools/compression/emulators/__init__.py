"""
Import the different implementations of the Emulator abstract class to make them accessible.
"""

from .zfp_emulator import ZFPEmulator
from .filters_emulator import FilterEmulator
from .libpressio_emulator import LibpressioEmulator

# Define the default emulator
DefaultEmulator = FilterEmulator
