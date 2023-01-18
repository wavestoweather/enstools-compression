from dataclasses import dataclass
from typing import Union

from enstools.core.errors import EnstoolsError
from enstools.encoding.api import lossy_compressors_and_modes


@dataclass
class AnalysisOptions:
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
    options: AnalysisOptions

    def __post_init__(self):
        # If mode is not None, compressor also shouldn't be None
        if self.options.mode is not None and self.options.compressor is None:
            raise EnstoolsError(f"Compression mode is assigned to {self.options.mode} but no compressor is specified.")
        self.multi_mode = self.options.mode in [None, "None", "all"]

    @property
    def compressors(self):
        if self.options.compressor in ["None", "all"]:
            return [compressor for compressor in lossy_compressors_and_modes]
        else:
            return [self.options.compressor]

    def get_compressor_mode_combinations(self):
        """
        Get a list of compressors and modes that will be evaluated.
        :return:
        """

        combinations_dictionary = {}
        # In case both the compressor and the mode are defined, just return these
        if not self.multi_mode:
            combinations_dictionary[f"{self.options.compressor}:{self.options.mode}"] = (
                self.options.compressor, self.options.mode)
            return combinations_dictionary
        else:
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
    Convert a dictionary to a csv string.
    """
    return ",".join([f"{key}:{value}" for key, value in dictionary.items()])


def from_csv_to_dict(csv: str) -> dict:
    """
    Convert a csv string to a dictionary.
    """
    to_return = {}
    for entry in csv.split(","):
        key, value = entry.split(":")
        to_return[key] = float(value)
    return to_return
