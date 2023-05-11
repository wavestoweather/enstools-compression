"""
Module containing AnalysisOptions and AnalysisParameters classes.
"""
from dataclasses import dataclass
from typing import Union

from enstools.core.errors import EnstoolsError
from enstools.encoding.api import lossy_compressors_and_modes


@dataclass
class AnalysisOptions:
    """
    A class representing analysis options, including compressor, mode,
    constraints, and thresholds.
    """
    compressor: str
    mode: str
    constrains: str
    thresholds: dict

    def __init__(self,
                 compressor: Union[str, None],
                 mode: Union[str, None],
                 constrains: Union[None, str] = None,
                 thresholds: Union[None, dict] = None,
                 ):
        self.compressor = str(compressor)

        self.mode = str(mode)

        if constrains and not thresholds:
            self.constrains = constrains
            self.thresholds = from_csv_to_dict(constrains)
        elif not constrains and thresholds:
            self.constrains = from_dict_to_csv(thresholds)
            self.thresholds = thresholds
        else:
            raise AssertionError("Only one of the two arguments should be provided.")


@dataclass
class AnalysisParameters:
    """
    A class representing analysis parameters, including the AnalysisOptions instance.
    """
    options: AnalysisOptions

    def __post_init__(self):
        # If mode is not None, compressor also shouldn't be None
        if self.options.mode is not None and self.options.compressor is None:
            raise EnstoolsError(f"Compression mode is assigned to {self.options.mode} but no compressor is specified.")
        self.multi_mode = self.options.mode in [None, "None", "all"]

    @property
    def compressors(self):
        """
        Get the list of compressors to be used based on the AnalysisOptions instance.

        :return: A list of compressor names. If the option is "None" or "all",
                 it returns all available compressors from the `lossy_compressors_and_modes` dictionary.
                 Otherwise, it returns a list containing a single compressor specified in the options.
        """
        if self.options.compressor in ["None", "all"]:
            return list(lossy_compressors_and_modes)

        return [self.options.compressor]

    def get_compressor_mode_combinations(self):
        """
        Get a list of compressor and mode combinations that will be evaluated.

        :return: A dictionary with keys in the format "compressor:mode" and
                 values as tuples (compressor, mode).
        """

        combinations_dictionary = {}
        # In case both the compressor and the mode are defined, just return these
        if not self.multi_mode:
            combinations_dictionary[f"{self.options.compressor}:{self.options.mode}"] = (
                self.options.compressor, self.options.mode)
            return combinations_dictionary

        # Otherwise, loop over the possible combinations
        for compressor in self.compressors:
            for mode in lossy_compressors_and_modes[compressor]:
                # FIXME: For now we are skipping the norm2 and psnr modes for sz3 because seem to be buggy
                if mode in ["norm2", "psnr"]:
                    continue
                combinations_dictionary[f"{compressor}:{mode}"] = (compressor, mode)
        return combinations_dictionary


def from_dict_to_csv(dictionary: dict) -> str:
    """
    Convert a dictionary to a CSV string.

    :param dictionary: The dictionary to convert.
    :return: The CSV string representation of the dictionary.
    """
    return ",".join([f"{key}:{value}" for key, value in dictionary.items()])


def from_csv_to_dict(csv: str) -> dict:
    """
    Convert a CSV string to a dictionary.

    :param csv: The CSV string to convert.
    :return: The dictionary representation of the CSV string.
    """
    to_return = {}
    for entry in csv.split(","):
        key, value = entry.split(":")
        to_return[key] = float(value)
    return to_return
