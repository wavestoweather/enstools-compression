from utils import wrapper, TestClass

folders = None


class TestZFP(TestClass):
    def test_zfp_filter_availability(self):
        from enstools.encoding.api import check_zfp_availability
        assert check_zfp_availability

    def test_compress_zfp_rate(self):
        compression = "lossy,zfp,rate,1"
        wrapper(self, compression=compression)

    def test_compress_zfp_accuracy(self):
        compression = "lossy,zfp,accuracy,.1"
        wrapper(self, compression=compression)

    def test_compress_zfp_precision(self):
        compression = "lossy,zfp,precision,17"
        wrapper(self, compression=compression)

    def test_compress_zfp_variable_specification(self):
        compression = "temperature:lossy,zfp,rate,1 precipitation:lossy,zfp,rate,2"
        wrapper(self, compression=compression)

