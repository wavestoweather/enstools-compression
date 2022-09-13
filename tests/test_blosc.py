from utils import wrapper, TestClass

folders = None


class TestBlosc(TestClass):
    def test_compress_lossless(self):
        compression = "lossless"
        wrapper(self, compression=compression)

