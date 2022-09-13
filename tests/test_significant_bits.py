from os.path import join

from utils import TestClass

folders = None


class TestPrune(TestClass):
    def test_significant_bits_analysis(self):
        from enstools.compression.significant_bits import analyze_file_significant_bits
        input_tempdir = self.input_tempdir
        # Check that the compression without specifying compression parameters works
        datasets = ["dataset_%iD.nc" % dimension for dimension in range(3, 4)]
        for ds in datasets:
            input_path = join(input_tempdir.getpath(), ds)
            # Import and launch compress function
            analyze_file_significant_bits(input_path)

    def test_prune(self):
        from enstools.compression.pruner import pruner
        input_tempdir = self.input_tempdir
        output_tempdir = self.output_tempdir
        datasets = ["dataset_%iD.nc" % dimension for dimension in range(3, 4)]
        for ds in datasets:
            input_path = join(input_tempdir.getpath(), ds)
            # Import and launch compress function
            pruner(input_path, output_tempdir.getpath())
