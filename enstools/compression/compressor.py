"""
#
# Functions to compress netcdf/grib files from the command line.
#

"""
import logging
from os import rename, access, W_OK
from os.path import isdir
from os.path import splitext
from pathlib import Path
from pprint import pprint
from typing import Union, List

import xarray
from dask.distributed import performance_report

from enstools.compression.emulation import emulate_compression_on_dataset
from enstools.core import init_cluster
from enstools.io import read, write
from enstools.io.file_type import get_file_type
from enstools.io.paths import clean_paths
from .size_metrics import compression_ratio


def drop_variables(dataset: xarray.Dataset, variables_to_keep: List[str]) -> xarray.Dataset:
    """
    Drop all the variables that are not in list variables_to_keep.
    Keeps the coordinates.
    """
    # Drop the undesired variables and keep the coordinates
    coordinates = list(dataset.coords)
    variables = [v for v in dataset.variables if v not in coordinates]
    variables_to_drop = [v for v in variables if v not in variables_to_keep]
    return dataset.drop_vars(variables_to_drop)


def fix_filename(file_name: str) -> str:
    """
    Replace grib2 or grb file specification with .nc
    Parameters
    ----------
    file_name

    Returns
    -------
    fixed_file_name

    """
    cases = [".grib2", ".grb"]
    for case in cases:
        file_name = file_name.replace(case, ".nc")
    return file_name


def transfer(file_paths: Union[List[str], str, Path, List[Path]],
             output: Path,
             compression: str = "lossless",
             variables_to_keep: List[str] = None,
             emulate: bool = False,
             fill_na: Union[float, bool] = False,
             ) -> None:
    """
    This function loops through a list of files creating delayed dask tasks to copy each one of the files while
    optionally using compression.
    If there are dask workers available the tasks will be automatically distributed when using compute.

    Parameters:
    -----------

    file_paths: string or list of strings
                File-path or list of file-paths of all the files that will be copied.
    output_folder: string
                Path to the destination folder
    compression: string
                Compression specification or path to json configuration file.
    variables_to_keep: list of strings
                In case of only wanting to keep certain variables, pass the variables to keep as a list of strings.
    """
    file_paths = clean_paths(file_paths)
    # Just make sure that output is a Path object
    output = Path(output).resolve()

    # If we have a single file, we might accept a output filename instead of an output folder.
    # Some assertions first to prevent wrong usage.
    if len(file_paths) == 0:
        raise AssertionError("file_paths can't be an empty list")

    if len(file_paths) == 1:
        file_path = file_paths[0]
        new_file_path = destination_path(file_path, output) if isdir(output) else output
        transfer_file(file_path, new_file_path, compression,
                      variables_to_keep, emulate=emulate, fill_na=fill_na)
    elif len(file_paths) > 1:
        # In case of having more than one file, check that output corresponds to a directory
        assert output.is_dir(), "For multiple files, the output parameter should be a directory"
        assert access(
            output, W_OK), "The output folder provided does not have write permissions"

        transfer_multiple_files(
            file_paths=file_paths,
            output=output,
            compression=compression,
            variables_to_keep=variables_to_keep,
            emulate=emulate,
            fill_na=fill_na,
        )


def transfer_multiple_files(
        file_paths: List[Path],
        output: Path,
        compression: str = "lossless",
        variables_to_keep: List[str] = None,
        emulate: bool = False,
        fill_na: Union[float, bool] = False
) -> None:
    """
        This function will copy multiple files while optionally applying compression.

    Parameters
    ----------
    file_paths
    output
    compression
    variables_to_keep
    emulate
    fill_na

    Returns
    -------

    """
    # pylint: disable=import-outside-toplevel

    output = Path(output)
    file_paths = clean_paths(paths=file_paths)

    from dask import compute
    # Create and fill the list of tasks
    tasks = []

    # In order to give the files a temporary filename we will use a dictionary to keep the old and new names
    temporary_names_dictionary = {}

    for file_path in file_paths:
        new_file_path = destination_path(file_path, output)

        # Create temporary file name and store it in the dictionary
        temporary_file_path = Path(f"{new_file_path}.tmp")
        temporary_names_dictionary[temporary_file_path] = new_file_path

        # Create task:
        # The transfer file function returns a write task which hasn't been computed.
        # It is not necessary anymore to use the delayed function.
        task = transfer_file(file_path,
                             temporary_file_path,
                             compression,
                             variables_to_keep,
                             compute=False,
                             emulate=emulate,
                             fill_na=fill_na,
                             )
        # Add task to the list
        tasks.append(task)

    # Compute all the tasks
    compute(tasks)

    # Rename files
    for temporary_name, final_name in temporary_names_dictionary.items():
        rename(temporary_name, final_name)


def transfer_file(origin: Path, destination: Path, compression: str, variables_to_keep: List[str] = None,
                  compute: bool = True, emulate=False, fill_na: Union[float, bool] = False):
    """
    This function will copy a dataset while optionally applying compression.

    Parameters:
    ----------
    origin: string
            path to original file that will be copied.

    destination: string
            path to the new file that will be created.

    compression: string
            compression specification or path to json configuration file
    """

    dataset = read(origin, decode_times=False)
    if variables_to_keep is not None:
        dataset = drop_variables(dataset, variables_to_keep)

    if fill_na is not False:
        dataset = dataset.fillna(fill_na)
        logging.info("Filling missing values with %s", fill_na)

    # In case we are using emulate, we compress and decompress the dataset using LibPressio and output
    # the file without compression only to measure the impact compression would have.
    if emulate:
        dataset, _ = emulate_compression_on_dataset(dataset, compression)
        return write(dataset, destination, file_format="NC", compute=compute, compression=None,
                     format="NETCDF4_CLASSIC", engine="netcdf4")

    return write(dataset, destination, file_format="NC", compression=compression, compute=compute)


def destination_path(origin_path: Path, destination_folder: Path):
    """
    Function to obtain the destination file from the source file and the destination folder.
    If the source file has GRIB format (.grb) , it will be changed to netCDF (.nc).

    Parameters
    ----------
    origin_path : string
            path to the original file

    destination_folder : string
            path to the destination folder

    Returns the path to the new file that will be placed in the destination folder.
    """

    file_name = origin_path.name

    file_format = get_file_type(file_name, only_extension=True)
    if file_format != "NC":
        bname, _ = splitext(file_name)
        file_name = bname + ".nc"
    destination = destination_folder / file_name
    return destination


def compress(
        file_paths: List[Path],
        output: Path,
        compression: Union[str, dict, None],
        nodes: int = 0,
        variables_to_keep: Union[List[str], None] = None,
        show_compression_ratios=False,
        emulate=False,
        fill_na: Union[float, bool] = False,
) -> None:
    """
    Copies a list of files to the destination applying compression.

    Parameters
    ----------
    file_paths:
    a path or a list of paths. Can be strings or proper paths (pathlib.Path)
    output:
    destination folder
    compression:
    string following the Compression Specification Format or dictionary with different entries for different variables.
    nodes:
    can be used to parallelize compression using a slurm cluster.
    variables_to_keep:
    list of variables to keep
    show_compression_ratios:
    to activate printing of compression ratios
    emulate: bool
    if True, the files are compressed and uncompressed, so the effects of the compression are present but the files
    are not actually compressed. Useful for testing with software that is not hdf5 capable.
    fill_na: float or False
    Fill the NaN values with a float value

    Returns
    -------

    """
    file_paths = clean_paths(file_paths)
    output = Path(output)
    # In case of wanting to use additional nodes
    if nodes > 0:
        with init_cluster(nodes, extend=True) as client:
            client.wait_for_workers(nodes)
            client.get_versions(check=True)
            with performance_report(filename="dask-report.html"):
                # Transfer will copy the files from its origin path to the output folder,
                # using read and write functions from enstools
                transfer(file_paths,
                         output,
                         compression,
                         variables_to_keep=variables_to_keep,
                         emulate=emulate,
                         fill_na=fill_na,
                         )

    else:
        # Transfer will copy the files from its origin path to the output folder,
        # using read and write functions from enstools
        transfer(file_paths, output, compression,
                 variables_to_keep=variables_to_keep, emulate=emulate, fill_na=fill_na)

    if show_compression_ratios:
        check_compression_ratios(file_paths, output)


def check_compression_ratios(file_paths: List[Path], output: Path) -> None:
    """
    Utility to compute and print the compression ratios.
    Parameters
    ----------
    file_paths
    output

    Returns
    -------

    """
    # Compute compression ratios
    compression_ratios = {}

    for file_path in file_paths:
        file_name = file_path.name
        file_name = fix_filename(file_name)
        if output.is_dir():
            new_file_path = output / file_name
        elif output.is_file():
            new_file_path = output
        else:
            raise AssertionError(f"Output {output} is neither a file nor a folder!")
        file_compression_ratio = compression_ratio(file_path.as_posix(), new_file_path.as_posix())
        compression_ratios[file_name] = file_compression_ratio
    print("Compression ratios after compression:")
    pprint(compression_ratios)
