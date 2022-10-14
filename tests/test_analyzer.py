from os.path import isfile, join

import pytest

from enstools.encoding.api import check_sz_availability, check_libpressio_availability

from utils import file_size, wrapper, TestClass

folders = None


class TestAnalyzer(TestClass):
    def test_analyzer(self):
        from enstools.compression.api import analyze_files
        input_tempdir = self.input_directory_path
        # Check that the compression without specifying compression parameters works
        datasets = ["dataset_%iD.nc" % dimension for dimension in range(1, 4)]
        for ds in datasets:
            input_path = input_tempdir / ds
            analyze_files(file_paths=[input_path])

    def test_zfp_analyzer(self):
        from enstools.compression.api import analyze_files
        input_tempdir = self.input_directory_path
        # Check that the compression without specifying compression parameters works
        datasets = ["dataset_%iD.nc" % dimension for dimension in range(1, 4)]
        for ds in datasets:
            input_path = input_tempdir / ds
            analyze_files(file_paths=[input_path], compressor="zfp")

    def test_inverse_analyzer(self):
        """
        This tests checks that we can find compression parameters to fulfill a certain compression ratio.
        """
        from enstools.compression.api import analyze_files
        from enstools.compression.analyzer.AnalysisOptions import from_csv_to_dict
        # The resulting compression ratio should be within this tolerance.
        TOLERANCE = 1
        cr_label = "compression_ratio"
        input_tempdir = self.input_directory_path
        constrains = "compression_ratio:5"
        thresholds = from_csv_to_dict(constrains)
        # Check that the compression without specifying compression parameters works
        datasets = ["dataset_%iD.nc" % dimension for dimension in range(2, 4)]
        for ds in datasets:
            input_path = input_tempdir / ds
            encodings, metrics = analyze_files(file_paths=[input_path], constrains=constrains)
            if not metrics:
                raise AssertionError("Metrics shouldn't be empty")

            for var in metrics:
                if abs(metrics[var][cr_label] - thresholds[cr_label]) > TOLERANCE:
                    raise AssertionError(f"The resulting compression ratio of {metrics[var][cr_label]:.2f}"
                                         f"x is not close enough to the target of {thresholds[cr_label]:.2f}")

    @pytest.mark.skipif(not check_libpressio_availability(), reason="Requires libpressio")
    def test_sz_analyzer(self):
        from enstools.compression.api import analyze_files
        input_tempdir = self.input_directory_path
        # Check that the compression without specifying compression parameters works
        datasets = ["dataset_%iD.nc" % dimension for dimension in range(1, 4)]
        for ds in datasets:
            input_path = input_tempdir / ds
            analyze_files(file_paths=[input_path], compressor="sz")

    def test_constrains(self):
        from enstools.compression.api import analyze_files
        input_tempdir = self.input_directory_path
        # Check that the compression without specifying compression parameters works
        datasets = ["dataset_%iD.nc" % dimension for dimension in range(1, 4)]
        for ds in datasets:
            input_path = input_tempdir / ds
            analyze_files(file_paths=[input_path],
                          constrains="correlation_I:3,ssim_I:1,nrmse_I:1",
                          # Keep the analysis to a single compressor and mode to speed up tests
                          compressor="zfp",
                          mode="rate",
                          )

    def test_wrong_constrain(self):
        from enstools.compression.api import analyze_files
        from enstools.core.errors import EnstoolsError
        input_tempdir = self.input_directory_path
        # Check that the compression without specifying compression parameters works
        datasets = ["dataset_%iD.nc" % dimension for dimension in range(1, 4)]
        constrains = "dummy_metric:3"
        with pytest.raises(EnstoolsError):
            for ds in datasets:
                input_path = input_tempdir / ds
                analyze_files(file_paths=[input_path], constrains=constrains)

    def test_custom_metric(self):
        from enstools.scores import mean_square_error, add_score_from_file
        from enstools.compression.api import analyze_files

        input_tempdir = self.input_directory_path

        # Create a fake plugin copying an existing score 
        plugin_name = "dummy_metric"
        plugin_path = input_tempdir / f"{plugin_name}.py"

        # Copy the function mean_square_error
        dummy_function = mean_square_error

        # Get the source code
        import inspect
        lines = inspect.getsource(dummy_function)
        function_code = "".join(lines).replace(dummy_function.__name__, plugin_name)
        # Add xarray import to make it complete
        function_code = f"import xarray\n{function_code}"
        # Write it to a file
        with open(plugin_path, "w") as f:
            f.write(function_code)

        # Add the function inside the file as a new score
        add_score_from_file(plugin_path)

        # Check that the analysis using a custom metric defined with a plugin works
        datasets = ["dataset_%iD.nc" % dimension for dimension in range(1, 4)]
        constrains = f"{plugin_name}:3"

        for ds in datasets:
            input_path = input_tempdir / ds
            analyze_files(file_paths=[input_path],
                          constrains=constrains,
                          # Keep the analysis to a single compressor and mode to speed up tests
                          compressor="zfp",
                          mode="rate",
                          )
