"""Dependency-injection hooks for API authentication and persistence."""


def get_current_user() -> str:
    """Resolve the authenticated user from the configured auth provider."""
    raise NotImplementedError("configure an authentication provider")


def get_database_session():
    """Provide a database session from the configured database adapter."""
    raise NotImplementedError("configure a database session provider")
