"""Start/reuse the explicitly simulated loopback preview and open a browser."""
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import urllib.request
import webbrowser

ROOT = Path(__file__).resolve().parents[1]
URL = 'http://127.0.0.1:5010'


def ready():
    try:
        with urllib.request.urlopen(URL + '/demo-status', timeout=2) as response:
            return json.load(response).get('mode') == 'offline-simulated-demo'
    except Exception:
        return False


def main():
    if not ready():
        output = ROOT / 'outputs/demo-preview'
        output.mkdir(parents=True, exist_ok=True)
        flags = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
        with (output/'server.log').open('ab') as log:
            process = subprocess.Popen([sys.executable, '-X', 'utf8', str(ROOT/'demo_server.py')], cwd=ROOT,
                                       stdout=log, stderr=log, creationflags=flags,
                                       env={**os.environ, 'GROQ_API_KEY':'offline-demo-no-provider-access', 'PYTHONUTF8':'1'})
        for _ in range(60):
            if ready():
                break
            if process.poll() is not None:
                raise SystemExit('Demo failed to start. Check outputs/demo-preview/server.log; port 5010 may already be occupied.')
            time.sleep(.5)
        else:
            raise SystemExit('Demo did not become ready. Check outputs/demo-preview/server.log.')
    print('V2.2.8 Academic Final - SIMULATED OFFLINE DEMO: ' + URL)
    print('This is local rehearsal data, not live Groq or the public Render site.')
    webbrowser.open(URL, new=2)


if __name__ == '__main__':
    main()
