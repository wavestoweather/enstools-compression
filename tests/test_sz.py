from os.path import join

import pytest

from enstools.encoding.api import check_sz_availability, check_libpressio_availability

from utils import wrapper, TestClass

folders = None


class TestSZ(TestClass):
    def test_sz_analyzer(self):
        from enstools.compression.api import analyze_files
        # Check that the compression without specifying compression parameters works
        datasets = ["dataset_%iD.nc" % dimension for dimension in range(1, 4)]
        for ds in datasets:
            input_path = self.input_directory_path / ds
            analyze_files(file_paths=input_path, compressor="sz")

    def test_compress_sz_pw_rel(self):
        compression = "lossy,sz,pw_rel,0.1"
        wrapper(self, compression=compression)

    def test_compress_sz_abs(self):
        compression = "lossy,sz,abs,0.01"
        wrapper(self, compression=compression)

    def test_compress_sz_rel(self):
        compression = "lossy,sz,rel,0.001"
        wrapper(self, compression=compression)
