"""
Alternative implementation of transfer_file which does not rely on xarray to copy the files.
(it is used to read some file information though.)

The main purpose of this implementation was to overcome the Memory limitations of the dask approach,
which required to load the full file in memory at the same time at the moment of writing it.
"""

from pathlib import Path
from typing import List

import h5netcdf
import xarray as xr

from enstools.encoding.api import DatasetEncoding
from .slicing import MultiDimensionalSliceCollection


def copy_global_attributes(source_file, destination_file):
    """
    Copy global attributes from the source file to the destination file.

    Parameters
    ----------
    source_file : h5netcdf.File
        The source file to copy attributes from.
    destination_file : h5netcdf.File
        The destination file to copy attributes to.
    """
    for attr in source_file.attrs:
        destination_file.attrs[attr] = source_file.attrs[attr]


def add_dimensions(source_file, destination_file):
    """
    Add dimensions from the source file to the destination file.

    Parameters
    ----------
    source_file : h5netcdf.File
        The source file to copy dimensions from.
    destination_file : h5netcdf.File
        The destination file to copy dimensions to.
    """
    for dimension_name in source_file.dimensions:
        dimension = source_file.dimensions[dimension_name]
        if not dimension.isunlimited():
            destination_file.dimensions[dimension.name] = dimension.size
        else:
            destination_file.dimensions[dimension.name] = None
            destination_file.resize_dimension(dimension.name, dimension.size)


def get_variables_to_copy(source_file, dataset, variables_to_keep):
    """
    Get the list of variables to copy, including data variables and coordinates with values.

    Parameters
    ----------
    source_file : h5netcdf.File
        The source file containing the variables.
    dataset : xarray.Dataset
        The xarray Dataset object.
    variables_to_keep : List[str]
        The list of variables to keep in the destination file.

    Returns
    -------
    List[str]
        The list of variables to copy.
    """
    return (variables_to_keep if variables_to_keep is not None else list(dataset.data_vars)) \
        + [v for v in source_file.variables if v in source_file.dimensions]


def copy_variable_attributes(source_var, destination_var):
    """
    Copy attributes from the source variable to the destination variable.

    Parameters
    ----------
    source_var : h5netcdf.Variable
        The source variable to copy attributes from.
    destination_var : h5netcdf.Variable
        The destination variable to copy attributes to.
    """
    for attr in source_var.attrs:
        destination_var.attrs[attr] = source_var.attrs[attr]


def transfer_file(origin: Path,
                  destination: Path,
                  compression: str,
                  variables_to_keep: List[str] = None,
                  parts=1,
                  **kwargs):
    """
    This function will copy a dataset while optionally applying compression using the hdf5netcdf backend without xarray.

    Parameters:
    ----------
    origin: string
            path to original file that will be copied.

    destination: string
            path to the new file that will be created.

    compression: string
            compression specification or path to json configuration file
    """
    if kwargs:
        print(f"The h5netcdf implementation of transfer_file ignores the following keyword arguments: {kwargs}")

    with xr.open_dataset(origin, engine="h5netcdf") as dataset:
        encoding = DatasetEncoding(dataset, compression=compression)

    with h5netcdf.File(origin, 'r') as source_file, h5netcdf.File(destination, 'w') as destination_file:
        copy_global_attributes(source_file, destination_file)
        add_dimensions(source_file, destination_file)

        variables_to_keep = get_variables_to_copy(source_file, dataset, variables_to_keep)

        for var_name in variables_to_keep:
            source_var = source_file[var_name]
            var_encoding = {**encoding[var_name]}

            if "chunksizes" in var_encoding:
                var_encoding["chunks"] = var_encoding.pop("chunksizes")

            destination_file.create_variable(name=var_name,
                                             dimensions=source_var.dimensions,
                                             dtype=source_var.dtype,
                                             **var_encoding,
                                             )

            destination_var = destination_file[var_name]

            multi_dimensional_slice = MultiDimensionalSliceCollection(shape=destination_var.shape,
                                                                      chunk_sizes=destination_var.chunks,
                                                                      )

            if len(multi_dimensional_slice) > 1:
                slices = [group.slice for group in multi_dimensional_slice.split(parts=parts)]
                for slc in slices:
                    destination_var[slc] = source_var[slc][()]
            else:
                destination_var[:] = source_var[()]

            copy_variable_attributes(source_var, destination_var)
