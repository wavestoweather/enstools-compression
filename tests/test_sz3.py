from utils import wrapper, TestClass
import pytest
folders = None
import hdf5plugin
hdf5plugin.register(force=True)


class TestSZ3(TestClass):
    def test_compress_sz3_abs(self):
        compression = "lossy,sz3,abs,0.01"
        wrapper(self, compression=compression)

    def test_compress_sz3_rel(self):
        compression = "lossy,sz3,rel,0.001"
        wrapper(self, compression=compression)

    def test_sz3_analyzer(self):
        from enstools.compression.api import analyze_files
        # Check that the compression without specifying compression parameters works
        datasets = ["dataset_%iD.nc" % dimension for dimension in range(1, 4)]
        for ds in datasets:
            input_path = self.input_directory_path / ds
            analyze_files(file_paths=input_path, compressor="sz3")

