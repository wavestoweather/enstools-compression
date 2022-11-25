from enstools.compression.emulation import emulate_compression_on_data_array, emulate_compression_on_dataset
from enstools.encoding.api import FilterEncodingForH5py, FilterEncodingForXarray, Compressors, CompressionModes
import xarray


@xarray.register_dataarray_accessor("compression")
class EnstoolsCompressionDataArrayAccessor:
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
        compression_specification = FilterEncodingForH5py.from_string(compression)
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

        """
        return self.emulate(compression=compression, in_place=in_place)

    def analyze(self,
                constrains="correlation_I:5,ssim_I:2",
                compressor=Compressors.SZ,
                compression_mode=CompressionModes.ABS,
                ) -> tuple[str, dict]:
        from enstools.compression.analyzer.analyzer import analyze_data_array
        from enstools.compression.analyzer.AnalysisOptions import AnalysisOptions

        options = AnalysisOptions(compressor, compression_mode, constrains=constrains)
        return analyze_data_array(self._obj, options=options)


@xarray.register_dataset_accessor("compression")
class EnstoolsCompressionDatasetAccessor:
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
                fill_na: bool = False,
                ) -> tuple[str, dict]:
        from enstools.compression.analyzer.analyzer import analyze_dataset
        return analyze_dataset(dataset=self._obj, constrains=constrains, fill_na=fill_na)

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

