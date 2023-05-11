"""
This module registers the xarray compression accessor for Datasets and DataArrays.
After importing this module xarray datasets can use the compression methods in a convenient way, for example:
    dataset.compression("lossy,sz,pw_rel,0.0001")
or 
    data_array.compression("lossy,sz,pw_rel,0.0001")

"""

from os import PathLike
from typing import Union

from dask import delayed
import xarray

from enstools.encoding.api import VariableEncoding, DatasetEncoding
from enstools.compression.emulation import emulate_compression_on_data_array, emulate_compression_on_dataset
from enstools.compression.analyzer.analysis_options import AnalysisOptions
from enstools.compression.analyzer.analyzer import analyze_data_array, analyze_dataset


@xarray.register_dataarray_accessor("compression")
class EnstoolsCompressionDataArrayAccessor:
    """
    Enstools-compression DataArray accessor class.
    """
    def __init__(self, xarray_obj: xarray.DataArray):
        """
        Initialize the accessor saving a reference of the data array.

        Parameters
        ----------
        xarray_obj: xarray.DataArray
        """
        self._obj = xarray_obj

    def emulate(self, compression: str, in_place=False) -> xarray.DataArray:
        """
        Emulate compression on a data array.

        Parameters
        ----------
        compression: str
        in_place: bool

        Returns
        -------
        xarray.DataArray
        """
        compression_specification = VariableEncoding(compression)
        data_array, metrics = emulate_compression_on_data_array(data_array=self._obj,
                                                                compression_specification=compression_specification,
                                                                in_place=in_place)
        data_array.attrs["compression_specification"] = compression
        data_array.attrs["compression_ratio"] = f"{metrics['compression_ratio']:.2f}"
        return data_array

    def __call__(self, compression: str, in_place=False) -> xarray.DataArray:
        """
        Calling the accessor directly uses emulate method.

        Parameters
        ----------
        compression: str
        in_place: bool

        Returns
        -------
        xarray.DataArray


        """
        return self.emulate(compression=compression, in_place=in_place)

    def analyze(self,
                constrains="correlation_I:5,ssim_I:2",
                compressor="sz",
                compression_mode="abs",
                ):
        """
        Apply the analysis method on the DataArray

        Parameters
        ----------
        constrains: str
        compressor: str
        compression_mode: str

        Returns
        -------
        dict

        """
        options = AnalysisOptions(compressor, compression_mode, constrains=constrains)
        return analyze_data_array(self._obj, options=options)

    @staticmethod
    def encoding(compression: str):
        """
        Returns the VariableEncoding corresponding to this DataArray

        Args:
            compression (str): compression specification string

        Returns:
            VariableEncoding
        """
        return VariableEncoding(specification=compression)


@xarray.register_dataset_accessor("compression")
# pylint: disable=too-few-public-methods
class EnstoolsCompressionDatasetAccessor:
    """
    Enstools-compression Dataset accessor class.
    """

    def __init__(self, xarray_obj: xarray.Dataset):
        """
        Initialize the accessor saving a reference of the dataset.

        Parameters
        ----------
        xarray_obj: xarray.Dataset
        """
        self._obj = xarray_obj

    def emulate(self, compression: str, in_place=False) -> xarray.Dataset:
        """
        Emulate compression on a dataset.

        Parameters
        ----------
        compression: str
        in_place: bool

        Returns
        -------
        xarray.Dataset
        """
        # compression_specification = FilterEncodingForH5py.from_string(compression)
        dataset, metrics = emulate_compression_on_dataset(compression=compression, dataset=self._obj, in_place=in_place)
        # Set attributes for each variable
        for var, _metrics in metrics.items():
            dataset[var].attrs["compression_specification"] = compression
            dataset[var].attrs["compression_ratio"] = f"{_metrics['compression_ratio']:.2f}"
        return dataset

    def analyze(self,
                constrains="correlation_I:5,ssim_I:2",
                **kwargs
                ):
        """
        Apply the analysis method on the Dataset

        Parameters
        ----------
        constrains: str
        compressor: str
        compression_mode: str

        Returns
        -------
        dict

        """
        return analyze_dataset(dataset=self._obj, constrains=constrains, **kwargs)

    def encoding(self, compression: str):
        """
        Returns the DatasetEncoding corresponding to this DataArray

        Args:
            compression (str): compression specification string

        Returns:
            DatasetEncoding
        """
        return DatasetEncoding(self._obj, compression=compression)

    def __call__(self, compression: str, in_place=False) -> xarray.Dataset:
        """
        Calling the accessor directly uses emulate method.

        Parameters
        ----------
        compression: str
        in_place: bool

        Returns
        -------

        """
        return self.emulate(compression=compression, in_place=in_place)


@xarray.register_dataset_accessor("to_compressed_netcdf")
class EnstoolsCompressionToCompressedNetcdf:
    """
    Accessor to enable the method to_compressed_netcdf to xarray Datasets
    """
    def __init__(self, xarray_obj: xarray.Dataset):
        """
        Initialize the accessor saving a reference of the dataset.

        Parameters
        ----------
        xarray_obj: xarray.Dataset
        """
        self._obj = xarray_obj

    def __call__(self, path: Union[str, PathLike, None] = None, compression: str = None, **kwargs) -> \
            Union[bytes, None, delayed]:
        """
        The accessor is a shortcut to to_netcdf adding the proper encoding and the engine arguments.

        Parameters
        ----------
        path: str | pathlike | None
        compression: str
        kwargs: Any other keyword arguments that can be used with xarray's to_netcdf method.

        Returns
        -------

        """
        encoding = self._obj.compression.encoding(compression=compression)
        encoding.add_metadata()
        return self._obj.to_netcdf(path, encoding=encoding, engine="h5netcdf", **kwargs)
