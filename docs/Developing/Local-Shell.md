The Blue Alliance comes with a pre-configured [`ipython`](https://ipython.org/) environment to aid in running code locally. This will give you a regular python interpreter that has the ability to connect to your development instance's datastore.

## The Local TBA Shell

```bash
$ ./ops/shell/tba_shell.sh
```

You can now import TBA code and run them, as you would in any other python interpreter.

## Connecting to the Datastore

The shell will use the same local configuration as the dev app. You can configure the datastore connection properties using [`tba_dev_config.local.json`](https://github.com/the-blue-alliance/the-blue-alliance/wiki/tba_dev_config) in your local repository.

The Cloud NDB library requires there be an active NDB connection context, there is a convienence wrapper (`shell_lib.connect_to_ndb()`) automatically imported for you to use, as part of the shell utilities library:

```python
In [1]: with shell_lib.connect_to_ndb():
   ...:     from backend.common.models.event import Event
   ...:     event = Event.get_by_id("2019ctwat")
   ...:     print(event.name)
   ...: 
Connecting to NDB using keyfile ops/dev/keys/tbatv-prod-hrd-key.json
NE District Waterbury Event
```

## Running Local User Scripts

There may be situations where it is preferable to write and commit a simple python script to run against a production datastore instance instead of building it in the interpreter. For that, we also support running scripts as the entrypoint for the special ipython environment.

These scripts are stored in `ops/shell/user_scripts` and are invoked using the `ops/shell/run_user_script.sh` wrapper. That script takes the name of the script to run, as well as any relevant arguments after `--`. For example, here is a simple user script that prints an event:

```bash
# Show the script
$ cat ops/shell/user_scripts/print_event.py 
import argparse

from shell.lib import connect_to_ndb

from backend.common.models.event import Event

parser = argparse.ArgumentParser()
parser.add_argument("event_key")
args = parser.parse_args()

with connect_to_ndb():
    print(f"Fetching {args.event_key}...")
    print(Event.get_by_id(args.event_key))

# Run the script
$ ./ops/shell/run_user_script.sh print_event.py -- 2019ctwat
Connecting to NDB using keyfile ops/dev/keys/tbatv-prod-hrd-key.json
Fetching 2019ctwat...
Event(key=Key('Event', '2019ctwat'), city='Waterbury' ...
```