"""Module to define configuration variables"""
import os

ConfigOptionsWord = {
    "SECURITY_MARKINGS": ["CUI", "[CUI]", "CONTROLLED UNCLASSIFIED INFORMATION", "UNCLASSIFIED",
                          "Unclassified", "TOP SECRET", "SECRET", "CONFIDENTIAL"]
}

# Security configuration
ALLOWED_UPLOAD_EXTENSIONS = {'.docx', '.xlsx'}
ALLOWED_MEDIA_EXTENSIONS = {'.wav', '.webm'}
MAX_FILE_SIZE_MB = {
    'document': 50,  # Max size for Word/Excel files in MB
    'media': 500     # Max size for audio/video files in MB
}

# SSL configuration
VERIFY_SSL = {
    'development': False,  # Allow unverified SSL in dev
    'testing': True,
    'production': True
}

DevelopmentConfig = {
    "DEBUG": True,
    "Testing": False,
    "VERIFY_SSL": VERIFY_SSL['development']
}

TestingConfig = {
    "DEBUG": False,
    "TESTING": True,
    "VERIFY_SSL": VERIFY_SSL['testing']
}

ProductionConfig = {
    "DEBUG": False,
    "Testing": False,
    "VERIFY_SSL": VERIFY_SSL['production']
}
