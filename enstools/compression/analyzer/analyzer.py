"""
    #
    # Routines to find optimal compression parameters to satisfy certain quality thresholds
    #

"""
import logging
from pathlib import Path
from typing import Union, List, Tuple, Dict

import numpy as np
import xarray

from .AnalysisOptions import AnalysisOptions, AnalysisParameters
from .analyze_data_array import analyze_data_array, ANALYSIS_DIAGNOSTIC_METRICS, COMPRESSION_RATIO_LABEL
from enstools.compression.compressor import drop_variables


def find_optimal_encoding(dataset: xarray.Dataset, options: AnalysisOptions):
    """
    Given a dataset, find the optimal compression parameters.

    Once the metrics from the different compression options are collected, find the best according to the mode:
    - If the target was to achieve a compression_ratio, the goal will be to maximise quality metrics.
    - If the target are certain quality metrics, the goal will be to maximise the compression ratio.
    :param dataset:
    :param options:
    :return:
    """
    encodings, metrics = find_encodings_for_all_combinations(dataset, options)
    return select_optimal_encoding(encodings, metrics, options)


def select_optimal_encoding(encodings: dict, metrics: dict, options: AnalysisOptions) -> Tuple[Dict, Dict]:
    """
    This function will select between finding the best compression ratio or the best quality depending on the
    analysis options provided.
    If we are aiming at a certain compression ratio, all the encodings and metrics provided to this function
    should have values close to this compression ratio. So we will select the best within them based on
    quality metrics.
    If we are aiming for quality instead of compression ratio the same reasoning applies:
    all the provided encodings should satisfy the quality requirements, so the best one will be the one
    with the highest compression ratio.
    """

    if COMPRESSION_RATIO_LABEL in options.thresholds:
        return select_optimal_encoding_based_on_quality_metrics(encodings, metrics)
    else:
        return select_optimal_encoding_based_on_compression_ratio(encodings, metrics)


def select_optimal_encoding_based_on_compression_ratio(encodings: dict, metrics: dict) -> Tuple[Dict, Dict]:
    """
    Within the encodings provided, the one with higher compression ratio is selected.
    """
    # Unpack keys
    combinations = [*encodings]
    variables = [*encodings[combinations[0]]]

    best_combination = {}
    for variable in variables:
        best_compression_ratio = 0
        for combination in combinations:
            if metrics[combination][variable][COMPRESSION_RATIO_LABEL] > best_compression_ratio:
                best_compression_ratio = metrics[combination][variable][COMPRESSION_RATIO_LABEL]
                best_combination[variable] = combination

    selected_encodings = {variable: encodings[combination][variable] for variable, combination in
                          best_combination.items()}
    selected_metrics = {variable: metrics[combination][variable] for variable, combination in
                        best_combination.items()}
    return selected_encodings, selected_metrics


def select_optimal_encoding_based_on_quality_metrics(encodings: dict, metrics: dict) -> Tuple[Dict, Dict]:
    """
    Within the encodings provided, the one with higher quality metrics is selected.
    """

    # Unpack keys
    combinations = [*encodings]
    variables = [*encodings[combinations[0]]]

    best_combination = {}

    for variable in variables:
        best_metrics = {met: -1.0 for met in ANALYSIS_DIAGNOSTIC_METRICS}
        for combination in combinations:
            for metric in ANALYSIS_DIAGNOSTIC_METRICS:
                if metric in metrics[combination][variable]:
                    if metrics[combination][variable][metric] > best_metrics[metric]:
                        best_metrics[metric] = metrics[combination][variable][metric]
                        best_combination[variable] = combination
    selected_encodings = {variable: encodings[combination][variable] for variable, combination in
                          best_combination.items()}
    selected_metrics = {variable: metrics[combination][variable] for variable, combination in
                        best_combination.items()}
    return selected_encodings, selected_metrics


def find_encodings_for_all_combinations(dataset: xarray.Dataset, options: AnalysisOptions):
    """
    Given a dataset and certain analysis options, find the compression parameters that fulfill the requirements for each
    combination of compressor and mode..
    :param dataset:
    :param options:
    :return:
    """
    # Get list of variables and coordinates
    variables = [v for v in dataset.data_vars]
    coordinates = [v for v in dataset.coords]

    compression_parameters = AnalysisParameters(options)

    # Get all possible combinations to analyze
    combinations = compression_parameters.get_compressor_mode_combinations()

    # Initialize dictionaries to save the results
    encodings = {}
    metrics = {}
    for combination in combinations:
        compressor, mode = combinations[combination]
        # Find optimal encoding
        combination_encoding = {}
        combination_metrics = {}
        for var in variables:
            # Coordinates will be losslessly compressed
            if var in coordinates:
                combination_encoding[var] = "lossless"
                combination_metrics[var] = {COMPRESSION_RATIO_LABEL: 1.0}
                continue
            # Small arrays will be losslessly compressed.
            # This number is arbitrary, a better based quantity is welcome.
            if dataset[var].size < 10000:
                combination_encoding[var] = "lossless"
                combination_metrics[var] = {COMPRESSION_RATIO_LABEL: 1.0}
                continue
            if not np.issubdtype(dataset[var].dtype, np.floating):
                logging.debug(
                    f"Variable {var} is not a float, it is {dataset[var].dtype}. Going with lossless.")
                combination_encoding[var] = "lossless"
                combination_metrics[var] = {COMPRESSION_RATIO_LABEL: 1.0}
                continue

            variable_encoding, variable_metrics = analyze_data_array(
                data_array=dataset[var],
                options=AnalysisOptions(compressor, mode, thresholds=options.thresholds)
            )
            combination_encoding[var] = variable_encoding
            combination_metrics[var] = variable_metrics
            # (dataset, variable_name, thresholds, compressor_name, mode)
            logging.info(f"{var} {variable_encoding}  CR:{variable_metrics[COMPRESSION_RATIO_LABEL]:.1f}")
        encodings[combination] = combination_encoding
        metrics[combination] = combination_metrics

    return encodings, metrics


def analyze_files(file_paths: List[Path],
                  output_file: Path = None,
                  constrains: str = "correlation_I:5,ssim_I:2",
                  file_format: str = "yaml",
                  compressor: str = None,
                  mode: str = None,
                  grid: str = None,
                  fill_na: Union[float, bool] = False,
                  variables: List = None,
                  ):
    """
    Finds optimal compression parameters for a list of files to fulfill certain thresholds.
    If an output_file argument is provided it will output the dictionary in there (yaml or json allowed).

    :param file_paths:
    :param output_file:
    :param constrains:
    :param file_format:
    :param compressor:
    :param mode:
    :param grid:
    :param fill_na:
    :param variables:
    :return:
    """

    print(
        f"\nAnalyzing files to determine optimal compression options for compressor {compressor!r} "
        f"with mode {mode!r} to fulfill the following constrains:\n"
        f"{constrains}\n"
    )
    print()
    from enstools.io import read

    # Load dataset, possibly using a grid file
    if grid:
        dataset = read(file_paths, constant=grid)
    else:
        dataset = read(file_paths)

    encoding, metrics = analyze_dataset(dataset=dataset,
                                        constrains=constrains,
                                        compressor=compressor,
                                        mode=mode,
                                        fill_na=fill_na,
                                        variables=variables,
                                        )

    save_encoding(encoding, output_file, file_format)

    return encoding, metrics


def analyze_dataset(dataset: xarray.Dataset,
                    constrains: str = "correlation_I:5,ssim_I:2",
                    compressor: str = None,
                    mode: str = None,
                    fill_na: Union[float, bool] = False,
                    variables: List = None,
                    ):
    if variables is not None:
        dataset = drop_variables(dataset, variables)

    if fill_na is not False:
        dataset = dataset.fillna(fill_na)

    options = AnalysisOptions(compressor=compressor, mode=mode, constrains=constrains)
    return find_optimal_encoding(dataset, options)


def save_encoding(encoding: dict, output_file: Union[Path, str, None] = None, file_format: str = "yaml"):
    """
    Output the encoding dictionary to a file or to the stdout.
    :param encoding:
    :param output_file:
    :param file_format:
    :return:
    """
    if file_format == "json":
        import json
        if output_file:
            print("Compression options saved in: %s " % output_file)
            with open(output_file, "w") as outfile:
                json.dump(encoding, outfile, indent=4, sort_keys=True)
        else:
            print("Compression options:")
            print(json.dumps(encoding, indent=4, sort_keys=True))
    elif file_format == "yaml":
        import yaml
        if output_file:
            output_file = Path(output_file)
            print("Compression options saved in: %s " % output_file)
            with open(output_file, "w") as outfile:
                yaml.dump(encoding, outfile, sort_keys=True)
        else:
            print("Compression options:")
            print(yaml.dump(encoding, indent=4, sort_keys=True))

    return encoding
