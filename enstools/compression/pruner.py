import xarray
import numpy as np
import xarray

from .compressor import drop_variables
from .significant_bits import get_uint_type_by_bit_length, single_bit_mask, apply_mask, \
    mask_generator
from enstools.io.paths import clean_paths
from typing import Union, List
from pathlib import Path


def prune_numpy_array(array: np.ndarray, significant_bits=0, round_to_nearest=True):
    """
    Create and apply a mask with number of ones given by the input variable significant_bits.

    Rounding is controlled by round_to_nearest input variable.
    """

    bits = array.dtype.itemsize * 8
    int_type = get_uint_type_by_bit_length(bits)

    # round_to_nearest = True
    if round_to_nearest:
        # Get the mask for the first discarded value
        next_bit_mask = single_bit_mask(position=significant_bits, bits=bits)

        # Apply the mask
        next_bit_value = apply_mask(array, next_bit_mask)

        # Shift left
        next_bit_value = np.left_shift(next_bit_value.view(dtype=int_type), 1)

        # Apply or
        new_array = np.bitwise_or(array.view(dtype=int_type), next_bit_value).view(dtype=array.dtype)

        # Reasign
        array = new_array[:]

    # Create mask
    mask = mask_generator(bits=bits, ones=significant_bits)
    # Apply mask
    pruned = apply_mask(array, mask)
    assert len(pruned) == len(array)

    return pruned


def pruner(file_paths: Union[Path, List[Path], str, List[str]],
           output: Union[str, Path],
           significant_bit_info=None,
           variables_to_keep=None,
           ):
    """
    Apply bit prunning to a list of files.

    """
    from enstools.compression.compressor import destination_path
    from os.path import isdir
    from os import access, W_OK

    file_paths = clean_paths(file_paths)
    output = Path(output).resolve()

    # If we have a single file, we might accept a output filename instead of an output folder.
    # Some assertions first to prevent wrong usage.
    if len(file_paths) == 0:
        raise AssertionError("file_paths can't be an empty list")
    elif len(file_paths) == 1:
        file_path = file_paths[0]
        new_file_path = destination_path(file_path, output) if output.is_dir() else output
        prune_file(file_path, new_file_path, significant_bit_info=significant_bit_info,
                   variables_to_keep=variables_to_keep)
    elif len(file_paths) > 1:
        # In case of having more than one file, check that output corresponds to a directory
        assert isdir(output), "For multiple files, the output parameter should be a directory"
        assert access(output, W_OK), "The output folder provided does not have write permissions"
        for file_path in file_paths:
            new_file_path = destination_path(file_path, output)
            prune_file(file_path, new_file_path, significant_bit_info=significant_bit_info,
                       variables_to_keep=variables_to_keep)


def prune_file(file_path, destination, significant_bit_info=None, variables_to_keep=None):
    """
    Apply bit pruning to a file. 
    """
    from enstools.io import read, write
    print(f"{file_path} -> {destination}")
    dataset = read(file_path)

    if variables_to_keep is not None:
        dataset = drop_variables(dataset, variables_to_keep)

    if significant_bit_info is None:
        from enstools.compression.significant_bits import analyze_file_significant_bits
        significant_bits_dictionary = analyze_file_significant_bits(file_path)
    else:
        significant_bits_dictionary = significant_bit_info
    print(significant_bits_dictionary)
    prune_dataset(dataset, significant_bits_dictionary)

    # After pruning the file we save it to the new destination.
    write(dataset, destination, compression="lossless")


def prune_dataset(dataset: xarray.Dataset, significant_bits_dictionary: dict):
    """
    Apply bit pruning to a dataset.
    """
    variables = [v for v in dataset.variables if v not in dataset.coords]

    for variable in variables:
        if variable not in significant_bits_dictionary:
            print(f"Warning: number of significant bits for variable {variable} has not been provided.")
            continue
        significant_bits = significant_bits_dictionary[variable]
        prune_data_array(dataset[variable], significant_bits)


def prune_data_array(data_array: xarray.DataArray, significant_bits: int):
    """
    Apply pruning to a Data Array.
    """
    data_array.values = prune_numpy_array(data_array.values, significant_bits=significant_bits)
