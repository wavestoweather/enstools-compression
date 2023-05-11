"""
This module provides functions to calculate compression ratio and file size metrics.
"""

import math
from pathlib import Path


def file_size(file_path: str) -> int:
    """
    Get the file size in bytes.

    Args:
        file_path: The path to the file.

    Returns:
        The file size in bytes.
    """
    return Path(file_path).stat().st_size


def convert_size(size_bytes: int) -> str:
    """
    Convert file size in bytes to a human-readable format.

    Args:
        size_bytes: The file size in bytes.

    Returns:
        A human-readable representation of the file size.
    """
    if size_bytes == 0:
        return "0B"
    size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
    index = int(math.floor(math.log(size_bytes, 1024)))
    power = math.pow(1024, index)
    size = round(size_bytes / power, 2)
    return f"{size} {size_name[index]}"


def readable_size(file_path: str) -> str:
    """
    Get the human-readable file size of a file.

    Args:
        file_path: The path to the file.

    Returns:
        A human-readable representation of the file size.
    """
    return convert_size(file_size(file_path))


def compression_ratio(path_to_original: str, path_to_compressed: str) -> float:
    """
    Calculate the compression ratio of the original file to the compressed file.

    Args:
        path_to_original: The path to the original file.
        path_to_compressed: The path to the compressed file.

    Returns:
        The compression ratio as a float.
    """
    original_size = file_size(path_to_original)
    compressed_size = file_size(path_to_compressed)
    return original_size / compressed_size
