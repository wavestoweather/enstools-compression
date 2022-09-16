from os.path import isfile, join

import pytest

from enstools.encoding import check_sz_availability, check_libpressio_availability

from utils import file_size, wrapper, TestClass

folders = None


class TestAnalyzer(TestClass):
    def test_analyzer(self):
        from enstools.compression import analyze
        input_tempdir = self.input_tempdir
        # Check that the compression without specifying compression parameters works
        datasets = ["dataset_%iD.nc" % dimension for dimension in range(1, 4)]
        for ds in datasets:
            input_path = join(input_tempdir.getpath(), ds)
            analyze(file_paths=[input_path])

    def test_zfp_analyzer(self):
        from enstools.compression import analyze
        input_tempdir = self.input_tempdir
        # Check that the compression without specifying compression parameters works
        datasets = ["dataset_%iD.nc" % dimension for dimension in range(1, 4)]
        for ds in datasets:
            input_path = join(input_tempdir.getpath(), ds)
            analyze(file_paths=[input_path], compressor="zfp")

    def test_inverse_analyzer(self):
        """
        This tests checks that we can find compression parameters to fulfill a certain compression ratio.
        """
        from enstools.compression import analyze
        from enstools.compression.analyzer.AnalysisOptions import from_csv_to_dict
        # The resulting compression ratio should be within this tolerance.
        TOLERANCE = 1
        cr_label = "compression_ratio"
        input_tempdir = self.input_tempdir
        constrains = "compression_ratio:5"
        thresholds = from_csv_to_dict(constrains)
        # Check that the compression without specifying compression parameters works
        datasets = ["dataset_%iD.nc" % dimension for dimension in range(2, 4)]
        for ds in datasets:
            input_path = join(input_tempdir.getpath(), ds)
            encodings, metrics = analyze(file_paths=[input_path], constrains=constrains)
            if not metrics:
                raise AssertionError("Metrics shouldn't be empty")

            for var in metrics:
                if abs(metrics[var][cr_label] - thresholds[cr_label]) > TOLERANCE:
                    raise AssertionError(f"The resulting compression ratio of {metrics[var][cr_label]:.2f}"
                                         f"x is not close enough to the target of {thresholds[cr_label]:.2f}")

    @pytest.mark.skipif(not check_libpressio_availability(), reason="Requires libpressio")
    def test_sz_analyzer(self):
        from enstools.compression import analyze
        input_tempdir = self.input_tempdir
        # Check that the compression without specifying compression parameters works
        datasets = ["dataset_%iD.nc" % dimension for dimension in range(1, 4)]
        for ds in datasets:
            input_path = join(input_tempdir.getpath(), ds)
            analyze(file_paths=[input_path], compressor="sz")

    def test_constrains(self):
        from enstools.compression import analyze
        input_tempdir = self.input_tempdir
        # Check that the compression without specifying compression parameters works
        datasets = ["dataset_%iD.nc" % dimension for dimension in range(1, 4)]
        constrains = "correlation_I:3,ssim_I:1,nrmse_I:1"
        for ds in datasets:
            input_path = join(input_tempdir.getpath(), ds)
            analyze(file_paths=[input_path], constrains=constrains)

    def test_wrong_constrain(self):
        from enstools.compression import analyze
        from enstools.core.errors import EnstoolsError
        input_tempdir = self.input_tempdir
        # Check that the compression without specifying compression parameters works
        datasets = ["dataset_%iD.nc" % dimension for dimension in range(1, 4)]
        constrains = "dummy_metric:3"
        with pytest.raises(EnstoolsError):
            for ds in datasets:
                input_path = join(input_tempdir.getpath(), ds)        
                analyze(file_paths=[input_path], constrains=constrains)

    def test_custom_metric(self):
        import enstools.scores
        function_file = "/home/o/Oriol.Tinto/enstools-projects/try_things/dummy_function.py"
        enstools.scores.add_score_from_file(function_file)
        from enstools.compression import analyze
        from enstools.compression.metrics import available_metrics

        assert "dummy_function" in available_metrics
        
        # Set the dummy metric
        
        
        input_tempdir = self.input_tempdir
        # Check that the compression without specifying compression parameters works
        datasets = ["dataset_%iD.nc" % dimension for dimension in range(1, 4)]
        constrains = "dummy_function:3"


        """
        def dummy_metric(reference, target):
            return 4
        
        import inspect
        lines = inspect.getsource(dummy_metric)
        ####
        # Define and write a dummy metric file.


        with open(f"{extra_metrics}.py", "w") as f:
            f.write(lines)
        """

        for ds in datasets:
            input_path = join(input_tempdir.getpath(), ds)        
            analyze(file_paths=[input_path], constrains=constrains)