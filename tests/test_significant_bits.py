from utils import TestClass

folders = None


class TestPrune(TestClass):
    def test_significant_bits_analysis(self):
        from enstools.compression.significant_bits import analyze_file_significant_bits
        # Check that the compression without specifying compression parameters works
        datasets = ["dataset_%iD.nc" % dimension for dimension in range(3, 4)]
        for ds in datasets:
            input_path = self.input_directory_path / ds
            # Import and launch compress function
            analyze_file_significant_bits(input_path)

    def test_prune(self):
        from enstools.compression.pruner import pruner
        datasets = ["dataset_%iD.nc" % dimension for dimension in range(3, 4)]
        for ds in datasets:
            input_path = self.input_directory_path / ds
            # Import and launch compress function
            pruner(input_path, self.output_directory_path)

    def test_prune_multiple_files(self):
        from enstools.compression.pruner import pruner
        datasets = ["dataset_%iD.nc" % dimension for dimension in range(2, 4)]
        data_paths = [self.input_directory_path / ds for ds in datasets]
        pruner(data_paths, self.output_directory_path)

    def test_prune_multiple_keeping_variables(self):
        from enstools.compression.pruner import pruner
        datasets = ["dataset_%iD.nc" % dimension for dimension in range(2, 4)]
        data_paths = [self.input_directory_path / ds for ds in datasets]
        pruner(data_paths, self.output_directory_path, variables_to_keep=["temperature"])
