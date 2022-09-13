from os.path import join

import pytest

from enstools.encoding import check_libpressio_availability

from utils import TestClass

folders = None


class TestEmulate(TestClass):
    @pytest.mark.skipif(not check_libpressio_availability(), reason="Requires libpressio")
    def test_emulation(self):
        from enstools.io import read
        from enstools.compression.emulation import emulate_compression_on_dataset
        input_tempdir = self.input_tempdir
        output_tempdir = self.output_tempdir
        datasets = ["dataset_%iD.nc" % dimension for dimension in range(3, 4)]
        compression_specifications = ["lossy,sz,rel,0.1",
                                      "lossy,sz,pw_rel,0.01",
                                      "lossy,zfp,rate,1.0"
                                      ]
        for ds in datasets:
            input_path = join(input_tempdir.getpath(), ds)
            # Import and launch compress function
            ds = read(input_path)
            for compression_specification in compression_specifications:
                ds, _ = emulate_compression_on_dataset(ds, compression=compression_specification)
