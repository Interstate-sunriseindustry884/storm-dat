"""Security utilities for file handling and sanitization"""
import os
import html
from werkzeug.utils import secure_filename as werkzeug_secure_filename


def sanitize_filename(filename):
    """
    Sanitize a filename to prevent path traversal attacks.

    Args:
        filename: The original filename from user input

    Returns:
        A safe filename string with no path components
    """
    if not filename:
        return None

    # Use werkzeug's secure_filename to remove path components
    safe_name = werkzeug_secure_filename(filename)

    # Additional check: ensure no path separators remain
    safe_name = os.path.basename(safe_name)

    return safe_name if safe_name else None


def sanitize_html_content(content):
    """
    Sanitize HTML content to prevent XSS attacks.

    Args:
        content: HTML string content

    Returns:
        Escaped HTML content safe for display
    """
    if not content:
        return ""

    # Use html.escape to convert special characters to HTML entities
    return html.escape(str(content))
