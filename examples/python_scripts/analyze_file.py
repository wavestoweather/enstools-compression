#!/usr/bin/env python3

# Imports
import xarray
from pathlib import Path
from enstools.compression.analyzer import analyze_files

# Define path for temporary file
file_path = Path("tmp.nc")

# Download tutorial data and save it to a file
dataset_name = "air_temperature"
dataset = xarray.tutorial.open_dataset(dataset_name)
dataset.to_netcdf(file_path)

# Analyze file with default constrains (correlation_I:5,ssim_I:2)
encoding, metrics = analyze_files(file_path)
print("Default:")
print(encoding)
print(metrics)

# Analyze file using custom constrains
constrains = "correlation_I:3,ssim_I:1"
encoding, metrics = analyze_files(file_path, constrains=constrains)
print("Custom constrains:")
print(encoding)
print(metrics)

# Remove temporary file
if file_path.exists():
    file_path.unlink()
