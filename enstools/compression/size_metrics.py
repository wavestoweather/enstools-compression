import math
from pathlib import Path


###############################################################
# Functions to calculate compression ratio from files
#
def file_size(file_path: str) -> int:
    """
    Get the file size in bytes.
    """
    return Path(file_path).stat().st_size


def convert_size(size_bytes: int) -> str:
    if size_bytes == 0:
        return "0B"
    size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return "%s %s" % (s, size_name[i])


def readable_size(file_path: str) -> str:
    return convert_size(file_size(file_path))


def compression_ratio(path_to_original: str, path_to_compressed: str) -> float:
    original_size = file_size(path_to_original)
    compressed_size = file_size(path_to_compressed)
    return original_size / compressed_size
