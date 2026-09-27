"""Jessie — convert JPG, JPEG and PNG images into Windows .ico files."""

from jessie.converter import (
    DEFAULT_SIZES,
    SUPPORTED_EXTENSIONS,
    ConversionResult,
    convert_many,
    convert_to_ico,
)
from jessie.exceptions import (
    EmptyBatchError,
    IconWriteError,
    InvalidSizeError,
    JessieError,
    OutputExistsError,
    SourceNotFoundError,
    UnsupportedFormatError,
)

__all__ = [
    "DEFAULT_SIZES",
    "SUPPORTED_EXTENSIONS",
    "ConversionResult",
    "EmptyBatchError",
    "IconWriteError",
    "InvalidSizeError",
    "JessieError",
    "OutputExistsError",
    "SourceNotFoundError",
    "UnsupportedFormatError",
    "convert_many",
    "convert_to_ico",
]
__version__ = "0.1.0"
