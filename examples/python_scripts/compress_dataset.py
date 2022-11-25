#!/usr/bin/env python3

# Imports
import xarray
from enstools.io import write

# Get some data
dataset = xarray.tutorial.open_dataset("air_temperature")

# Save the dataset into a compressed netCDF using SZ.
write(dataset, "output.nc", compression='lossy,sz,abs,0.1')
