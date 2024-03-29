import pytest

from utils import TestClass

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

    def test_analyzer_constant_array(self):
        import enstools.compression.xr_accessor  # noqa
        import numpy as np
        import xarray as xr

        shape = (100, 100, 100)
        data = np.zeros(shape)
        data_array = xr.DataArray(data)
        # Expect a warning about constant values
        with pytest.warns(UserWarning, match="All values in the variable .* are constant."):
            specs, metrics = data_array.compression.analyze()

        data_array.compression(specs)

    def test_analyzer_without_lat_lon(self):
        import enstools.compression.xr_accessor  # noqa
        import numpy as np
        import xarray as xr

        shape = (100, 100, 100)
        data = np.random.random(size=shape)
        data_array = xr.DataArray(data)
        specs, metrics = data_array.compression.analyze()
        data_array.compression(specs)


    def test_zfp_analyzer(self):
        from enstools.compression.api import analyze_files
        input_tempdir = self.input_directory_path
        # Check that the compression without specifying compression parameters works
        datasets = ["dataset_%iD.nc" % dimension for dimension in range(1, 4)]
        for ds in datasets:
            input_path = input_tempdir / ds
            analyze_files(file_paths=[input_path], compressor="zfp")

    def test_analyzer_zfp_precision(self):
        from enstools.compression.api import analyze_files
        from enstools.encoding.dataset_encoding import DatasetEncoding
        input_tempdir = self.input_directory_path
        # Check that the compression without specifying compression parameters works
        datasets = ["dataset_%iD.nc" % dimension for dimension in range(1, 4)]
        for ds in datasets:
            input_path = input_tempdir / ds
            encoding, _ = analyze_files(file_paths=[input_path], compressor="zfp", mode="precision")
            ds_encoding = DatasetEncoding(None, encoding)

    def test_inverse_analyzer(self):
        """
        This tests checks that we can find compression parameters to fulfill a certain compression ratio.
        """
        from enstools.compression.api import analyze_files
        from enstools.compression.analyzer.analysis_options import from_csv_to_dict
        # The resulting compression ratio should be within this tolerance.
        TOLERANCE = 1
        cr_label = "compression_ratio"
        input_tempdir = self.input_directory_path
        constrains = "compression_ratio:5"
        thresholds = from_csv_to_dict(constrains)
        # Check that the compression without specifying compression parameters works
        datasets = ["dataset_%iD.nc" % dimension for dimension in range(3, 4)]
        for ds in datasets:
            input_path = input_tempdir / ds
            encodings, metrics = analyze_files(file_paths=[input_path],
                                               constrains=constrains,
                                               compressor="sz",
                                               mode="abs")
            if not metrics:
                raise AssertionError("Metrics shouldn't be empty")

            for var in metrics:
                if abs(metrics[var][cr_label] - thresholds[cr_label]) > TOLERANCE:
                    raise AssertionError(
                        f"Case:{input_path.name}.The resulting compression ratio of {metrics[var][cr_label]:.2f}"
                        f"x is not close enough to the target of {thresholds[cr_label]:.2f}")

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

    def test_rmse(self):
        from enstools.compression.api import analyze_files
        input_tempdir = self.input_directory_path
        # Check that the compression without specifying compression parameters works
        datasets = ["dataset_%iD.nc" % dimension for dimension in range(1, 4)]
        for ds in datasets:
            input_path = input_tempdir / ds
            analyze_files(file_paths=[input_path],
                          constrains="normalized_root_mean_square_error:1e-5",
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
        from enstools.scores import mean_square_error, register_score
        from enstools.compression.api import analyze_files

        input_tempdir = self.input_directory_path

        # Create a fake plugin copying an existing score
        custom_metric_name = "dummy_metric"

        # Copy the function mean_square_error
        dummy_function = mean_square_error

        # Add the function inside the file as a new score
        register_score(function=dummy_function, name=custom_metric_name)

        # Check that the analysis using a custom metric defined with a plugin works
        datasets = ["dataset_%iD.nc" % dimension for dimension in range(1, 4)]
        constrains = f"{custom_metric_name}:1e-5"

        for ds in datasets:
            input_path = input_tempdir / ds
            analyze_files(file_paths=[input_path],
                          constrains=constrains,
                          # Keep the analysis to a single compressor and mode to speed up tests
                          compressor="zfp",
                          mode="rate",
                          )

    def test_custom_metric_from_file(self):
        from enstools.scores import mean_square_error, add_score_from_file
        from enstools.compression.api import analyze_files

        input_tempdir = self.input_directory_path

        # Create a fake plugin copying an existing score 
        custom_metric_name = "dummy_metric"
        custom_metric_path = input_tempdir / f"{custom_metric_name}.py"

        # Copy the function mean_square_error
        dummy_function = mean_square_error

        # Get the source code
        import inspect
        lines = inspect.getsource(dummy_function)
        function_code = "".join(lines).replace(dummy_function.__name__, custom_metric_name)
        # Add xarray import to make it complete
        function_code = f"import xarray\n{function_code}"
        # Write it to a file
        with open(custom_metric_path, "w") as f:
            f.write(function_code)

        # Add the function inside the file as a new score
        add_score_from_file(custom_metric_path)

        # Check that the analysis using a custom metric defined with a plugin works
        datasets = ["dataset_%iD.nc" % dimension for dimension in range(1, 4)]
        constrains = f"{custom_metric_name}:1e-5"

        for ds in datasets:
            input_path = input_tempdir / ds
            analyze_files(file_paths=[input_path],
                          constrains=constrains,
                          # Keep the analysis to a single compressor and mode to speed up tests
                          compressor="zfp",
                          mode="rate",
                          )
