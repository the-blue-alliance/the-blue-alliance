The Blue Alliances writes files to backup and archive data. Examples include storing responses from the FRC API (to allow replaying API responses) and periodic backups of data. Production uses [Google Cloud Storage](https://cloud.google.com/storage/docs/introduction), while the development container writes these files to the local filesystem. The development container can be configured to use an upstream Google Cloud Storage instance as well.

## Configuration

[`tba_dev_config.json`/`tba_dev_config.local.json`](https://github.com/the-blue-alliance/the-blue-alliance/wiki/tba_dev_config) exposes two fields to configure storage - `storage_mode` and `storage_path`. `storage_mode` is required to be either `local` or `remote`, while `storage_path` is only necessary if `storage_mode` is `local` (and will be ignored when `storage_mode` is `remote`).

After syncing over your modified config file, make sure to either restart your dev container or restart the `dev_appserver.sh` script in the tmux session in order to get the local project to respect the modified config file.

### Local

Change the `storage_mode` property to `local`, and set the `storage_path` property to a local file path. The path will be resolved from the root of the project (ex: `the-blue-alliance/` folder).

```json
{
    ...
    "storage_mode": "local",
    "storage_path": "ops/dev/storage",
    ...
}
```

### Google Cloud Storage

A local development instance can be configured to point to an upstream Google Cloud Storage bucket. You'll need an upstream Google App Engine instance. Refer to the [[Google App Engine + Firebase Setup|GAE-Firebase-Setup]] for details. By default, a bucket named the `{project}.appspot.com` will be used to read/write files from.

Change the `storage_mode` property to be `remote`. `storage_path` can be removed or left as-is - it will be ignored. Additionally, set the `google_application_credentials` field (details can be found in the [[development runbook|Development-Runbook]]).

```json
{
    ...
    "google_application_credentials": "ops/dev/keys/my-key.json",
    "storage_mode": "remote",
    ...
}
```

## Writing Files

Write files to storage by specifying both a file name and the content. The content should be a string.

```python
import json

from backend.common import storage

def write_file():
    storage.write('file_name.json', json.dumps({'some': 'content'}))

write_file()
```

## Reading Files

Read files from storage by specifying a file name. The content will be `None` if the file does not exist.

```python
from backend.common import storage

def read_file():
    print(storage.read("nonexistent_file.json"))  # None
    print(storage.read("file_name.json"))  # {'some': 'content'}

read_file()
```
