"""
Command Line Interface for different enstools-compression utilities
"""

# Few help messages
compressor_help_text = """
compress: 

Tool to apply HDF5 compression filters to netCDF files. Compression specifications must follow the Compression Specification Format, more details below.

Examples
--------

-Single file:
    >>> enstools-compression compress "input.nc" -o "output/folder/" 
    or
    >>> enstools-compression compress "input.nc" -o "output_file.nc"

-Multiple files:
    >>> enstools-compression compress "input_1.nc" "input_2.nc" -o "output/folder/"

-Multiple files using wildcards:
    >>> enstools-compression compress "input_files_*" -o "output/folder/"  


To use custom compression parameters:
    >>> enstools-compression compress "input_files_*" -o "output/folder/" --compression compression_specification

Compression Specification Format
--------------------------------

The compression_specification can be a string that follows the Compression Specification Format (see more details in enstools-encoding.readthedocs.com) or a filepath
to a configuration file in which we might have per variable specification.

For lossless compression, we can choose the backend and the compression leven as follows
    >>> lossless,backend,compression_level(from 1 to 9)
    
The backend must be one of the following options:
        - blosclz
        - lz4
        - lz4hc
        - snappy
        - zlib
        - zstd

For lossy compression, we can choose the compressor (sz or zfp),
the method and the method parameter.

    >>> lossy,compressor,mode,parameter

Some examples:
    - lossless
    - lossless,zlib,5
    - lossy,zfp,accuracy,0.00001
    - lossy,zfp,precision,12
    - lossy,zfp,rate,3.2
    - lossy,sz,abs,0.1
    - lossy,sz,rel,0.0001
    - lossy,sz,pw_rel,1.e-6
            
If using a configuration file, the file should follow a yaml format and can contain per-variable values.
It is also possible to define a default option. For example:

    .. highlight:: python
    .. code-block:: yaml
        
        default: lossless
        temp: lossy,zfp,accuracy,0.1
        qv: lossy,sz,pw_rel,0.0001


So, few examples with custom compression would be:

    >>> enstools-compression compress "input_files_*" -o "output/folder/" --compression lossless

    >>> enstools-compression compress "input_files_*" -o "output/folder/" --compression lossless,blosclz,9

    >>> enstools-compression compress "input_files_*" -o "output/folder/" --compression lossy,zfp,rate,3.2
    
    >>> enstools-compression compress "input_files_*" -o "output/folder/" --compression lossy,sz,abs,0.01

    >>> enstools-compression compress "input_files_*" -o "output/folder/" --compression compression_parameters.yaml

Also, it is possible to automatically find which are the compression parameters that must be applied
to each variable in order to maintain a 0.99999 Pearson correlation and a 0.99 structural similarity.
Be aware that that will cause an overhead due to the necessary time to find the appropriate parameters. 

    >>> enstools-compression compress "input_files_*" -o "output/folder/" --compression auto

It is possible to parallelize the compression of multiple files by launch a SLURM job for workers.
To do that, specify the number of nodes to use:

    >>> enstools-compression compress -o "output/folder/" "input_files_*" --nodes 4

"""

# For each possible usage (compress, analyze, ...) we will define a function to add
# the corresponding command line arguments to the parser and another one to manage the call

###############################
# Compressor
def add_subparser_compressor(subparsers):
    import argparse

    subparser = subparsers.add_parser('compress', help='Compress help',
                                      formatter_class=argparse.RawDescriptionHelpFormatter,
                                      description=compressor_help_text)
    subparser.add_argument("files", type=expand_paths, nargs='*',
                           help="Path to file/files that will be compressed."
                                "Multiple files and regex patterns are allowed.")
    subparser.add_argument("-o", '--output', type=str, dest="output", default=None, required=True)

    subparser.add_argument('--compression', type=str, dest="compression", nargs="+", default="lossless",
                           help="""
        Specifications about the compression options. Default is: %(default)s""")
    subparser.add_argument("--nodes", "-N", dest="nodes", default=0, type=int,
                           help="This parameter can be used to allocate additional nodes in the cluster"
                                "to speed-up the computation.")
    subparser.add_argument("--variables", dest="variables", default=None, type=str,
                           help="List of variables to be kept. The other variables will be dropped."
                                "Must be a list of comma separated values: i.e. vor,temp,qv"
                                "Default=None")
    subparser.add_argument("--emulate", dest="emulate", default=False, action='store_true',
                           help="Instead of saving compressed files, it compresses and decompresses the data to see"
                                "compression effects without requiring the plugins to open the files.")
    subparser.add_argument("--fill-na", dest="fill_na", default=False,
                           help="Fill the missing values with a float.")

    subparser.set_defaults(which='compressor')


def call_compressor(args):
    from os.path import realpath
    # Read the output folder from the command line and assert that it exists and has write permissions.
    output = realpath(args.output)

    file_paths = args.files
    file_paths = sum(file_paths, [])

    # Compression options
    compression = args.compression

    # Get parameter for fill_na
    fill_na = args.fill_na
    if fill_na is not False:
        fill_na = float(fill_na)
    if isinstance(compression, list):
        compression = " ".join(compression)

    if compression in ["None", "none"]:
        compression = None

    # Read the number of nodes
    nodes = args.nodes

    # List of variables
    variables = args.variables
    if variables is not None:
        variables = variables.split(",")
    emulate = args.emulate
    # Import and launch compress function
    from enstools.compression.api import compress
    compress(file_paths, output, compression, nodes, variables_to_keep=variables, emulate=emulate, fill_na=fill_na)


###############################
# Analyzer

analyzer_help_text = """
analyze: 

Tool to find which compression specifications maximise the compression ratio while maintaining certain quality metrics provided by the argument **constrains**.

Examples
--------

Analyze file using default constrains:

>>> enstools-compression analyze "input_file.nc"


Analyze file using custom constrains:

>>> enstools-compression analyze "input_file.nc" --constrains "correlation_I:7,ssim_I:4"

Analyze file and save the results to a file:

>>> enstools-compression analyze "input_file.nc" -o "compression_specifications.yaml"

Analyze files using a custom metric:

>>> enstools-compression analyze "input_file.nc" --constrains "my_metric:5" --plugin my_metric.py

where **my_metric.py** contains a function with the same name which expects two xarray as arguments (reference and target) 
and returns an xarray with the time-series of the desired metric.


Constrains
----------

The constrain specification must be provided in the following format:
    >>> "metric1:value1,metric2:value2,metric3:value3"


"""

def add_subparser_analyzer(subparsers):
    import argparse

    subparser = subparsers.add_parser('analyze', help=analyzer_help_text,
                                      formatter_class=argparse.RawDescriptionHelpFormatter)

    subparser.add_argument("--constrains", dest="constrains",
                           default="correlation_I:5,ssim_I:2", type=str,
                           help="Quality constrains that need to be fulfilled.")

    subparser.add_argument("--output", "-o", dest="output", default=None, type=str,
                           help="Path to the file where the configuration will be saved."
                                "If not provided will be print in the stdout.",
                           )
    subparser.add_argument("--compressor", "-c", dest="compressor", default=None, type=str,
                           help="Which compressor will be used. Options are zfp, sz or all.",
                           )
    subparser.add_argument("--mode", "-m", dest="mode", default=None, type=str,
                           help="Which mode will be used. The options depend on the compressor."
                                "For sz: abs, rel, pw_rel. For zfp: accuracy, rate, precision."
                                "Also it is possible to use 'all'",
                           )
    subparser.add_argument("--grid", "-g", dest="grid", default=None, type=str,
                           help="Path to the file containing grid information.",
                           )
    subparser.add_argument("files", type=str, nargs="+",
                           help='List of files to compress. '
                                'Multiple files and regex patterns are allowed.',
                           )

    subparser.add_argument("--plugins", type=str, nargs="*",
                           help='List of files with custom metric definitions.'
                           )

    subparser.add_argument("--fill-na", dest="fill_na", default=False,
                           help="Fill the missing values with a float.")
    subparser.add_argument("--variables", dest="variables", default=None, type=str,
                           help="List of variables to analyze."
                                "Must be a list of comma separated values: i.e. vor,temp,qv"
                                "Default=None")

    subparser.set_defaults(which='analyzer')


def call_analyzer(args):
    file_paths = args.files
    grid = args.grid
    # Compression options
    constrains = args.constrains
    compressor = args.compressor
    mode = args.mode

    # Output filename
    output_file = args.output

    # Get parameter for
    fill_na = float(args.fill_na) if args.fill_na is not False else False

    # List of variables
    variables = args.variables
    if variables is not None:
        variables = variables.split(",")

    # In case a custom plugin is used:
    plugins = args.plugins
    if plugins:
        import enstools.scores
        for plugin in plugins:
            enstools.scores.add_score_from_file(plugin)

    from enstools.compression.api import analyze_files
    analyze_files(
        file_paths=file_paths,
        output_file=output_file,
        constrains=constrains,
        compressor=compressor,
        mode=mode,
        grid=grid,
        fill_na=fill_na,
        variables=variables,
    )


###############################
# Find significand bits

significant_bits_help_text = """
significand:

Tool to find the ammount of significand bits in a data file following the approach described in Klöwer et al 2021 _[1].

.. [1] Klöwer, M., Razinger, M., Dominguez, J.J. et al. Compressing atmospheric data into its real information content.
Nat Comput Sci 1, 713-724 (2021). https://doi.org/10.1038/s43588-021-00156-2

"""

def add_subparser_significand(subparsers):
    import argparse

    subparser = subparsers.add_parser('significand', help=significant_bits_help_text,
                                      formatter_class=argparse.RawDescriptionHelpFormatter)
    subparser.add_argument("--output", "-o", dest="output", default=None, type=str,
                           help="Path to the file where the configuration will be saved."
                                "If not provided will be print in the stdout.")
    subparser.add_argument("--grid", "-g", dest="grid", default=None, type=str,
                           help="Path to the file containing grid information.")
    subparser.add_argument("files", type=str, nargs="+",
                           help='List of files to compress. Multiple files and regex patterns are allowed.')
    subparser.set_defaults(which='significand')


def call_significand(args):
    from enstools.compression.api import analyze_file_significant_bits
    file_paths = args.files

    for file_path in file_paths:
        analyze_file_significant_bits(file_path)


###############################
# Evaluator
evaluate_help_text = """
evaluate:

Tool to quickly compare two datasets, mainly though to compare a compressed dataset with its reference.

"""

def add_subsubparser(subparsers):
    import argparse
    subparser = subparsers.add_parser('evaluate', help=evaluate_help_text,
                                      formatter_class=argparse.RawDescriptionHelpFormatter)
    subparser.add_argument("--reference", "-r", dest="reference_file", default=None, type=str,
                           help="Path to reference file. Default=%(default)s", required=True)
    subparser.add_argument("--target", "-t", dest="target_file", default=None, type=str,
                           help="Path to target file", required=True)
    subparser.add_argument("--plot", dest="plot", default=False, action='store_true',
                           help="Produce evaluation plots. Default=%(default)s")
    subparser.set_defaults(which='evaluator')


def call_evaluator(args):
    reference_file_path = args.reference_file
    target_file_path = args.target_file
    plot = args.plot

    from enstools.compression.api import evaluate
    evaluate(reference_file_path, target_file_path, plot=plot)


###############################
# Pruner
pruner_help_text = """
pruner:

Tool to prune a file up to a certain number of significant bits.

"""

def add_subparser_pruner(subparsers):
    import argparse
    subparser = subparsers.add_parser('prune', help=pruner_help_text,
                                      formatter_class=argparse.RawDescriptionHelpFormatter)
    subparser.add_argument("files", type=str, nargs="+",
                           help='List of files to compress. Multiple files and regex patterns are allowed.')
    subparser.add_argument("-o", '--output', type=str, dest="output", default=None, required=True)
    subparser.set_defaults(which='pruner')


def call_pruner(args):
    from enstools.compression.pruner import pruner
    file_paths = args.files
    output = args.output

    pruner(file_paths, output)


###############################

def add_subparsers(parser):
    """
    Add the different subparsers.
    """

    subparsers = parser.add_subparsers(help='Select between the different enstools utilities')

    # Create the parser for the "compressor" command
    add_subparser_compressor(subparsers)
    # Create the parser for the "analyzer" command
    add_subparser_analyzer(subparsers)
    # Create the parser for the "significand" command
    add_subparser_significand(subparsers)
    # Create the parser for the "evaluator" command
    add_subsubparser(subparsers)
    # Create the parser for the "pruner" command
    add_subparser_pruner(subparsers)
    # To add an additional subparser, just create a function like the ones above and add the call here.


def expand_paths(string: str):
    import glob
    from os.path import realpath
    """
    Small function to expand the file paths
    """
    files = glob.glob(string)
    return [realpath(f) for f in files]


###############################

def get_parser():
    # Create parser
    import argparse

    # Create the top-level parser
    parser = argparse.ArgumentParser()
    parser.set_defaults(which=None)

    # Add the different subparsers.
    # If willing to add new parser, this is the function where to look at.
    add_subparsers(parser)
    return parser


def main():
    """
    Entry point of the Command Line Interface for enstools-compression
    Returns
    -------

    """
    parser = get_parser()

    # Parse the command line arguments
    args = parser.parse_args()

    # Process options according to the selected option
    if args.which is None:
        parser.print_help()
        exit(0)
    elif args.which == "compressor":
        call_compressor(args)
    elif args.which == "analyzer":
        call_analyzer(args)
    elif args.which == "significand":
        call_significand(args)
    elif args.which == "evaluator":
        call_evaluator(args)
    elif args.which == "pruner":
        call_pruner(args)
    else:
        raise NotImplementedError
