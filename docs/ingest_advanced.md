# Advanced ingest configuration

!!! note

    This section describes advanced use cases. Most users will not need to customize their ingest configuration.

## Defining your own Index Mappings, Settings, and Ingest Pipeline

You can customize the mappings, settings and define an [ingest pipeline](https://opensearch.org/docs/latest/ingest-pipelines/index/) by creating a [component template](https://opensearch.org/docs/latest/im-plugin/index-templates/#use-component-templates-to-create-an-index-template) called `metrics-homeassistant@custom`

### Custom Ingest Pipeline

The following is an example on how to push your Home Assistant metrics into an ingest pipeline called `metrics-homeassistant-pipeline`:

=== "Dev Tools"
    Run these commands using OpenSearch Dashboards' [Dev Tools console](https://opensearch.org/docs/latest/dashboards/dev-tools/index-dev/):

    ```
    PUT _ingest/pipeline/metrics-homeassistant-pipeline
    {
        "description": "Pipeline for HomeAssistant dataset",
        "processors": [ ]
    }
    ```

    ```
    PUT _component_template/metrics-homeassistant@custom
    {
        "template": {
            "mappings": {}
            "settings": {
                "index.default_pipeline": "metrics-homeassistant-pipeline",
            }
        }
    }
    ```

=== "curl"

    ```bash
    OS_URL=https://localhost:9200 # (1)
    OS_USER=admin # (2)
    OS_PASSWORD=admin # (3)
    curl -X PUT "$OS_URL/_ingest/pipeline/metrics-homeassistant-pipeline" \
        -u "$OS_USER":"OS_PASSWORD" \
        -H "Content-Type: application/json" \
        -d'
        {
            "description": "Pipeline for HomeAssistant dataset",
            "processors": [ ]
        }
        ' # (4)

    curl -X PUT "$OS_URL/_component_template/metrics-homeassistant@custom" \
        -u "$OS_USER":"OS_PASSWORD" \
        -H "Content-Type: application/json" \
        -d'
        {
            "template": {
                "mappings": {}
                "settings": {
                    "index.default_pipeline": "metrics-homeassistant-pipeline",
                }
            }
        }
        '
    ```

    1. Replace `https://localhost:9200` with the URL of your OpenSearch instance
    2. Replace `admin` with your OpenSearch username
    3. Replace `admin` with your OpenSearch password
    4. Add your ingest pipeline processors to the `processors` array

Component template changes apply when the datastream performs a rollover so the first time you modify the template you may need to manually initiate index/datastream rollover to start applying the pipeline.

### Custom Attribute mappings

The following is an example on how to provide custom mappings for any attributes you're interested in making available as other data types `metrics-homeassistant-pipeline`:

=== "Dev Tools"
    Run these commands using OpenSearch Dashboards' [Dev Tools console](https://opensearch.org/docs/latest/dashboards/dev-tools/index-dev/):

    ```
    PUT /_component_template/metrics-homeassistant@custom
    {
        "template": {
            "mappings": {
                "properties": {
                    "hass.entity.attributes": {
                        "type": "object",
                        "properties": {
                            "temperature": {
                                "type": "float"
                                "ignore_malformed": true
                            }
                        }
                    }
                }
            }
        }
    }
    ```

=== "curl"

    ```bash
    OS_URL=https://localhost:9200 # (1)
    OS_USER=admin # (2)
    OS_PASSWORD=admin # (3)

    curl -X PUT "$OS_URL/_component_template/metrics-homeassistant@custom" \
        -u "$OS_USER":"OS_PASSWORD" \
        -H "Content-Type: application/json" \
        -d'
        {
            "template": {
                "mappings": {
                    "properties": {
                        "hass.entity.attributes": {
                            "type": "object",
                            "properties": {
                                "temperature": {
                                    "type": "float"
                                    "ignore_malformed": true
                                }
                            }
                        }
                    }
                }
            }
        }
        '
    ```

    1. Replace `https://localhost:9200` with the URL of your OpenSearch instance
    2. Replace `admin` with your OpenSearch username
    3. Replace `admin` with your OpenSearch password
    4. Modify the body of the component template to include desired mappings
