# Using OpenSearch Dashboards

The integration will put data into OpenSearch under the `metrics-homeassistant.*` [data stream](https://opensearch.org/docs/latest/dashboards/im-dashboards/datastream/). To explore your data, create visualizations, or dashboards in OpenSearch Dashboards you first need to create an [Index Pattern](https://opensearch.org/docs/latest/dashboards/management/index-patterns/).

## Create an index pattern

=== "OpenSearch Dashboards UI"
    Create an Index Pattern using OpenSearch Dashboards' UI:

    1. Open OpenSearch Dashboards
    2. Using the instructions in the [OpenSearch Dashboards documentation](https://opensearch.org/docs/latest/dashboards/management/index-patterns/), navigate to the `Index Patterns` page, and create an index pattern with the following values:
        - **Index pattern name**: `metrics-homeassistant.*`
        - **Time field**: `@timestamp`

=== "curl"
    Create an Index Pattern using `curl` and the OpenSearch Dashboards [Saved Objects API](https://opensearch.org/docs/latest/dashboards/management/saved-objects/):

    ```bash
    DASHBOARDS_URL=http://localhost:5601 # (1)
    DASHBOARDS_USER=admin # (2)
    DASHBOARDS_PASSWORD=admin # (3)
    curl -X POST "$DASHBOARDS_URL/api/saved_objects/index-pattern" \
        -u "$DASHBOARDS_USER":"DASHBOARDS_PASSWORD" \
        -H "Content-Type: application/json" \
        -H "osd-xsrf: true" \
        -d'
        {
            "attributes": {
                "title": "metrics-homeassistant.*",
                "timeFieldName": "@timestamp"
            }
        }
        '
    ```

    1. Replace `http://localhost:5601` with the URL of your OpenSearch Dashboards instance
    2. Replace `admin` with your OpenSearch Dashboards username
    3. Replace `admin` with your OpenSearch Dashboards password

=== "Dev Tools"
    Create an Index Pattern using OpenSearch Dashboards' [Dev Tools console](https://opensearch.org/docs/latest/dashboards/dev-tools/index-dev/):

    ```
    POST .kibana/_doc/index-pattern:metrics-homeassistant
    {
        "type": "index-pattern",
        "index-pattern": {
            "title": "metrics-homeassistant.*",
            "timeFieldName": "@timestamp"
        }
    }
    ```

## Exploring Home Assistant data in OpenSearch Dashboards

Once you have created an Index Pattern, you can start exploring your Home Assistant data in OpenSearch Dashboards using `Discover`:

1. In OpenSearch Dashboards select `Discover`
2. Select the `metrics-homeassistant.*` Index Pattern at the top left
3. You can now see all the Home Assistant data that has been published to OpenSearch
4. You can filter the data using the filter bar at the top
5. You can pull specific fields into the document table at the bottom by clicking on the `+` icon next to a field
6. You can change the time range of the data you are viewing using the time picker in the top right

![img](assets/kibana-discover.png)

## Viewing Home Assistant data in OpenSearch Dashboards

When creating new visualizations you may find the following fields useful:

| Field | Description |
| --- | --- |
| `@timestamp` | The timestamp of the event (ex. `Apr 10, 2024 @ 16:23:25.878`) |
| `hass.entity.attributes.friendly_name` | The name of the entity in Home Assistant (ex. `Living Room EcoBee Temperature`) |
| `hass.entity.device.area.name` | The area of the device in Home Assistant (ex. `Living Room`) |
| `hass.entity.id` | The entity id of the entity in Home Assistant (ex. `sensor.living_room_ecobee_temperature`) |
| `hass.entity.value` | The state of the entity in Home Assistant (ex. `72.5`), as a string-typed value |
| `hass.entity.valueas.integer` | The state of the entity in Home Assistant (ex. `72`), as an integer-typed value |
| `hass.entity.valueas.float` | The state of the entity in Home Assistant (ex. `72.5`), as a float-typed value |
| `hass.entity.valueas.boolean` | The state of the entity in Home Assistant (ex. `true`), as a boolean-typed value |
| `hass.entity.valueas.date` | The state of the entity in Home Assistant (ex. `2024-04-10`), as a date-typed value |
| `hass.entity.valueas.datetime` | The state of the entity in Home Assistant (ex. `2024-04-10T16:23:25.878`), as a datetime-typed value |
| `hass.entity.valueas.time` | The state of the entity in Home Assistant (ex. `16:23:25.878`), as a time-typed value |


To build a visualization that shows the temperature of a specific entity over time, you can use the following steps:

1. In OpenSearch Dashboards select `Visualizations` and create a new visualization
2. Select `metrics-homeassistant.*`
3. For the `X-axis` select `@timestamp`
4. For the `Y-axis` select `hass.entity.valueas.float`
5. In the filter bar at the top, add a filter for `hass.entity.id` and set the value to the entity id of the entity you want to visualize (ex. `sensor.living_room_ecobee_temperature`) or `hass.entity.attributes.friendly_name` and set the value to the friendly name of the entity you want to visualize (ex. `Living Room EcoBee Temperature`)

![img](assets/kibana-lens-visualization.png)

## Inspiration

### HVAC Usage
Graph your home's climate and HVAC Usage:

![img](assets/hvac-history.png)

### Weather Station
Visualize and alert on data from your weather station:

![img](assets/weather-station.png)

![img](assets/weather-station-wind-pressure.png)

### Additional examples

Some usage examples inspired by [real users of the original Elasticsearch integration](https://github.com/legrego/homeassistant-elasticsearch/issues/203), whose techniques can also inspire OpenSearch users:

- Utilizing a Raspberry Pi in [kiosk mode](https://www.raspberrypi.com/tutorials/how-to-use-a-raspberry-pi-in-kiosk-mode/) with a 15" display, the homeassistant-opensearch integration enables the creation of rotating fullscreen OpenSearch Dashboards visualizations. Those dashboards display metrics collected from various Home Assistant integrations, offering visually dynamic and informative dashboards for monitoring smart home data.
- To address temperature maintenance issues in refrigerators and freezers, temperature sensors in each appliance report data to Home Assistant, which is then published to OpenSearch. OpenSearch Dashboards' [alerting framework](https://opensearch.org/docs/latest/observing-your-data/alerting/index/) is employed to set up rules that notify the user if temperatures deviate unfavorably for an extended period. The OpenSearch rule engine and aggregations simplify the monitoring process for this specific use case.
- Monitoring the humidity and temperature in a snake enclosure/habitat for a user's daughter, the integration facilitates the use of OpenSearch's Alerting framework. This choice is motivated by the framework's suitability for the monitoring requirements, providing a more intuitive solution compared to Home Assistant automations.
- The integration allows users to maintain a smaller subset of data, focusing on individual stats of interest, for an extended period. This capability contrasts with the limited retention achievable with Home Assistant and databases like MariaDB/MySQL. This extended data retention facilitates very long-term trend analysis, such as for weather data, enabling users to glean insights over an extended timeframe.
