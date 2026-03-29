"""HTTP security headers middleware"""


def add_security_headers(app):
    """
    Add security headers to all HTTP responses.

    This provides defense-in-depth against various web attacks including:
    - XSS (Cross-Site Scripting)
    - Clickjacking
    - MIME type sniffing
    - Man-in-the-middle attacks (in production)

    Args:
        app: Flask application instance

    Returns:
        Flask application with security headers configured
    """

    @app.after_request
    def set_security_headers(response):
        """Add security headers to response"""

        # Prevent MIME type sniffing (forces browser to respect Content-Type)
        response.headers['X-Content-Type-Options'] = 'nosniff'

        # Prevent clickjacking by disallowing framing
        response.headers['X-Frame-Options'] = 'DENY'

        # XSS protection for legacy browsers (most modern browsers ignore this)
        response.headers['X-XSS-Protection'] = '1; mode=block'

        # Control referrer information sent with requests
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'

        # Permissions policy - restrict access to sensitive APIs
        response.headers['Permissions-Policy'] = (
            'geolocation=(), '  # No geolocation
            'microphone=(self), '  # Microphone only for same origin (needed for recording)
            'camera=(self)'  # Camera only for same origin (needed for recording)
        )

        # HTTPS enforcement (production only)
        # Instructs browsers to only connect via HTTPS for 1 year
        # Commented out to support HTTP-only production deployment
        # if not app.config.get('DEBUG', False):
        #     response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'

        # Content Security Policy (CSP)
        # Note: 'unsafe-inline' is used for inline styles/scripts in templates
        # Consider moving to external files for stricter CSP
        csp_directives = [
            "default-src 'self'",
            "script-src 'self' 'unsafe-inline' https://code.jquery.com https://cdn.jsdelivr.net https://stackpath.bootstrapcdn.com",
            "style-src 'self' 'unsafe-inline' https://stackpath.bootstrapcdn.com",
            "img-src 'self' data: blob:",  # blob: needed for video preview
            "media-src 'self' blob:",  # blob: needed for recorded media
            "font-src 'self' data:",
            "connect-src 'self'",
            "frame-ancestors 'none'",
            "base-uri 'self'",
            "form-action 'self'",
            "object-src 'none'"  # No Flash, Java, etc.
        ]
        response.headers['Content-Security-Policy'] = '; '.join(csp_directives)

        return response

    return app
