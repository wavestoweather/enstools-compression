from os.path import isfile
from typing import Callable, Union
from enstools.core.errors import EnstoolsError

import numpy as np
import xarray

from enstools.io import read


def get_matching_scores(arguments: list) -> dict:
    """
    Returns a dictionary of functions that match with the provided arguments.
    """
    import enstools.scores
    from inspect import getmembers, isfunction, signature
    functions_list = getmembers(enstools.scores, isfunction)

    def check_signature(function: Callable):
        sig = signature(function)
        return all([arg in sig.parameters for arg in arguments])

    # Keep only the functions that match the desired
    return {name: fun for name, fun in functions_list if check_signature(fun)}


# Workaround to update the list of available metrics when the metrics are used,
# not only when the module is imported.
class AvailableMetrics:
    @property
    def get(self):
        return get_matching_scores(arguments=["reference", "target"])

available_metrics = AvailableMetrics()


class DataArrayMetrics:
    """
    First object oriented approach to avoid redundant computation of metrics. (i.e. don't compute mse several times)
    """
    difference: np.ndarray
    available_metrics: list

    def __init__(self, reference: Union[xarray.DataArray, np.ndarray],
                 target: Union[xarray.DataArray, np.ndarray]) -> None:
        # Setting reference and reference_values  depending on the type of the input
        if isinstance(reference, np.ndarray):
            self.reference = xarray.DataArray(reference)
        else:
            self.reference = reference

        if isinstance(target, np.ndarray):
            self.target = xarray.DataArray(target)
        else:
            self.target = target

        # If the inputs have NaNs, replace them with a fill value
        self.fix_nan()

        # Initialize an empty dictionary for metrics
        self.metric_values = {}

        # Add the list of available metrics from metric_definitions
        self.available_metrics = list(available_metrics.get.keys())

    def __getitem__(self, name: str) -> xarray.DataArray:
        # Look if the metric has already been computed.
        # If its true, just return it, otherwise compute it and then return it.
        if name not in self.metric_values:
            self.metric_values[name] = self.compute_metric(name)
        return self.metric_values[name]

    def fix_nan(self):
        # FIXME: That looks a bit dangerous.
        # Replace NaNs with a fill value.
        fill_value = -10000.
        if np.isnan(self.reference.values).any():
            self.reference.values[np.isnan(self.reference.values)] = fill_value
        if np.isnan(self.target.values).any():
            self.target.values[np.isnan(self.target.values)] = fill_value

    def compute_metric(self, method: str) -> xarray.DataArray:
        if method not in self.available_metrics:
            raise EnstoolsError(f"Metric {method!r} not available.")
        return available_metrics.get[method](self.reference, self.target)

    def plot_summary(self, output_folder: str = "report"):
        # TODO: This is not the proper place to put this code. Move it somewhere else.
        import matplotlib.pyplot as plt
        import matplotlib as mpl

        from os.path import isdir, join
        from os import makedirs

        # Get dimensions  
        shape = self.reference.shape
        # Get variable name from DataArray object
        variable_name = self.reference.name

        if len(shape) == 4:
            y, z, x, y = shape
            sl = (0, int(z / 2), slice(None), slice(None))
        elif len(shape) == 3:
            sl = 0, slice(None), slice(None)
        elif len(shape) == 2:
            sl = slice(None), slice(None)
        elif len(shape) == 1:
            return
        else:
            raise NotImplementedError

        plot_num = 4
        reference_data = self.reference[sl]
        target_data = self.target[sl]

        var_range = np.max(reference_data)-np.min(reference_data)

        # Prepare a plot of an intermediate level
        plt.figure(figsize=(9, 9))

        # Plot reference
        plt.subplot(int(f"{plot_num}11"))
        plt.imshow(reference_data)
        plt.colorbar()
        # Plot comparison target
        plt.subplot(int(f"{plot_num}12"))
        plt.imshow(target_data)
        plt.colorbar()

        # Plot differences
        plt.subplot(int(f"{plot_num}13"))
        color_levels = 7
        cmap = plt.cm.seismic  # define the colormap
        # extract all colors from the colormap
        cmaplist = [cmap(i) for i in range(cmap.N)]
        # Generate new colormap with only few levels
        cmap = mpl.colors.LinearSegmentedColormap.from_list('Custom cmap', cmaplist, color_levels)
        difference = self.difference[sl]
        _min = np.min(difference)
        _max = np.max(difference)
        __ = max(abs(_min), _max)
        factor = var_range / __
        vmin = -__
        vmax = __
        # vmin =-iqr/10
        # vmax = iqr/10
        plt.imshow(difference, vmin=vmin, vmax=vmax, cmap=cmap)
        plt.title(f"The difference range is {factor:.1f} smaller than the InterQuartileRange")
        cbar = plt.colorbar()
        cbar.set_ticks(np.linspace(vmin, vmax, color_levels + 1))

        # Put something related with the metrics
        fig = plt.gcf()
        ax = fig.add_subplot(414, polar=True)

        selected_metrics = ["correlation_I", "ssim_I", "nrmse_I"]
        selected_values = np.array([self[m] for m in selected_metrics])
        make_radar_chart(variable_name, selected_metrics, selected_values, ax)
        if not isdir(output_folder):
            makedirs(output_folder)
        plt.tight_layout()
        plt.savefig(join(output_folder, f"report_{variable_name}.png"))
        plt.close("all")

    def __repr__(self):
        return f"DataArray Metrics (id:{id(self)}) Variable:{self.reference.name}"


class DatasetMetrics:
    def __init__(self, reference: Union[str, xarray.Dataset], target: Union[str, xarray.Dataset]) -> None:
        # Check that files exist and save them

        if not isinstance(reference, xarray.Dataset):
            assert isfile(reference), f"Path {reference} its not a valid file."

            self.reference_path = reference

            # Read files
            self.reference = read(self.reference_path)
        else:
            # Read files
            self.reference = reference

        if not isinstance(target, xarray.Dataset):
            assert isfile(target), f"Path {target} its not a valid file."

            self.target_path = target

            # Read files
            self.target = read(self.target_path)
        else:
            self.target = target

        # Get variables
        self.coords = [v for v in self.reference.coords]
        self.variables = [v for v in self.reference.variables if v not in self.coords]

        # Consistency check
        self.check_consistency()

        # Initialize metrics
        self.metrics = {}
        self.initialize_metrics()

    def check_consistency(self) -> None:
        # Check that files are meant to represent the same things
        assert set(self.reference.variables) == set(self.target.variables)
        assert set(self.reference.coords) == set(self.target.coords)

    def initialize_metrics(self) -> None:
        for variable in self.variables:
            self.metrics[variable] = DataArrayMetrics(self.reference[variable], self.target[variable])
        pass

    def __getitem__(self, name: str) -> DataArrayMetrics:
        assert name in self.variables, f"The provided variable name {name} does not exist in this dataset."
        return self.metrics[name]

    def make_plots(self):
        print("Producing plots:")
        for index, variable in enumerate(self.variables):
            print(f"\r{index + 1}/{len(self.variables)} {variable:30} ", end="")
            self[variable].plot_summary()
        print("\rPlots done!" + 30 * " ")

    def create_gradients(self):
        """
        Create first order gradients
        """
        for variable in self.variables:
            ref_grad = array_gradient(self[variable].reference)
            target_grad = array_gradient(self[variable].target)
            if ref_grad is not None:
                self.reference[ref_grad.name] = ref_grad
                self.target[target_grad.name] = target_grad

        # Update list of variables to include the gradients
        self.variables = [v for v in self.reference.variables if v not in self.reference.coords]
        self.initialize_metrics()

    def create_second_order_gradients(self):
        """
        Create first order gradients
        """
        for variable in [v for v in self.variables if v.count("_gradient")]:
            ref_grad = array_gradient(self[variable].reference)
            target_grad = array_gradient(self[variable].target)
            ref_grad.name = ref_grad.name.replace("_gradient" * 2, "_gradient_O2")  # type: ignore
            target_grad.name = target_grad.name.replace("_gradient" * 2, "_gradient_O2")  # type: ignore
            if ref_grad is not None:
                self.reference[ref_grad.name] = ref_grad
                self.target[target_grad.name] = target_grad

        # Update list of variables to include the gradients
        self.variables = [v for v in self.reference.variables if v not in self.reference.coords]
        self.initialize_metrics()

    def __repr__(self):
        return f"Dataset Metrics (id:{id(self)}) Variables:" \
               f"{[v for v in self.reference.variables if v not in self.reference.coords]}"


def make_radar_chart(name, attribute_labels, stats, ax):
    import matplotlib.pyplot as plt
    markers = [0, 3, 6, 9, 12]
    # str_markers = ["0", "3", "6", "9", "12"]

    labels = np.array(attribute_labels)

    angles = np.linspace(0, 2 * np.pi, len(labels), endpoint=False)
    stats = np.concatenate((stats, [stats[0]]))
    angles = np.concatenate((angles, [angles[0]]))

    ax.plot(angles, stats, 'o-', linewidth=.5, alpha=1, markersize=5)
    ax.fill(angles, stats, alpha=0.25)
    ax.set_thetagrids(angles[:-1] * 180 / np.pi, labels)

    ax.plot(angles, [5, 3, 2, 5], ":", color="r", alpha=.5)
    plt.yticks(markers)
    ax.set_title(name)
    ax.grid(True)


def array_gradient(data_array: xarray.DataArray) -> Union[None, xarray.DataArray]:
    """
    Takes one Data Array and returns the gradient.
    In case of multidimensional data, it returns the magnitude of the gradient.

    Maybe it shouldn't be in this file.
    """
    dimensions = len(data_array.shape)
    if dimensions == 1:
        return None

    gradient_axis = tuple(range(1, dimensions))

    new_array = data_array.copy()
    data_values = data_array.values
    try:
        gradient_vect = np.gradient(data_values, axis=gradient_axis)
    except Exception as err:
        print(err)
        return None

    gradient_norm = np.linalg.norm(gradient_vect, axis=0)

    new_array.values = gradient_norm

    new_array.name = f"{new_array.name}_gradient"
    return new_array
