from dataclasses import dataclass
from typing import Union

from enstools.core.errors import EnstoolsError
from enstools.encoding.api import Compressors, CompressionModes, check_libpressio_availability

compression_modes = {
    Compressors.ZFP: [
        CompressionModes.ACCURACY,
        CompressionModes.RATE,
        CompressionModes.PRECISION,
    ],
    Compressors.SZ: [
        CompressionModes.ABS,
        CompressionModes.REL,
        CompressionModes.PW_REL,
    ]
}


@dataclass
class AnalysisOptions:
    compressor: Compressors
    mode: CompressionModes
    constrains: str
    thresholds: dict

    def __init__(self,
                 compressor: Union[str, Compressors, None],
                 mode: Union[str, CompressionModes, None],
                 constrains: Union[None, str] = None,
                 thresholds: Union[None, dict] = None,
                 ):
        if compressor is None:
            self.compressor = Compressors.NONE
        elif isinstance(compressor, Compressors):
            self.compressor = compressor
        else:
            self.compressor = Compressors[compressor.upper()]

        if mode is None:
            self.mode = CompressionModes.ALL
        elif isinstance(mode, CompressionModes):
            self.mode = mode
        else:
            self.mode = CompressionModes[mode.upper()]

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
        self.multi_mode = self.options.mode is None or self.options.mode is CompressionModes.ALL

    @property
    def compressors(self):
        # Check library availability and select proper analysis_function
        if check_libpressio_availability():
            if self.options.compressor is Compressors.NONE or self.options.compressor is Compressors.ALL:
                return [Compressors.ZFP, Compressors.SZ]
            else:
                return [self.options.compressor]
        else:
            if self.options.compressor is not Compressors.NONE:
                assert self.options.compressor == Compressors.ZFP, "The only available option without libpressio is 'zfp'."

            return [Compressors.ZFP]

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
                for mode in compression_modes[compressor]:
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
