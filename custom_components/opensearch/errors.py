"""Errors for the OpenSearch component."""

from homeassistant.exceptions import HomeAssistantError


class OSIntegrationException(HomeAssistantError):  # noqa: N818
    """Base class for OpenSearch exceptions."""


class OSIntegrationConnectionException(OSIntegrationException):
    """Base class for OpenSearch exceptions."""


class AuthenticationRequired(OSIntegrationConnectionException):
    """Cluster requires authentication."""


class InsufficientPrivileges(AuthenticationRequired):
    """Credentials are lacking the required privileges."""


class CannotConnect(OSIntegrationConnectionException):
    """Unable to connect to the cluster."""


class ServerError(CannotConnect):
    """Server Error."""


class ClientError(CannotConnect):
    """Client Error."""


class SSLError(CannotConnect):
    """Error related to SSL."""


class UntrustedCertificate(SSLError):
    """Received a untrusted certificate error."""


class UnsupportedVersion(OSIntegrationConnectionException):
    """Connected to an unsupported version of OpenSearch."""
