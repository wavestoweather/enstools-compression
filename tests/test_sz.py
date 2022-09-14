from os.path import join

import pytest

from enstools.encoding import check_sz_availability, check_libpressio_availability

from utils import wrapper, TestClass

folders = None


class TestSZ(TestClass):
    @pytest.mark.skipif(check_sz_availability(), reason="Requires SZ not being available")
    def test_sz_checker(self):
        from enstools.encoding.errors import EnstoolsCompressionError
        compression = "lossy,sz,pw_rel,0.1"
        with pytest.raises(EnstoolsCompressionError):
            wrapper(self, compression=compression)

    @pytest.mark.skipif(not check_libpressio_availability(), reason="Requires libpressio")
    def test_sz_analyzer(self):
        from enstools.compression import analyze
        input_tempdir = self.input_tempdir
        # Check that the compression without specifying compression parameters works
        datasets = ["dataset_%iD.nc" % dimension for dimension in range(1, 4)]
        for ds in datasets:
            input_path = join(input_tempdir.getpath(), ds)
            analyze(file_paths=[input_path], compressor="sz")

    @pytest.mark.skipif(not check_sz_availability(), reason="Requires SZ")
    def test_compress_sz_pw_rel(self):
        compression = "lossy,sz,pw_rel,0.1"
        wrapper(self, compression=compression)

    @pytest.mark.skipif(not check_sz_availability(), reason="Requires SZ")
    def test_compress_sz_abs(self):
        compression = "lossy,sz,abs,0.01"
        wrapper(self, compression=compression)

    @pytest.mark.skipif(not check_sz_availability(), reason="Requires SZ")
    def test_compress_sz_rel(self):
        compression = "lossy,sz,rel,0.001"
        wrapper(self, compression=compression)
