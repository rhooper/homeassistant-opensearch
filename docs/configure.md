# Configuration

## Gather OpenSearch details

You will need the following details to configure the OpenSearch integration:

1. The URL of your OpenSearch instance
2. Credentials to access the OpenSearch instance (if required)
3. The SSL certificate authority (CA) file, if you are using a custom CA not trusted by the host system

### Credentials

You must provide credentials if your OpenSearch instance is secured. Provide a username and password to authenticate with your OpenSearch cluster.

Use the following command to create a dedicated user for the Home Assistant component:

=== "curl"
    ```bash
    curl https://localhost:9200/_plugins/_security/api/internalusers/hass_writer \ # (1)
      -X PUT \
      -H "Content-Type: application/json" \
      -u admin:admin \ # (2)
      -d'
      {
        "password": "your_secure_password",
        "opendistro_security_roles": ["all_access"],
        "backend_roles": ["hass_writer"]
      }
    '
    ```

    1. Replace `https://localhost:9200` with the URL of your OpenSearch instance.
    2. Replace `admin:admin` with your OpenSearch admin credentials.

=== "OpenSearch Dashboards Dev Tools"
    ```
    PUT _plugins/_security/api/internalusers/hass_writer
    {
      "password": "your_secure_password",
      "opendistro_security_roles": ["all_access"],
      "backend_roles": ["hass_writer"]
    }
    ```

Read the [OpenSearch documentation](https://opensearch.org/docs/latest/security/access-control/users-roles/) for more information on creating users and roles.

## Add the integration

This component is configured interactively via Home Assistant's integration configuration page.

1. Verify you have restarted Home Assistant after installing the component.
2. From the [`Integrations` configuration menu](https://my.home-assistant.io/redirect/integrations/), add a new `OpenSearch` integration.
3. Provide the URL of your OpenSearch server in the format `https://<host>:<port>`. For example, `https://localhost:9200`.
4. If your OpenSearch instance is untrusted, you will be prompted to provide the path to the CA file or disable certificate verification.
5. If your OpenSearch instance is secured, you will be prompted to provide a username and password.
5. Once the integration is setup, you may tweak all configuration options via the `Configure` button on the [integrations page](https://my.home-assistant.io/redirect/integration/?domain=opensearch){:target="_blank"}.

## Configuration options

Select `Configure` from the integration's homepage to configure the following settings.

[![Open your Home Assistant instance and show the OpenSearch integration.](https://my.home-assistant.io/badges/integration.svg)](https://my.home-assistant.io/redirect/integration/?domain=opensearch){:target="_blank"}

### Send events to OpenSearch at this interval
The frequency at which events are published to OpenSearch, in seconds. The default is `60`.

### Gather all entity states at this interval
The frequency at which all entity states are gathered, in seconds. The default is `60`.

### Choose what types of entity changes to listen for and publish
There are two types of entity changes that can be published to OpenSearch:
- `Track entities with state changes` - Publish entities when their state changes
- `Track entities with attribute changes` - Publish entities when their attributes change

Enabling both options will publish entities when either their state or attributes change.

### Tags to apply to all published events
Tags are values that can be used to filter events in OpenSearch. You can use this to add tags to all published events.

### Toggle to only publish the set of targets below

Pick area, device, entity, or labels and only publish events from one of these targets. If you select multiple targets, events that match any of the targets will be published. If you select no targets, all events will be published.

### Toggle to exclude publishing the set of targets below

Pick area, device, entity, or labels and exclude events from one of these targets. If you select multiple targets, events that match any of the targets will be excluded. If you also configure `Toggle to only publish the set of targets below`, the exclusion will be applied after the inclusion.

## Advanced configuration

### Custom certificate authority (CA)

This component will use the system's default certificate authority (CA) bundle to verify the OpenSearch server's certificate. If you need to use a custom CA, you can provide the path to the CA file in the integration configuration.

1. Place the CA file somewhere within Home Assistant's `configuration` directory.
2. Follow the steps above to [add the integration](#add-the-integration).
3. After providing connection details, the component will attempt to establish a connection to the OpenSearch server. If the server's certificate is not signed by a known CA, you will be prompted for the CA file's path.
4. Provide the path to the CA file and continue with the setup.

!!! note
    You can choose to bypass certificate verification during setup, if you do not have the CA file available.
