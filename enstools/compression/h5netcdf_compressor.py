from pathlib import Path
from typing import List


def transfer_file(origin: Path,
                  destination: Path,
                  compression: str,
                  variables_to_keep: List[str] = None,
                  parts=1,
                  **kwargs):
    if kwargs:
        print(f"The h5netcdf implementation of transfer_file ignores the following keyword arguments: {kwargs}")
    import h5netcdf
    from enstools.encoding.api import DatasetEncoding

    # Still using xarray to get the encoding
    import xarray as xr
    with xr.open_dataset(origin, engine="h5netcdf") as ds:
        # Fet variables
        data_vars = variables_to_keep if variables_to_keep is not None else [v for v in ds.data_vars]
        encoding = DatasetEncoding(ds, compression=compression)

    # Open the origin and destination files.
    with h5netcdf.File(origin, 'r') as source_file, h5netcdf.File(destination, 'w') as destination_file:
        # Copy global attributes
        for attr in source_file.attrs:
            destination_file.attrs[attr] = source_file.attrs[attr]

        # Add dimensions
        for dimension_name in source_file.dimensions:
            dimension = source_file.dimensions[dimension_name]
            if not dimension.isunlimited():
                destination_file.dimensions[dimension.name] = dimension.size
            else:
                destination_file.dimensions[dimension.name] = None
                destination_file.resize_dimension(dimension.name, dimension.size)

        # Get the list of variables to copy which include the data variables and the coordinates with values
        variables_to_copy = data_vars + [v for v in source_file.variables if v in source_file.dimensions]

        # Copy variable by variable
        for var_name in variables_to_copy:
            source_var = source_file[var_name]
            var_encoding = {**encoding[var_name]}

            # xarray and h5netcdf use different keyword for the chunks. Here we replace the key
            if "chunksizes" in var_encoding:
                var_encoding["chunks"] = var_encoding.pop("chunksizes")
            # Create variable without the data
            destination_file.create_variable(name=var_name,
                                             dimensions=source_var.dimensions,
                                             dtype=source_var.dtype,
                                             **var_encoding,
                                             )

            # Get the destination variable object
            destination_var = destination_file[var_name]

            # Slice the domain in chunks of a certain chunk size:
            from .slicing import MultiDimensionalSliceCollection
            multi_dimensional_slice = MultiDimensionalSliceCollection(shape=destination_var.shape,
                                                                      chunk_sizes=destination_var.chunks,
                                                                      )

            # If there's more than a single chunk, loop over the chunks.
            if len(multi_dimensional_slice) > 1:

                # Divide the multi-dimensional-slice in a certain number of parts
                groups = multi_dimensional_slice.split(parts=parts)

                # Get the slices corresponding to each part
                slices = [g.slice for g in groups]

                # Copy the slices
                for slc in slices:
                    destination_var[slc] = source_var[slc][()]
            else:
                destination_var[:] = source_var[()]

            # Copy variable attributes
            for attr in source_var.attrs:
                destination_var.attrs[attr] = source_var.attrs[attr]
