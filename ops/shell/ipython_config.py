import json
import os

c = get_config()  # pyre-ignore  # noqa: F821

c.TerminalIPythonApp.display_banner = True
c.InteractiveShell.autoindent = True
c.InteractiveShell.confirm_exit = False

# Configure welcome banner
c.InteractiveShell.banner2 = """
Welcome to the TBA Shell!

Refer to documentation for how to use the shell at <link>
"""

# Add the TBA code to PYTHONPATH
c.InteractiveShellApp.exec_lines = [
    'import sys; sys.path.extend(["src", "ops/shell/lib"])',
    "import ops.shell.lib as shell_lib",
]

# Set up Google Application Credentials
if os.path.isfile("tba_dev_config.local.json"):
    with open("tba_dev_config.local.json") as f:
        local_config = json.load(f)
        if "google_application_credentials" in local_config:
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = local_config[
                "google_application_credentials"
            ]
