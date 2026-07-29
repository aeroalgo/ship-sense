class ConnectError(Exception):
    """Raised when a source connection cannot be established or maintained."""


class ConfigError(Exception):
    """Raised when collector configuration is invalid."""
