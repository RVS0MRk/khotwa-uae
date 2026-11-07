"""Mock-only bootstrap, safe even if config was imported before these tests.

Never read a local credential file. This module is not used by test_api.py's
explicit live smoke test or by production application startup.
"""
import os
import sys

TEST_KEY = "test-only-placeholder"


def configure_mock_environment():
    os.environ["GROQ_API_KEY"] = TEST_KEY
    import config
    config.GROQ_API_KEY = TEST_KEY
    if "app" in sys.modules:
        sys.modules["app"].API_KEY = TEST_KEY


configure_mock_environment()
