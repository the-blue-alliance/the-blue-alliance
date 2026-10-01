import os
import sys

# The scripts in ops/pr_screenshots/ import each other by bare module name
# (they run from that directory in CI), so make them importable here too.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
