It is possible to change the way the local instance inside the dev container runs using a local configuration file. The defaults are checked into the repo as `tba_dev_config.json` and should be sufficient for most everyday use. However, if you want to configure overrides locally, add a json file to `tba_dev_config.local.json` (which will be ignored by `git`). Note that you need to `halt` and restart the development container for changes to take effect.

```bash
$ cp tba_dev_config.json tba_dev_config.local.json
$ edit tba_dev_config.local.json
$ vagrant halt && vagrant up
```

## tba_dev_config Options

| Parameter | Description |
| --- | --- |
| `auth_use_prod` | Set to `true` (or any non-empty value) to use an upstream Firebase project for authentication. Requires `google_application_credentials` to be set. If unset, will use the Firebase emulator locally for authentication. |
| `datastore_mode` | Can be either `local` or `remote`. By default this is set to `local` and will use the [Datastore emulator](https://cloud.google.com/datastore/docs/tools/datastore-emulator) bundled with the App Engine SDK. If instead you want to point your instance to a real Datatsore instance, set this to `remote` and also set the `google_application_credentials` property (**note: current remote mode does not work with the builtin NDB library**)|
| `flask_response_cache_enabled` | Can be either `true` or `false`. This is used to configure whether or not we store rendered html pages in memcache or not. By default this is `false`, to make development iteration faster. |
| `google_application_credentials` | A path (relative to the repository root) to a [service account JSON key](https://cloud.google.com/iam/docs/creating-managing-service-account-keys) used to authenticate to a production Google Cloud service. We recommend to put these in `ops/dev/keys` (which will be ignored by `git`). Example: `ops/dev/keys/tba-prod-key.json` |
| `log_level` | This will be used to set the `--log-level` flag when invoking `dev_appserver`. See the [documentation](https://cloud.google.com/appengine/docs/standard/python3/tools/local-devserver-command) for allowed values. |
| `tba_log_level` | This is used to configure the minimum log level for logs emitted by the TBA application. Allowed values correspond to the possible [`logging` library levels](https://docs.python.org/2/library/logging.html#logging-levels). |
| `storage_mode` | Can be either `local` or `remote`. By default this is set to `local` and will store files on the local filesystem. If instead you want to point your instance to an upstream Google Cloud Storage bucket, follow the setup instructions in the [Google Cloud Storage](https://github.com/the-blue-alliance/the-blue-alliance/wiki/Storage#google-cloud-storage) setup section. |
| `storage_path` | (Optional) The local directory to store files to when in local `storage_mode`. Path should be relative to the root of the project. |
