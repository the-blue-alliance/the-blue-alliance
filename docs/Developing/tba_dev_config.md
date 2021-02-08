It is possible to change the way the local instance inside the dev container runs using a local configuration file. The defaults are checked into the repo as `tba_dev_config.json` and should be sufficient for most everyday use. However, if you want to configure overrides locally, add a json file to `tba_dev_config.local.json` (which will be ignored by `git`). Note that you need to `halt` and restart the development container for changes to take effect.

```bash
$ cp tba_dev_config.json tba_dev_config.local.json
$ edit tba_dev_config.local.json
$ vagrant halt && vagrant up
```

## tba_dev_config Options

| Parameter | Description |
| --- | --- |
| `datastore_mode` | Can be either `local` or `remote`. By default this is set to `local` and will use the [Datastore emulator](https://cloud.google.com/datastore/docs/tools/datastore-emulator) bundled with the App Engine SDK. If instead, you want to point your instance to a real Datatsore instance, set this to `remote` and also set the `google_application_credentials` property |
| `tasks_mode` | Can be either `local` or `remote`. By default this is set to `local` and will use Redis + RQ locally to enqueue tasks. If instead, you want to point your instance to a real Google Cloud Tasks queue, follow the setup instructions in the [Google Cloud Tasks + ngrok](https://github.com/the-blue-alliance/the-blue-alliance/wiki/Queues-and-defer#google-cloud-tasks--ngrok) setup section. |
| `tasks_remote_config` | (Optional) A dictionary of configuration parameters for using a remote task queue. Only necessary if `tasks_mode` is set to `remote`. See setup instructions in the [Google Cloud Tasks + ngrok](https://github.com/the-blue-alliance/the-blue-alliance/wiki/Queues-and-defer#google-cloud-tasks--ngrok) setup section. |
| `tasks_remote_config.ngrok_url` | (Optional) The URL of the ngrok session created to route requests from Google Cloud Tasks back to a local service. Only necessary if `tasks_mode` is set to `remote`. See setup instructions in the [Google Cloud Tasks + ngrok](https://github.com/the-blue-alliance/the-blue-alliance/wiki/Queues-and-defer#google-cloud-tasks--ngrok) setup section. |
| `redis_cache_url` | The url of a Redis cache used for caching datastore responses. Defaults to `redis://localhost:6739`, which is the address of Redis running inside the dev container. To disable the global cache, set this property to an empty string. |
| `flask_response_cache_enabled` | Can be either `true` or `false`. This is used to configure whether or not we store rendered html pages in Redis or not. By default this is `false`, to make development iteration faster. |
| `google_application_credentials` | A path (relative to the repository root) to a [service account JSON key](https://cloud.google.com/iam/docs/creating-managing-service-account-keys) used to authenticate to a production Google Cloud service. We recommend to put these in `ops/dev/keys` (which will be ignored by `git`). Example: `ops/dev/keys/tba-prod-key.json` |
| `log_level` | This will be used to set the `--log-level` flag when invoking `dev_appserver`. See the [documentation](https://cloud.google.com/appengine/docs/standard/python3/tools/local-devserver-command) for allowed values. |
| `tba_log_level` | This is used to configure the minimum log level for logs emitted by the TBA application. Allowed values correspond to the possible [`logging` library levels](https://docs.python.org/2/library/logging.html#logging-levels). |
