## Troubleshooting

Solutions to common questions and errors:

### Error loading opensearch

After installing this component, you may see an error similar to this on startup:

> No module named 'opensearchpy'

```
ERROR (MainThread) [homeassistant.setup] Error during setup of component elastic Traceback (most recent call last): File "/usr/src/app/homeassistant/setup.py", line 145, in _async_setup_component hass, processed_config) File "/usr/local/lib/python3.6/asyncio/coroutines.py", line 212, in coro res = func(*args, **kw) File "/config/custom_components/elastic/__init__.py", line 62, in async_setup gateway = ElasticsearchGateway(hass, conf) File "/config/custom_components/elastic/__init__.py", line 126, in __init__ self.client = self._create_es_client() File "/config/custom_components/elastic.py", line 134, in _create_es_client import opensearchpy ModuleNotFoundError: No module named 'opensearchpy'
```

This means that home-assistant was not able to download the required `opensearch-py` module for this component to function.

**Solution**: Restart home assistant

More info: https://github.com/rhooper/homeassistant-opensearch/issues/23

### Certificate verify failed

When connecting to a TLS protected cluster, you might receive the following error:

```
ssl.SSLError: [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed (_ssl.c:720)
```

This generally means that the certificate is not trusted by the home-assistant runtime. Please ensure your certificates are setup correctly. To skip certificate verification, see setup instructions [here](https://github.com/rhooper/homeassistant-opensearch/pull/36)

More info: https://github.com/rhooper/homeassistant-opensearch/issues/33
