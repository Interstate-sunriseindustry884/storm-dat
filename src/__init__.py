"""Module to initiate flask app"""
import os
import ssl
import logging
import secrets
from logging import StreamHandler, FileHandler
import certifi
from flask import Flask
from flask_cors import CORS
from src import routes
from src.utils.security_headers import add_security_headers


# Set SSL certificate path
os.environ["SSL_CERT_FILE"] = certifi.where()


def create_app(config_class=None):
    """Create a Flask application instance."""
    app = Flask(__name__)
    CORS(app)

    if config_class:
        app.config.from_object(config_class)

    # Configure SSL based on environment
    verify_ssl = config_class.get('VERIFY_SSL', True) if config_class else True
    if not verify_ssl:
        # Only disable SSL verification in development
        ssl._create_default_https_context = ssl._create_unverified_context  # pylint: disable=protected-access
        app.logger.warning("SSL certificate verification is DISABLED. This should only be used in development!")

    # Configure logging
    logging_level = logging.DEBUG if config_class and config_class.get('DEBUG') else logging.INFO
    logging.basicConfig(filename="log_file.log",
                        filemode="w", level=logging_level,
                        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler = StreamHandler()
    handler.setLevel(logging_level)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    app.logger.addHandler(handler)

    file_handler = FileHandler('log_file.log')
    file_handler.setLevel(logging_level)
    file_handler.setFormatter(formatter)
    app.logger.addHandler(file_handler)

    # Set secret key from environment variable or generate a secure one
    secret_key = os.environ.get('FLASK_SECRET_KEY')
    if secret_key:
        app.secret_key = secret_key
    else:
        # Generate a secure random secret key
        app.secret_key = secrets.token_hex(32)
        app.logger.warning(
            "FLASK_SECRET_KEY not set in environment. Using generated key. "
            "This will invalidate sessions on restart. "
            "Set FLASK_SECRET_KEY environment variable for production."
        )

    app.register_blueprint(routes.main)

    # Add security headers to all responses
    add_security_headers(app)

    # Initialize Whisper model at startup to avoid loading on every request
    app.logger.info("Loading Whisper model at startup...")
    try:
        import whisper
        app.whisper_model = whisper.load_model("medium")
        app.logger.info("Whisper model loaded successfully")
    except Exception as e:
        app.logger.error(f"Failed to load Whisper model: {e}")
        app.whisper_model = None

    return app
