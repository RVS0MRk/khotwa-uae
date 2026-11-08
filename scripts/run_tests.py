"""Run mock Python and managed-Chromium suites with one command; no live API calls."""

import os
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
os.chdir(ROOT)
env = {**os.environ, "GROQ_API_KEY": "", "PYTHON_EXE": sys.executable, "PYTHONUTF8": "1"}
commands = [[sys.executable, "-m", "unittest", "discover", "-v"]]
if "--python-only" not in sys.argv:
    node = shutil.which("node")
    if not node:
        raise SystemExit("Node.js is required. Install Node LTS, npm install, then npx playwright install chromium.")
    commands += [
        [node, name]
        for name in ("test_browser.cjs", "test_redesign.cjs", "test_v2.cjs", "test_v21.cjs", "test_v22.cjs")
    ]
for command in commands:
    print("Running: " + " ".join(command), flush=True)
    result = subprocess.run(command, env=env)
    if result.returncode:
        raise SystemExit(result.returncode)
print("All requested mock suites passed. Live Groq was not called.")
