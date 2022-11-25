#!/usr/bin/env python3

# Imports
import xarray
from pathlib import Path
from enstools.compression.analyzer.analyzer import analyze_dataset
from enstools.io import write

# Getting some dummy data
dataset_name = "air_temperature"
dataset = xarray.tutorial.open_dataset(dataset_name)

# Find optimal encoding using default constrains
encoding, metrics = analyze_dataset(dataset)

# Define a path for the temporary file
file_path = Path("tmp.nc")

# Write compressed file using encoding from the analysis
write(dataset, file_path, compression=encoding)

# Remove temporary file
if file_path.exists():
    file_path.unlink()
