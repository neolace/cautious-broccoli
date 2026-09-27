"""Domain exceptions raised by Jessie."""


class JessieError(Exception):
    """Base class for all Jessie errors."""


class UnsupportedFormatError(JessieError):
    """Raised when the input file is not a supported image type."""


class OutputExistsError(JessieError):
    """Raised when the output file exists and overwriting is disabled."""


class InvalidSizeError(JessieError):
    """Raised when a requested icon size is outside the ICO limits (1-256)."""


class SourceNotFoundError(JessieError, FileNotFoundError):
    """Raised when the source image does not exist."""


class IconWriteError(JessieError, OSError):
    """Raised when the icon or its parent directory cannot be written."""


class EmptyBatchError(JessieError, ValueError):
    """Raised when a batch is given no source images."""
