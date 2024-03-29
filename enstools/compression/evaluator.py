"""
#
# Functions to evaluate differences in netcdf/grib files that should represent the same data.
#

"""
import warnings as _warnings

from enstools.compression.metrics import DataArrayMetrics, DatasetMetrics

# Some hardcoded ASCII characters to format the output
HEADER = '\033[95m'
OKBLUE = '\033[94m'
OKCYAN = '\033[96m'
OKGREEN = '\033[92m'
WARNING = '\033[93m'
FAIL = '\033[91m'
ENDC = '\033[0m'
BOLD = '\033[1m'
UNDERLINE = '\033[4m'
V_CHAR = '\u2713'


def print_green(text: str):
    """Prints the given text in green color.

    Args:
        text (str): The text to be printed in green color.
    """
    print(f"{OKGREEN}{text}{ENDC}")


def print_red(text: str):
    """Prints the given text in red color.

    Args:
        text (str): The text to be printed in red color.
    """
    print(f"{FAIL}{text}{ENDC}")


def evaluate(reference_path: str, target_path: str, plot: bool = False, create_gradients: bool = False):
    """
    The purpose of this routine is to obtain some metrics and plots on how similar are two datasets.
    """

    file_comparison = DatasetMetrics(reference_path, target_path)

    if create_gradients:
        # Compute gradients and add it as new variables
        file_comparison.create_gradients()
        # Compute second order gradients and add it as new variables
        file_comparison.create_second_order_gradients()

    # Get list of variables
    variables = file_comparison.variables

    # As a tentative idea, we can rise some warnings in case some metrics are below certain thresholds:
    # These thresholds could be:
    #   ssim_I < 3
    #   correlation_I < 4
    #   nrmse_I < 2

    def checks(metrics: DataArrayMetrics):

        thresholds = {
            "ssim_I": 3,
            "correlation_I": 4,
            "nrmse_I": 2,
            # "max_rel_diff": 10000000,
            "ks_I": 2,
        }
        for key, value in thresholds.items():
            with _warnings.catch_warnings():
                _warnings.simplefilter("ignore")
                if any(metrics[key] < value):
                    yield f"{BOLD}{key}{ENDC} index is low: {metrics[key].max().values:.1f}."

    warnings = {}
    for variable in variables:
        warnings[variable] = list(checks(file_comparison[variable]))

    for variable in variables:
        if warnings[variable]:
            print_red(f"{variable} X")
            for warning in warnings[variable]:
                print(f"\t{warning}")
        else:
            print_green(f"{variable} {V_CHAR}")

    print("\nSUMMARY:")
    num_variables_with_warnings = sum(1 if len(warnings[v]) > 0 else 0 for v in variables)
    if not num_variables_with_warnings:
        print_green("Any variable has warnings!")
    else:
        print(f"{num_variables_with_warnings}/{len(variables)}  variables have warnings.\n\n")

    # Produce visual reports
    if plot:
        file_comparison.make_plots()
