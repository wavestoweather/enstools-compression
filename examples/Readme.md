# Collection of examples on how to use **enstools-compression**

Few examples on how **enstools-compression** can be used to find proper compression parameters and use these to compress datasets.


## Extra dependencies

For simplicity we rely on sample data provided by xarray that can be fetched by using `xr.tutorial.open_dataset(dataset_name)`.
To do so, besides **enstools-compression** there's a dependency to **pooch**, a library to manage sample data files.
