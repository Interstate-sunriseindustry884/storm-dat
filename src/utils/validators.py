"""Input validation utilities"""
import os
from ..config import config


class ValidationError(Exception):
    """Custom exception for validation errors"""
    pass


def validate_file_extension(filename, allowed_extensions):
    """
    Validate that a file has an allowed extension.

    Args:
        filename: The filename to check
        allowed_extensions: Set of allowed extensions (including dot, e.g., {'.docx', '.xlsx'})

    Returns:
        True if valid

    Raises:
        ValidationError if extension not allowed
    """
    if not filename:
        raise ValidationError("No filename provided")

    ext = os.path.splitext(filename)[1].lower()

    if ext not in allowed_extensions:
        allowed = ', '.join(sorted(allowed_extensions))
        raise ValidationError(f"File type '{ext}' not allowed. Allowed types: {allowed}")

    return True


def validate_file_size(file_obj, max_size_mb):
    """
    Validate that a file does not exceed maximum size.

    Args:
        file_obj: FileStorage object from request.files
        max_size_mb: Maximum size in megabytes

    Returns:
        True if valid

    Raises:
        ValidationError if file too large
    """
    if not file_obj:
        raise ValidationError("No file provided")

    # Seek to end to get size
    file_obj.seek(0, os.SEEK_END)
    size_bytes = file_obj.tell()
    file_obj.seek(0)  # Reset to beginning

    size_mb = size_bytes / (1024 * 1024)
    if size_mb > max_size_mb:
        raise ValidationError(f"File size {size_mb:.1f}MB exceeds maximum {max_size_mb}MB")

    return True


def validate_document_upload(file_obj):
    """
    Validate a document file (Word, Excel).

    Args:
        file_obj: FileStorage object from request.files

    Returns:
        True if valid

    Raises:
        ValidationError if validation fails
    """
    if not file_obj or not file_obj.filename:
        raise ValidationError("No file provided")

    validate_file_extension(file_obj.filename, config.ALLOWED_UPLOAD_EXTENSIONS)
    validate_file_size(file_obj, config.MAX_FILE_SIZE_MB['document'])

    return True


def validate_media_upload(file_obj, extension):
    """
    Validate a media file (audio, video).

    Args:
        file_obj: FileStorage object from request.files
        extension: Expected extension (e.g., '.wav', '.webm')

    Returns:
        True if valid

    Raises:
        ValidationError if validation fails
    """
    if not file_obj:
        raise ValidationError("No file provided")

    if extension not in config.ALLOWED_MEDIA_EXTENSIONS:
        raise ValidationError(f"Media type '{extension}' not allowed")

    validate_file_size(file_obj, config.MAX_FILE_SIZE_MB['media'])

    return True
