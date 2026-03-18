---
title: Introduction
---

# OpenSearch Component for Home-Assistant

Publish Home Assistant events to your [OpenSearch](https://opensearch.org) cluster!

## Features

- Efficiently publishes Home-Assistant events to OpenSearch using the Bulk API
- Automatically sets up Datastreams using Time Series Data Streams ("TSDS") and Datastream Lifecycle Management ("DLM")
- Supports OpenSearch [security features](https://opensearch.org/docs/latest/security/) via optional username and password
- Selectively publish events based on labels, entities, devices, or areas

## Compatibility

- OpenSearch 2.0+
- [Home Assistant Community Store](https://github.com/custom-components/hacs)
- Home Assistant >= 2025.6

## Older versions

[Version `1.0.0`](https://github.com/legrego/homeassistant-opensearch/releases/tag/v1.0.0) includes support for older OpenSearch versions. No features or bugfixes will be backported to this version.
[Version `0.4.0`](https://github.com/legrego/homeassistant-opensearch/releases/tag/v0.4.0) includes support for older versions of OpenSearch. No features or bugfixes will be backported to this version.
