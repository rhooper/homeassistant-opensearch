"""OpenSearch Gateway."""

from __future__ import annotations

import ssl
from collections import OrderedDict
from contextlib import contextmanager
from dataclasses import dataclass
from types import MappingProxyType
from typing import TYPE_CHECKING, Any

import opensearchpy
from homeassistant.util.ssl import client_context
from opensearchpy import AsyncOpenSearch
from opensearchpy.helpers import async_streaming_bulk

from custom_components.opensearch.const import OS_CHECK_PERMISSIONS_DATASTREAM
from custom_components.opensearch.encoder import Serializer
from custom_components.opensearch.errors import (
    AuthenticationRequired,
    CannotConnect,
    InsufficientPrivileges,
    ServerError,
    UntrustedCertificate,
)
from custom_components.opensearch.os_gateway import (
    GatewaySettings,
    OpenSearchGateway,
)

from .logger import LOGGER as BASE_LOGGER
from .logger import async_log_enter_exit_debug

if TYPE_CHECKING:  # pragma: no cover
    from collections.abc import AsyncGenerator
    from logging import Logger


@dataclass
class Gateway8Settings(GatewaySettings):
    """OpenSearch Gateway settings object."""

    def to_client(self) -> AsyncOpenSearch:
        """Create an OpenSearch client from the settings."""

        settings: dict[str, Any] = {
            "hosts": [self.url],
            "serializer": Serializer(),
            "timeout": self.request_timeout,
        }

        if self.url.startswith("https"):
            context: ssl.SSLContext = client_context()

            if not self.verify_certs:
                context.check_hostname = False
                context.verify_mode = ssl.CERT_NONE
            else:
                context.check_hostname = self.verify_hostname
                context.verify_mode = ssl.CERT_REQUIRED

                if self.ca_certs:
                    context.load_verify_locations(cafile=self.ca_certs)

            settings["ssl_context"] = context

        if self.username:
            settings["http_auth"] = (self.username, self.password)

        return AsyncOpenSearch(**settings)


class OpenSearch2Gateway(OpenSearchGateway):
    """Encapsulates OpenSearch operations."""

    _settings: Gateway8Settings
    _client: AsyncOpenSearch

    def __init__(
        self,
        gateway_settings: Gateway8Settings,
        log: Logger = BASE_LOGGER,
    ) -> None:
        """Initialize the OpenSearch Gateway."""

        super().__init__(
            gateway_settings=gateway_settings,
            log=log,
        )

        self._settings = gateway_settings
        self._client = self._settings.to_client()

    async def async_init(self) -> None:
        """Initialize the OpenSearch Gateway."""

        await super().async_init()

    @classmethod
    async def async_init_then_stop(
        cls,
        url: str,
        username: str | None = None,
        password: str | None = None,
        verify_certs: bool = True,
        verify_hostname: bool = True,
        ca_certs: str | None = None,
        request_timeout: int = 30,
        minimum_privileges: MappingProxyType[str, Any] = OS_CHECK_PERMISSIONS_DATASTREAM,
        log: Logger = BASE_LOGGER,
    ) -> None:
        """Initialize the gateway and then stop it."""

        gateway = cls(
            Gateway8Settings(
                url=url,
                username=username,
                password=password,
                verify_certs=verify_certs,
                verify_hostname=verify_hostname,
                ca_certs=ca_certs,
                request_timeout=request_timeout,
                minimum_privileges=minimum_privileges,
            ),
            log=log,
        )

        try:
            await gateway.async_init()
        finally:
            await gateway.stop()

    @property
    def client(self) -> AsyncOpenSearch:
        """Return the underlying OpenSearch Client."""

        return self._client

    @property
    def settings(self) -> Gateway8Settings:
        """Return the settings."""

        return self._settings

    @async_log_enter_exit_debug
    async def info(self) -> dict:
        """Retrieve info about the connected OpenSearch cluster."""

        with self._error_converter(msg="Error retrieving cluster info from OpenSearch"):
            return await self.client.info()

    @async_log_enter_exit_debug
    async def ping(self) -> bool:
        """Ping the OpenSearch cluster. Raises only on Authentication issues."""
        try:
            await self.info()

        except AuthenticationRequired:
            self._previous_ping = False

            self._logger.debug("Authentication error pinging OpenSearch", exc_info=True)

            raise
        except:  # noqa: E722
            self._previous_ping = False

            self._logger.debug("Error pinging OpenSearch", exc_info=True)

            return False
        else:
            self._previous_ping = True

            return True

    @async_log_enter_exit_debug
    async def has_security(self) -> bool:
        """Check if the cluster has security enabled."""
        return True

    @async_log_enter_exit_debug
    async def has_privileges(self, privileges) -> bool:
        """Check if the user has the required privileges.

        OpenSearch does not have a _has_privileges API equivalent.
        We skip privilege checking and rely on operation-level errors instead.
        """
        return True

    @async_log_enter_exit_debug
    async def get_index_template(self, name, ignore: list[int] | None = None) -> dict:
        """Retrieve an index template."""
        with self._error_converter(msg="Error retrieving index template"):
            params = {}
            if ignore:
                params["ignore"] = ignore
            return await self.client.indices.get_index_template(name=name, params=params)

    @async_log_enter_exit_debug
    async def put_index_template(self, name, body) -> dict:
        """Create an index template."""
        with self._error_converter(msg="Error creating index template"):
            return await self.client.indices.put_index_template(name=name, body=body)

    @async_log_enter_exit_debug
    async def get_datastream(self, datastream: str) -> dict:
        """Retrieve datastreams."""
        with self._error_converter(msg="Error retrieving datastreams"):
            return await self.client.indices.get_data_stream(name=datastream)

    @async_log_enter_exit_debug
    async def rollover_datastream(self, datastream: str) -> dict:
        """Rollover an index."""
        with self._error_converter(msg="Error rolling over datastream"):
            return await self.client.indices.rollover(alias=datastream)

    @async_log_enter_exit_debug
    async def bulk(self, actions: AsyncGenerator[dict[str, Any], Any]) -> None:
        """Perform a bulk operation."""

        with self._error_converter("Error performing bulk operation"):
            count = 0
            okcount = 0
            errcount = 0
            async for ok, result in async_streaming_bulk(
                client=self.client,
                actions=actions,
                max_retries=3,
                raise_on_error=False,
                yield_ok=True,
            ):
                count += 1
                action, outcome = result.popitem()
                if not ok:
                    errcount += 1
                    self._logger.error("failed to %s, error information: %s", action, outcome)
                else:
                    okcount += 1

            if count > 0:
                if errcount == 0:
                    self._logger.info("Successfully published %d documents", okcount)
                elif errcount > 0:
                    self._logger.error("Failed to publish %d of %d documents", errcount, count)
            else:
                self._logger.debug("Publish skipped, no new events to publish.")

    async def stop(self) -> None:
        """Stop the gateway."""
        if self._client is not None:
            await self.client.close()

    # Functions for handling errors

    @contextmanager
    def _error_converter(self, msg: str | None = None):
        """Convert an internal error from the opensearch package into one of our own."""

        def append_msg(append_msg: str) -> str:
            """Append the exception's message to the caller's message."""
            if msg is None:
                return append_msg

            return f"{msg}. {append_msg}"

        def append_cause(err: opensearchpy.TransportError, msg: str) -> str:
            """Append the root cause to the error message."""
            if not hasattr(err, "info") or err.info is None:
                return msg

            error_details = err.info if isinstance(err.info, dict) else {}
            if "error" in error_details:
                error_details = error_details["error"]

            specifics: OrderedDict = OrderedDict()
            if isinstance(error_details, dict):
                if "type" in error_details:
                    specifics["type"] = error_details["type"]

                if "reason" in error_details:
                    specifics["reason"] = error_details["reason"]

            # join specifics into a string with key: value pairs
            specific_str = "; ".join(f"{k}={v}" for k, v in specifics.items())

            return f"{msg} ({specific_str})" if specific_str else msg

        try:
            yield

        except opensearchpy.AuthenticationException as err:
            raise AuthenticationRequired(
                append_cause(err, append_msg("Authentication error connecting to OpenSearch"))
            ) from err

        except opensearchpy.AuthorizationException as err:
            raise InsufficientPrivileges(
                append_cause(err, append_msg("Authorization error connecting to OpenSearch"))
            ) from err

        except opensearchpy.ConnectionTimeout as err:
            raise ServerError(append_msg("Connection timeout connecting to OpenSearch")) from err

        except opensearchpy.SSLError as err:
            raise UntrustedCertificate(append_msg(f"Could not complete TLS Handshake. {err.error}")) from err

        except opensearchpy.ConnectionError as err:
            # Check if the underlying cause is an SSL certificate error
            # opensearchpy stores the original exception in err.info
            underlying = err.info
            if isinstance(underlying, ssl.SSLCertVerificationError) or (
                hasattr(underlying, "certificate_error")
            ):
                raise UntrustedCertificate(
                    append_msg(f"Could not complete TLS Handshake. {err.error}")
                ) from err
            raise CannotConnect(append_msg(f"Error connecting to OpenSearch. {err.error}")) from err

        except opensearchpy.TransportError as err:
            if hasattr(err, "status_code") and isinstance(err.status_code, int) and err.status_code >= 400:
                raise ServerError(append_msg(f"Error in request to OpenSearch: {err.status_code}")) from err
            else:
                raise CannotConnect(
                    append_msg(f"Unknown transport error connecting to OpenSearch: {err.error}")
                ) from err

        except Exception:
            BASE_LOGGER.exception("Unknown and unexpected exception occurred.")
            raise
