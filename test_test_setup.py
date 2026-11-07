import os
from pathlib import Path
import subprocess
import sys
import unittest


class TestEnvironmentTests(unittest.TestCase):
    def test_mock_bootstrap_survives_config_imported_without_key(self):
        env = dict(os.environ)
        env.pop("GROQ_API_KEY", None)
        code = """
import builtins, os
assert 'GROQ_API_KEY' not in os.environ
import config
assert config.GROQ_API_KEY == ''
original = builtins.open
def guarded(file, *args, **kwargs):
    if str(file).endswith('secret.txt'):
        raise AssertionError('Mock tests must not read a local credential file')
    return original(file, *args, **kwargs)
builtins.open = guarded
import test_support
import app
assert app.API_KEY == test_support.TEST_KEY
"""
        result = subprocess.run([sys.executable, "-c", code], cwd=Path(__file__).parent,
                                env=env, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
