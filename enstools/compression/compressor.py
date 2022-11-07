"""
#
# Functions to compress netcdf/grib files from the command line.
#

"""
import logging
import time
from functools import partial
from os import rename, access, W_OK
from os.path import isfile, isdir
from typing import Union, List
import xarray
from pathlib import Path
from enstools.io.paths import clean_paths

from enstools.compression.emulation import emulate_compression_on_dataset


def drop_variables(dataset: xarray.Dataset, variables_to_keep: List[str]) -> xarray.Dataset:
    """
    Drop all the variables that are not in list variables_to_keep.
    Keeps the coordinates.
    """
    # Drop the undesired variables and keep the coordinates
    coordinates = [v for v in dataset.coords]
    variables = [v for v in dataset.variables if v not in coordinates]
    variables_to_drop = [v for v in variables if v not in variables_to_keep]
    return dataset.drop_vars(variables_to_drop)


def fix_filename(file_name: str) -> str:
    cases = [".grib2", ".grb"]
    for case in cases:
        file_name = file_name.replace(case, ".nc")
    return file_name


def transfer(file_paths: Union[List[str], str, Path, List[Path]],
             output: Path,
             compression: str = "lossless",
             variables_to_keep: List[str] = [],
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

    from dask.diagnostics import ProgressBar

    use_progress_bar = False

    if use_progress_bar:
        p = ProgressBar()
        p.register()

    # If we have a single file, we might accept a output filename instead of an output folder.
    # Some assertions first to prevent wrong usage.
    if len(file_paths) == 0:
        raise AssertionError("file_paths can't be an empty list")
    elif len(file_paths) == 1:
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
    if use_progress_bar:
        p.unregister()


def transfer_multiple_files(
        file_paths: List[Path],
        output: Path,
        compression: str = "lossless",
        variables_to_keep: List[str] = None,
        emulate: bool = False,
        fill_na: Union[float, bool] = False
) -> None:
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
    from enstools.io import read, write
    dataset = read(origin, decode_times=False)
    if variables_to_keep is not None:
        dataset = drop_variables(dataset, variables_to_keep)

    # If we don't chunk the dataset before writing, it might try to operate with the full array leading to
    # memory issues
    chunks = {k: v if k != "time" else 1 for k, v in dataset.chunksizes.items()}
    dataset = dataset.chunk(chunks)

    if fill_na is not False:
        dataset = dataset.fillna(fill_na)
        logging.info(f"Filling missing values with {fill_na!r}")
    # In case we are using emulate, we compress and decompress the dataset using LibPressio and output
    # the file without compression only to measure the impact compression would have.
    if emulate:
        dataset, _ = emulate_compression_on_dataset(dataset, compression)
        return write(dataset, destination, file_format="NC", compute=compute, compression=None,
                     format="NETCDF4_CLASSIC", engine="netcdf4")
    else:
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
    from os.path import join, basename, splitext
    from enstools.io.file_type import get_file_type

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
    Copies a list of files to a destination folder, optionally applying compression.
    """
    file_paths = clean_paths(file_paths)
    output = Path(output)
    # In case of using automatic compression option, call here get_compression_parameters()
    if compression == "auto":
        from .analyzer import analyze_files
        if output.is_dir():
            compression_parameters_path = output / "compression_parameters.yaml"
        else:
            compression_parameters_path = output.parent.resolve() / "compression_parameters.yaml"
        # By using thresholds = None we will be using the default values.
        analyze_files(file_paths=file_paths,output_file=compression_parameters_path)
        # Now lets continue setting compression = compression_parameters_path
        compression = compression_parameters_path

    # In case of wanting to use additional nodes
    if nodes > 0:
        from enstools.core import init_cluster
        from dask.distributed import performance_report
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


def check_compression_ratios(file_paths: Union[List[str], str], output: str):
    # Compute compression ratios
    from .size_metrics import compression_ratio
    from os.path import join, basename
    from pprint import pprint
    compression_ratios = {}

    # Single file case
    if isinstance(file_paths, str):
        file_path = file_paths
        if isdir(output):
            file_name = basename(file_path)
            new_file_path = join(output, file_name)
        elif isfile(output):
            new_file_path = output
        else:
            raise NotImplementedError
        CR = compression_ratio(file_path, new_file_path)
        print(f"Compression ratios after compression:\nCR: {CR:.1f}")
        return

    # Multiple files
    for file_path in file_paths:
        file_name = basename(file_path)
        file_name = fix_filename(file_name)
        new_file_path = join(output, file_name)
        if isfile(new_file_path):
            CR = compression_ratio(file_path, new_file_path)
            compression_ratios[basename(file_path)] = CR
    print("Compression ratios after compression:")
    pprint(compression_ratios)
