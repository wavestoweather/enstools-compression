"""
Tests for the commandline interface.
"""

from os.path import isfile

import pytest
from utils import TestClass


class TestCommandLineInterface(TestClass):
    def test_help(self, mocker):
        """
        Check that the cli prints the help and exists.
        """
        import enstools.compression.cli
        commands = ["_", "-h"]
        mocker.patch("sys.argv", commands)
        with pytest.raises(SystemExit):
            enstools.compression.cli.main()

    def test_compress(self, mocker):
        """
        Test enstools-compressor compress
        """
        import enstools.compression.cli

        file_name = "dataset_%iD.nc" % 3
        file_path = self.input_directory_path / file_name
        output_file_path = self.output_directory_path / file_name
        commands = ["_", "compress", str(file_path), "-o", str(output_file_path)]
        mocker.patch("sys.argv", commands)
        enstools.compression.cli.main()
        assert output_file_path.exists()

    def test_compress_with_compression_specification(self, mocker):
        """
        Test enstools-compressor compress
        """
        import enstools.compression.cli

        file_name = "dataset_%iD.nc" % 3
        file_path = self.input_directory_path / file_name
        output_file_path = self.output_directory_path / file_name
        compression = "temperature:lossy,zfp,rate,3.2 precipitation:lossy,zfp,rate,1.6 default:lossless"
        commands = ["_", "compress", str(file_path), "-o", str(output_file_path), "--compression", compression]
        mocker.patch("sys.argv", commands)
        enstools.compression.cli.main()
        assert isfile(output_file_path)

    def test_analyze(self, mocker):
        """
        Test enstools-compressor analyze
        """
        import enstools.compression.cli

        file_name = "dataset_%iD.nc" % 3
        file_path = self.input_directory_path / file_name
        commands = ["_", "analyze", str(file_path)]
        mocker.patch("sys.argv", commands)
        enstools.compression.cli.main()

    def test_analyze_with_plugin(self, mocker):
        """
        Test enstools-compressor analyze using a custom plugin.
        """
        import enstools.compression.cli

        file_name = "dataset_%iD.nc" % 3
        file_path = self.input_directory_path / file_name

        # Create a fake plugin copying an existing score 
        plugin_name = "dummy_metric"
        plugin_path = self.input_directory_path / f"{plugin_name}.py"

        from enstools.scores import mean_square_error
        dummy_function = mean_square_error

        import inspect
        lines = inspect.getsource(dummy_function)
        function_code = "".join(lines).replace(dummy_function.__name__, plugin_name)
        # Add xarray import to make it complete
        function_code = f"import xarray\n{function_code}"
        with open(plugin_path, "w") as f:
            f.write(function_code)

        commands = ["_", "analyze", str(file_path), "--constrains", f"{plugin_name}:4", "--plugins",
                    str(plugin_path), "-c", "zfp"]
        mocker.patch("sys.argv", commands)
        enstools.compression.cli.main()

    def test_analyze_with_sz_and_plugin(self, mocker):
        """
        Test enstools-compressor analyze using a custom plugin.
        """
        import enstools.compression.cli

        file_name = "dataset_%iD.nc" % 3
        file_path = self.input_directory_path / file_name

        # Create a fake plugin copying an existing score 
        plugin_name = "dummy_metric"
        plugin_path = self.input_directory_path / f"{plugin_name}.py"

        from enstools.scores import mean_square_error
        dummy_function = mean_square_error

        import inspect
        lines = inspect.getsource(dummy_function)
        function_code = "".join(lines).replace(dummy_function.__name__, plugin_name)
        # Add xarray import to make it complete
        function_code = f"import xarray\n{function_code}"
        with open(plugin_path, "w") as f:
            f.write(function_code)

        commands = ["_", "analyze", str(file_path), "--constrains", f"{plugin_name}:4", "--plugins", str(plugin_path), "-c", "sz"]
        mocker.patch("sys.argv", commands)
        enstools.compression.cli.main()

    def test_inverse_analyze(self, mocker):
        """
        Test enstools-compressor analyze in compression ratio mode.
        """
        import enstools.compression.cli
        file_name = "dataset_%iD.nc" % 3
        file_path = self.input_directory_path / file_name
        commands = ["_", "analyze", str(file_path), "--constrains", "compression_ratio:5"]
        mocker.patch("sys.argv", commands)
        enstools.compression.cli.main()

    def test_evaluator(self, mocker):
        """
        Test enstools-compressor evaluate
        """
        import enstools.compression.cli
        file_name = "dataset_%iD.nc" % 3
        file_path = self.input_directory_path / file_name
        commands = ["_", "evaluate", "-r", str(file_path), "-t", str(file_path)]
        mocker.patch("sys.argv", commands)
        enstools.compression.cli.main()

    def test_significand(self, mocker):
        """
        Test enstools-compressor significand
        """
        import enstools.compression.cli
        file_name = "dataset_%iD.nc" % 3
        file_path = self.input_directory_path / file_name
        commands = ["_", "significand", str(file_path)]
        mocker.patch("sys.argv", commands)
        enstools.compression.cli.main()

    def test_pruner(self, mocker):
        """
        Test enstools-compressor prune
        """
        import enstools.compression.cli

        file_name = "dataset_%iD.nc" % 3
        file_path = self.input_directory_path / file_name
        commands = ["_", "prune", str(file_path), "-o", str(self.output_directory_path)]
        mocker.patch("sys.argv", commands)
        enstools.compression.cli.main()
