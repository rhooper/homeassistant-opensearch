"""Defines the index template for OpenSearch data streams."""

from typing import Any

index_template_definition: dict[str, Any] = {
    "index_patterns": ["metrics-homeassistant.*-default"],
    "template": {
        "mappings": {
            "dynamic": "false",
            "dynamic_templates": [
                {
                    "hass_numeric_attributes": {
                        "path_match": "hass.entity.attributes.*",
                        "match_mapping_type": "long",
                        "mapping": {
                            "type": "float",
                            "ignore_malformed": True,
                        },
                    }
                },
                {
                    "hass_double_attributes": {
                        "path_match": "hass.entity.attributes.*",
                        "match_mapping_type": "double",
                        "mapping": {
                            "type": "float",
                            "ignore_malformed": True,
                        },
                    }
                },
                {
                    "hass_boolean_attributes": {
                        "path_match": "hass.entity.attributes.*",
                        "match_mapping_type": "boolean",
                        "mapping": {
                            "type": "boolean",
                        },
                    }
                },
                {
                    "hass_string_attributes": {
                        "path_match": "hass.entity.attributes.*",
                        "match_mapping_type": "string",
                        "mapping": {
                            "type": "keyword",
                            "ignore_above": 1024,
                        },
                    }
                },
            ],
            "properties": {
                "data_stream": {
                    "properties": {
                        "type": {"type": "constant_keyword", "value": "metrics"},
                        "dataset": {"type": "keyword"},
                        "namespace": {"type": "constant_keyword", "value": "default"},
                    }
                },
                "hass": {
                    "type": "object",
                    "properties": {
                        "entity": {
                            "type": "object",
                            "properties": {
                                "id": {"type": "keyword"},
                                "domain": {"type": "keyword"},
                                "friendly_name": {"type": "keyword"},
                                "name": {"type": "keyword"},
                                "attributes": {"type": "object", "dynamic": True},
                                "object": {
                                    "type": "object",
                                    "properties": {
                                        "id": {
                                            "type": "keyword",
                                        }
                                    },
                                },
                                "location": {"type": "geo_point"},
                                "value": {"type": "keyword"},
                                "valueas": {
                                    "properties": {
                                        "string": {"type": "keyword"},
                                        "float": {
                                            "type": "float",
                                            "ignore_malformed": True,
                                        },
                                        "boolean": {"type": "boolean"},
                                        "datetime": {
                                            "type": "date",
                                            "ignore_malformed": True,
                                        },
                                        "date": {
                                            "type": "date",
                                            "format": "strict_date",
                                            "ignore_malformed": True,
                                        },
                                        "time": {
                                            "type": "date",
                                            "format": "HH:mm:ss.SSSSSS||time||strict_hour_minute_second||time_no_millis",
                                            "ignore_malformed": True,
                                        },
                                        "integer": {
                                            "type": "integer",
                                            "ignore_malformed": True,
                                        },
                                    }
                                },
                                "platform": {"type": "keyword"},
                                "unit_of_measurement": {"type": "keyword"},
                                "state": {"properties": {"class": {"type": "keyword"}}},
                                "labels": {"type": "keyword"},
                                "area": {
                                    "type": "object",
                                    "properties": {
                                        "floor": {
                                            "type": "object",
                                            "properties": {
                                                "id": {"type": "keyword"},
                                                "name": {"type": "keyword"},
                                            },
                                        },
                                        "id": {"type": "keyword"},
                                        "name": {"type": "keyword"},
                                    },
                                },
                                "device": {
                                    "type": "object",
                                    "properties": {
                                        "id": {"type": "keyword"},
                                        "name": {"type": "keyword"},
                                        "labels": {"type": "keyword"},
                                        "area": {
                                            "type": "object",
                                            "properties": {
                                                "floor": {
                                                    "type": "object",
                                                    "properties": {
                                                        "id": {"type": "keyword"},
                                                        "name": {"type": "keyword"},
                                                    },
                                                },
                                                "id": {"type": "keyword"},
                                                "name": {"type": "keyword"},
                                            },
                                        },
                                    },
                                },
                                "device_class": {"type": "keyword"},
                            },
                        }
                    },
                },
                "@timestamp": {
                    "type": "date_nanos",
                    "format": "strict_date_optional_time_nanos",
                },
                "tags": {"type": "keyword", "ignore_above": 1024},
                "event": {
                    "properties": {
                        "action": {"type": "keyword"},
                        "type": {"type": "keyword"},
                        "kind": {"type": "keyword"},
                    }
                },
                "agent": {
                    "properties": {
                        "version": {"type": "keyword"},
                    }
                },
                "host": {
                    "properties": {
                        "architecture": {"type": "keyword"},
                        "location": {"type": "geo_point"},
                        "hostname": {"type": "keyword"},
                        "name": {"type": "keyword"},
                        "os": {"properties": {"name": {"type": "keyword"}}},
                    }
                },
                "ecs": {"properties": {"version": {"type": "keyword"}}},
            },
        },
        "settings": {
            "codec": "best_compression",
            "mapping": {"total_fields": {"limit": "10000"}},
        },
    },
    "priority": 500,
    "data_stream": {},
    "version": 9,
}
