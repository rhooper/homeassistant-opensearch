"""Tests for the OpenSearch Gateway."""

# noqa: F401 # pylint: disable=redefined-outer-name

import os
import ssl
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import opensearchpy
import pytest
from aiohttp import client_exceptions
from custom_components.opensearch.const import OS_CHECK_PERMISSIONS_DATASTREAM
from custom_components.opensearch.datastreams.index_template import (
    index_template_definition,
)
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
from opensearchpy import AsyncOpenSearch

from tests import const as testconst


def self_signed_tls_error():
    """Return a self-signed certificate error."""
    connection_key = MagicMock()
    connection_key.host = "mock_os_integration"
    connection_key.port = 9200
    connection_key.is_ssl = True

    certificate_error = ssl.SSLCertVerificationError()
    certificate_error.verify_code = 19
    certificate_error.verify_message = "'self-signed certificate in certificate chain'"
    certificate_error.library = "SSL"
    certificate_error.reason = "CERTIFICATE_VERIFY_FAILED"
    certificate_error.strerror = "[SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: self-signed certificate in certificate chain (_ssl.c:1000)"
    certificate_error.errno = 1

    return client_exceptions.ClientConnectorCertificateError(
        connection_key=connection_key, certificate_error=certificate_error
    )


def mock_os_exception(exception, message="None"):
    """Return an AsyncMock that mocks an OpenSearch API response."""

    if issubclass(exception, opensearchpy.AuthenticationException):
        return AsyncMock(side_effect=exception(401, message, {}))

    if issubclass(exception, opensearchpy.AuthorizationException):
        return AsyncMock(side_effect=exception(403, message, {}))

    if issubclass(exception, opensearchpy.ConnectionTimeout):
        return AsyncMock(side_effect=exception("TIMEOUT", message, None))

    if issubclass(exception, opensearchpy.SSLError):
        return AsyncMock(side_effect=exception("SSL_ERROR", message, Exception(message)))

    if issubclass(exception, opensearchpy.ConnectionError):
        return AsyncMock(side_effect=exception("N/A", message, Exception(message)))

    if issubclass(exception, opensearchpy.TransportError):
        return AsyncMock(side_effect=exception(500, message, {}))

    return AsyncMock(side_effect=exception())


def mock_os_response(body):
    """Return an AsyncMock that mocks an OpenSearch API response."""
    return AsyncMock(return_value=body)


@pytest.fixture
def gateway_settings() -> GatewaySettings:
    """Return a GatewaySettings instance."""
    return GatewaySettings(
        url=testconst.CONFIG_ENTRY_DATA_URL,
        username="username",
        password="password",
        verify_certs=True,
        ca_certs=None,
        request_timeout=30,
    )


@pytest.fixture
async def gateway_mock_shared(gateway_settings) -> OpenSearchGateway:
    """Return a mock OpenSearch client."""
    gateway_settings.to_client = MagicMock(return_value=MagicMock(AsyncOpenSearch))

    gateway = OpenSearchGateway(gateway_settings=gateway_settings)

    gateway._client.security = MagicMock()

    gateway._client.indices = MagicMock()
    gateway._client.indices.get_index_template = mock_os_response(
        {
            "index_templates": [
                {
                    "name": "datastream_metrics",
                    "index_template": {"version": index_template_definition.get("version", 0)},
                }
            ]
        }
    )
    gateway._client.indices.put_index_template = mock_os_response({})
    gateway._client.indices.get_data_stream = mock_os_response(
        {
            "data_streams": [
                {
                    "name": "metrics-homeassistant.sensor-default",
                },
                {
                    "name": "metrics-homeassistant.counter-default",
                },
            ]
        }
    )
    gateway._client.indices.rollover = mock_os_response(
        {
            "acknowledged": True,
            "shards_acknowledged": True,
            "old_index": ".ds-metrics-homeassistant.domain-default-2024.12.19-000001",
            "new_index": ".ds-metrics-homeassistant.domain-default-2025.01.10-000002",
            "rolled_over": True,
            "dry_run": False,
            "lazy": False,
            "conditions": {},
        }
    )

    return gateway


@pytest.fixture
async def gateway_mock_stateful(gateway_mock_shared: OpenSearchGateway, mock_logger) -> OpenSearchGateway:
    """Return a mock OpenSearch client for a Stateful cluster."""

    gateway_mock_shared._client.info = mock_os_response(testconst.CLUSTER_INFO_2DOT17_RESPONSE_BODY)

    gateway_mock_shared._logger = mock_logger

    return gateway_mock_shared


class Test_Initialization:
    """Initialization tests for the OpenSearch Gateway."""

    async def test_init_basic_auth(self) -> None:
        """Test initializing a gateway with basic authentication."""
        gateway = OpenSearchGateway(
            gateway_settings=GatewaySettings(
                url=testconst.CONFIG_ENTRY_DATA_URL,
                username="username",
                password="password",
            )
        )

        assert gateway._client.transport.kwargs.get("http_auth") == (
            "username",
            "password",
        ) or hasattr(gateway._client, "_http_auth")

    async def test_init_no_auth(self) -> None:
        """Test initializing a gateway with no authentication."""
        gateway = OpenSearchGateway(
            gateway_settings=GatewaySettings(
                url=testconst.CONFIG_ENTRY_DATA_URL_INSECURE,
            )
        )

        assert gateway._client is not None

    @pytest.mark.parametrize(
        (
            "verify_certs",
            "verify_hostname",
            "expected_verify_mode",
            "expected_verify_hostname",
        ),
        [
            (True, True, ssl.CERT_REQUIRED, True),
            (True, False, ssl.CERT_REQUIRED, False),
            (False, True, ssl.CERT_NONE, False),
            (False, False, ssl.CERT_NONE, False),
        ],
        ids=[
            "Verify Certs and Verify Hostname",
            "Verify Certs and Don't Verify Hostname",
            "No Certs and Ignore Verify Hostname",
            "No Certs and Don't Verify Hostname",
        ],
    )
    async def test_init_tls(
        self,
        verify_certs,
        verify_hostname,
        expected_verify_mode,
        expected_verify_hostname,
    ) -> None:
        """Test initializing a gateway with various TLS settings."""

        gateway = OpenSearchGateway(
            gateway_settings=GatewaySettings(
                url=testconst.CONFIG_ENTRY_DATA_URL,
                verify_certs=verify_certs,
                verify_hostname=verify_hostname,
            )
        )

        # OpenSearch client stores ssl_context in transport kwargs
        ssl_context = gateway._client.transport.kwargs.get("ssl_context")

        assert ssl_context.check_hostname == expected_verify_hostname
        assert ssl_context.verify_mode == expected_verify_mode

    async def test_init_tls_custom_ca(self) -> None:
        """Test initializing a gateway with TLS and custom ca cert."""

        # cert is located in "certs/http_ca.crt" relative to this file, get the absolute path
        current_directory = os.path.dirname(os.path.abspath(__file__))

        gateway = OpenSearchGateway(
            gateway_settings=GatewaySettings(
                url=testconst.CONFIG_ENTRY_DATA_URL,
                verify_certs=True,
                verify_hostname=True,
                ca_certs=f"{current_directory}/certs/http_ca.crt",
            )
        )

        ssl_context = gateway._client.transport.kwargs.get("ssl_context")

        assert any(
            cert["serialNumber"] == "25813FA4F725F5566FCF014C0B8B0973E710DF90"
            for cert in ssl_context.get_ca_certs()
        )

    async def test_async_init(self, gateway_mock_stateful) -> None:
        """Test the async initialization with proper permissions on a supported version."""

        assert await gateway_mock_stateful.async_init() is None

    async def test_async_init_unauthenticated(self, gateway_mock_stateful) -> None:
        """Test the async_init method with an unauthenticated session."""

        gateway_mock_stateful._client.info = mock_os_exception(opensearchpy.AuthenticationException)

        with pytest.raises(AuthenticationRequired):
            await gateway_mock_stateful.async_init()

    async def test_async_init_ssl_error(self, gateway_mock_stateful):
        """Test async_init when there is a TLS Certificate issue."""

        gateway_mock_stateful._client.info = mock_os_exception(opensearchpy.SSLError)

        with pytest.raises(UntrustedCertificate):
            await gateway_mock_stateful.async_init()

    async def test_async_init_unauthorized(self, gateway_mock_stateful) -> None:
        """Test the async_init method unauthorized."""

        gateway_mock_stateful._client.info = mock_os_exception(opensearchpy.AuthorizationException)

        with pytest.raises(InsufficientPrivileges):
            assert await gateway_mock_stateful.async_init() is None

    async def test_async_init_unreachable(self, gateway_mock_stateful) -> None:
        """Test the async_init method with unreachable OpenSearch."""

        gateway_mock_stateful._client.info = mock_os_exception(opensearchpy.ConnectionTimeout)

        with pytest.raises(CannotConnect):
            assert await gateway_mock_stateful.async_init() is None


class Test_Public_Functions:
    """Public function tests for the OpenSearch Gateway."""

    async def test_ping(self, gateway_mock_stateful) -> None:
        """Test the ping method."""
        assert await gateway_mock_stateful.ping() is True

    async def test_ping_fail(self, gateway_mock_stateful) -> None:
        """Test the ping method."""
        gateway_mock_stateful._client.info = mock_os_exception(opensearchpy.AuthenticationException)
        with pytest.raises(AuthenticationRequired):
            await gateway_mock_stateful.ping()

        gateway_mock_stateful._client.info = mock_os_exception(opensearchpy.AuthorizationException)
        with pytest.raises(AuthenticationRequired):
            await gateway_mock_stateful.ping()

        gateway_mock_stateful._client.info = mock_os_exception(opensearchpy.ConnectionTimeout)
        assert await gateway_mock_stateful.ping() is False

    async def test_has_security(self, gateway_mock_stateful):
        """Test the has_security method always returns True."""

        assert await gateway_mock_stateful.has_security() is True

    async def test_get_datastream(self, gateway_mock_stateful):
        """Test the get_datastream method."""

        await gateway_mock_stateful.get_datastream("metrics-homeassistant.*")

        gateway_mock_stateful._client.indices.get_data_stream.assert_called_once_with(
            name="metrics-homeassistant.*"
        )

    async def test_rollover_datastream(self, gateway_mock_stateful):
        """Test the get_datastream method."""

        await gateway_mock_stateful.rollover_datastream("metrics-homeassistant.sensor-default")

        gateway_mock_stateful._client.indices.rollover.assert_called_once_with(
            alias="metrics-homeassistant.sensor-default"
        )

    async def test_has_privileges(self, gateway_mock_stateful):
        """Test the has_privileges method always returns True (OpenSearch has no _has_privileges API)."""
        privileges = OS_CHECK_PERMISSIONS_DATASTREAM

        assert await gateway_mock_stateful.has_privileges(privileges) is True

    async def test_get_index_template(self, gateway_mock_stateful):
        """Test the get_index_template method."""

        await gateway_mock_stateful.get_index_template("datastream_metrics")

        gateway_mock_stateful._client.indices.get_index_template.assert_called_once_with(
            name="datastream_metrics", params={}
        )

    async def test_get_index_template_ignore_404(self, gateway_mock_stateful):
        """Test the get_index_template method when the template is missing."""

        gateway_mock_stateful._client.indices.get_index_template = mock_os_response({"index_templates": []})

        assert await gateway_mock_stateful.get_index_template("datastream_metrics", ignore=[404]) == {
            "index_templates": []
        }

        gateway_mock_stateful._client.indices.get_index_template.assert_called_with(
            name="datastream_metrics", params={"ignore": [404]}
        )

    async def test_put_index_template(self, gateway_mock_stateful):
        """Test the put_index_template method."""

        await gateway_mock_stateful.put_index_template("datastream_metrics", index_template_definition)

        gateway_mock_stateful._client.indices.put_index_template.assert_called_once_with(
            name="datastream_metrics", body=index_template_definition
        )

    async def test_bulk(self, gateway_mock_stateful):
        """Test the bulk method."""

        async def yield_doc():
            yield AsyncMock()
            yield AsyncMock()
            yield AsyncMock()

        async def yield_response():
            yield (
                True,  # OK
                {
                    "action": "create",
                    "outcome": {
                        "_index": ".ds-metrics-homeassistant.counter-default-2025.01.12-000001",
                        "_id": "oEmJWJQB7GOvwEliMbKW",
                        "_version": 1,
                        "result": "created",
                        "_shards": {"total": 2, "successful": 1, "failed": 0},
                        "_seq_no": 0,
                        "_primary_term": 1,
                        "status": 201,
                    },
                },
            )

        with patch("custom_components.opensearch.os_gateway.async_streaming_bulk") as mock_streaming_bulk:
            mock_streaming_bulk.side_effect = [yield_response()]

            await gateway_mock_stateful.bulk(actions=yield_doc())

            assert mock_streaming_bulk.call_count == 1
            gateway_mock_stateful._logger.info.assert_called_once_with(
                "Successfully published %d documents", 1
            )

    async def test_bulk_nothing_to_do(self, gateway_mock_stateful):
        """Test the bulk method."""

        with patch("custom_components.opensearch.os_gateway.async_streaming_bulk") as mock_streaming_bulk:
            await gateway_mock_stateful.bulk(actions=[])

            assert mock_streaming_bulk.call_count == 1
            gateway_mock_stateful._logger.debug.assert_called_once_with(
                "Publish skipped, no new events to publish."
            )

    class Test_Check_Connection:
        """Tests for the check_connection method."""

        @pytest.fixture(name="gateway")
        async def gateway_fixture(self, gateway_settings, mock_logger):
            """Return a gateway instance."""
            gateway = OpenSearchGateway(gateway_settings=gateway_settings)

            gateway._logger = mock_logger

            try:
                yield gateway
            finally:
                await gateway.stop()

        async def test_check_connection_first_time_success(self, gateway) -> None:
            """Test check_connection method when connecting for the first time successfully."""
            gateway.ping = AsyncMock(return_value=True)

            result = await gateway.check_connection()

            assert result is True
            gateway._logger.info.assert_called_once_with("Connection to OpenSearch is established.")
            gateway._logger.error.assert_not_called()

        async def test_check_connection_first_time_failure(self, gateway) -> None:
            """Test check_connection method when connecting for the first time fails."""
            gateway.ping = AsyncMock(return_value=False)

            result = await gateway.check_connection()

            assert result is False
            gateway._logger.error.assert_called_once_with("Failed to establish connection to OpenSearch.")
            gateway._logger.info.assert_not_called()

        async def test_check_connection_maintained(self, gateway) -> None:
            """Test check_connection method when connection is maintained."""
            gateway._previous_ping = True
            gateway.ping = AsyncMock(return_value=True)

            result = await gateway.check_connection()

            assert result is True
            gateway._logger.debug.assert_called_once_with("Connection to OpenSearch is still available.")

        async def test_check_connection_lost(self, gateway) -> None:
            """Test check_connection method when connection is lost."""
            gateway._previous_ping = True
            gateway.ping = AsyncMock(return_value=False)

            result = await gateway.check_connection()

            assert result is False
            gateway._logger.error.assert_called_once_with("Connection to OpenSearch has been lost.")
            gateway._logger.debug.assert_not_called()

        async def test_check_connection_down(self, gateway) -> None:
            """Test check_connection method when connection is still down."""
            gateway._previous_ping = False
            gateway.ping = AsyncMock(return_value=False)

            result = await gateway.check_connection()

            assert result is False
            gateway._logger.debug.assert_called_once_with("Connection to OpenSearch is still down.")

        async def test_check_connection_reestablished(self, gateway) -> None:
            """Test check_connection method when connection is reestablished."""
            gateway._previous_ping = False
            gateway.ping = AsyncMock(return_value=True)

            result = await gateway.check_connection()

            assert result is True
            gateway._logger.info.assert_called_once_with("Connection to OpenSearch has been reestablished.")


class Test_Exception_Conversion:
    """Test the conversion of OpenSearch exceptions to custom exceptions."""

    @pytest.mark.parametrize(
        ("exception", "expected_exception", "message"),
        [
            (
                opensearchpy.TransportError(500, "Test Case", {}),
                ServerError,
                "Error in request to OpenSearch",
            ),
            (
                opensearchpy.AuthenticationException(401, "Test Case", {}),
                AuthenticationRequired,
                "Authentication error connecting to OpenSearch",
            ),
            (
                opensearchpy.AuthorizationException(403, "Test Case", {}),
                InsufficientPrivileges,
                "Authorization error connecting to OpenSearch",
            ),
            (
                opensearchpy.ConnectionTimeout("TIMEOUT", "Test Case", None),
                CannotConnect,
                "Connection timeout connecting to OpenSearch",
            ),
            (
                opensearchpy.SSLError("SSL_ERROR", "Test Case", Exception("Test Case")),
                UntrustedCertificate,
                "Could not complete TLS Handshake",
            ),
            (
                opensearchpy.ConnectionError("N/A", "Test Case", Exception("Test Case")),
                CannotConnect,
                "Error connecting to OpenSearch",
            ),
            (
                opensearchpy.TransportError("N/A", "Test Case", {}),
                CannotConnect,
                "Unknown transport error connecting to OpenSearch",
            ),
            (Exception(), Exception, ""),
        ],
        ids=[
            "TransportError(500) to ServerError",
            "AuthenticationException to AuthenticationRequired",
            "AuthorizationException to InsufficientPrivileges",
            "ConnectionTimeout to CannotConnect",
            "SSLError to UntrustedCertificate",
            "ConnectionError to CannotConnect",
            "TransportError to CannotConnect",
            "Exception to Exception",
        ],
    )
    async def test_error_conversion_bulk_index_error(
        self, gateway_mock_shared, exception, expected_exception, message
    ):
        """Test the error converter handling of a bulk index error."""
        with pytest.raises(expected_exception, match=message), gateway_mock_shared._error_converter():
            raise exception


class Test_Errors_e2e:
    """Test the error handling of aiohttp errors through the OpenSearch Client and Gateway."""

    @pytest.fixture
    async def gateway(self, gateway_settings, os_mock_builder):
        """Return a gateway instance."""

        os_mock_builder.as_opensearch_2_17().with_correct_permissions()
        gateway = OpenSearchGateway(gateway_settings=gateway_settings)
        os_mock_builder.reset()

        try:
            yield gateway
        finally:
            await gateway.stop()

    @pytest.mark.parametrize(
        ("status_code", "expected_exception"),
        [
            (404, CannotConnect),
            (401, AuthenticationRequired),
            (403, InsufficientPrivileges),
            (500, CannotConnect),
            (400, CannotConnect),
            (502, CannotConnect),
            (503, CannotConnect),
        ],
        ids=[
            "404 to CannotConnect",
            "401 to AuthenticationRequired",
            "403 to InsufficientPrivileges",
            "500 to CannotConnect",
            "400 to CannotConnect",
            "502 to CannotConnect",
            "503 to CannotConnect",
        ],
    )
    async def test_http_error_codes(
        self,
        gateway: OpenSearchGateway,
        os_mock_builder,
        status_code: int,
        expected_exception: Any,
    ) -> None:
        """Test the error converter."""
        os_mock_builder.with_server_error(status=status_code)

        with pytest.raises(expected_exception):
            await gateway.info()

    @pytest.mark.parametrize(
        ("aiohttp_exception", "expected_exception"),
        [
            (client_exceptions.ServerConnectionError(), CannotConnect),
            # child exceptions of ServerConnectionError
            (
                client_exceptions.ServerFingerprintMismatch(
                    expected=b"expected", got=b"actual", host="host", port=9200
                ),
                CannotConnect,
            ),
            (client_exceptions.ServerDisconnectedError(), CannotConnect),
            (client_exceptions.ServerTimeoutError(), CannotConnect),
            (client_exceptions.ClientError(), CannotConnect),
            # child exceptions of ClientError
            (
                client_exceptions.ClientResponseError(request_info=MagicMock(), history=MagicMock()),
                CannotConnect,
            ),
            (client_exceptions.ClientPayloadError(), CannotConnect),
            (client_exceptions.ClientConnectionError(), CannotConnect),
            (self_signed_tls_error(), UntrustedCertificate),
        ],
        ids=[
            "ServerConnectionError to CannotConnect",
            "ServerFingerprintMismatch to CannotConnect",
            "ServerDisconnectedError to CannotConnect",
            "ServerTimeoutError to CannotConnect",
            "ClientError to CannotConnect",
            "ClientResponseError to CannotConnect",
            "ClientPayloadError to CannotConnect",
            "ClientConnectionError to CannotConnect",
            "SSLCertVerificationError to UntrustedCertificate",
        ],
    )
    async def test_aiohttp_web_exceptions(
        self, aiohttp_exception, expected_exception, gateway, os_mock_builder
    ) -> None:
        """Test the error converter."""

        os_mock_builder.with_server_error(exc=aiohttp_exception)

        with pytest.raises(expected_exception):
            await gateway.info()

        await gateway.stop()
