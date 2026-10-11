"""HTTP middleware registration hooks."""


def configure_middleware(app: object) -> None:
    """Attach CORS, security headers, and request-size limits to the app."""
    raise NotImplementedError("configure API middleware and deployment policy")
