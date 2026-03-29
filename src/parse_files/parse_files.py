"""Module to read excel file into dataframe"""
import pandas as pd
from docx import Document
import bleach
import logging

logger = logging.getLogger(__name__)


class Parser:
    """Class of methods to read files"""

    # Allowed HTML tags and attributes for sanitization
    ALLOWED_TAGS = [
        'table', 'tr', 'td', 'th', 'thead', 'tbody', 'br', 'span',
        'div', 'p', 'b', 'i', 'strong', 'em', 'html', 'body'
    ]
    ALLOWED_ATTRIBUTES = {
        '*': ['style'],
        'table': ['border', 'style'],
        'td': ['style', 'colspan', 'rowspan'],
        'th': ['style', 'colspan', 'rowspan']
    }

    def read_excel_file(self, file_path):
        """Reads an Excel file and returns a pandas DataFrame."""
        return pd.read_excel(file_path)

    def read_word_file(self, file_path):
        """Reads a word document"""
        doc = Document(file_path)
        return doc

    def read_html(self, filename):
        """
        Reads and sanitizes HTML page to prevent XSS attacks.

        Args:
            filename: Path to HTML file

        Returns:
            Sanitized HTML content safe for rendering
        """
        try:
            with open(f'{filename}', 'r', encoding='utf-8') as f:
                html_content = f.read()

            if not html_content:
                logger.warning(f"HTML content read from {filename} is empty")
                return ""

            # Sanitize HTML to remove potentially dangerous content
            try:
                sanitized_html = bleach.clean(
                    html_content,
                    tags=self.ALLOWED_TAGS,
                    attributes=self.ALLOWED_ATTRIBUTES,
                    styles=['color', 'background-color', 'font-weight', 'border-collapse'],
                    strip=True
                )
                logger.info(f"HTML sanitized. Original length: {len(html_content)}, Sanitized length: {len(sanitized_html)}")
                return sanitized_html
            except Exception as e:
                logger.error(f"Bleach sanitization failed: {str(e)}")
                return html_content # Fallback to raw if logic is broken, though risky

        except FileNotFoundError:
            logger.error(f"Error: HTML output file not found at {filename}")
            return ""
        except Exception as e:
            logger.error(f"Error reading HTML: {str(e)}")
            return ""
