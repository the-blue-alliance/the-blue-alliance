import json
import os

c = get_config()  # pyre-ignore  # noqa: F821

c.TerminalIPythonApp.display_banner = True
c.InteractiveShell.autoindent = True
c.InteractiveShell.confirm_exit = False

# Configure welcome banner
c.InteractiveShell.banner2 = """
Welcome to the TBA Shell!

Refer to documentation for how to use the shell at:
https://github.com/the-blue-alliance/the-blue-alliance/wiki/local-shell
"""

c.InteractiveShellApp.exec_lines = [
    # Enable autoreloading changed files
    "%load_ext autoreload",
    "%autoreload 2",
    # Fix up TBA Import Paths
    "import sys; sys.path.extend(['src', 'ops'])",
    "import shell.lib as shell_lib",
]

# Set up Google Application Credentials
if os.path.isfile("tba_dev_config.local.json"):
    with open("tba_dev_config.local.json") as f:
        local_config = json.load(f)
        if "google_application_credentials" in local_config:
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = local_config[
                "google_application_credentials"
            ]

        if local_config.get("datastore_mode") == "local":
            # These match the defaults used in the dev_appserver invocation
            os.environ["DATASTORE_EMULATOR_HOST"] = "localhost:8089"
            os.environ["DATASTORE_DATASET"] = "test"
