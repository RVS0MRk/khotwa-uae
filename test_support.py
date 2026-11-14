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
    # Mock only the new external semantic-classification boundary. Production
    # has no environment switch bypassing it. Publication/source rules still run.
    import material_claims

    def fixture_classifier(items, _api_key):
        return {item["id"]: "noun_phrase" for item in items}

    material_claims.classify = fixture_classifier
    if "app" in sys.modules:
        sys.modules["app"].API_KEY = TEST_KEY


configure_mock_environment()


def signed_assistant_turn(client, text):
    """Obtain a genuine server-issued turn/signature without a live request."""
    import json
    from unittest.mock import patch
    import app

    answer = {
        "title": "Earlier suggestion",
        "summary": text,
        "points": [{"title": "Action", "text": text}],
        "next_action": text,
        "caution": "",
    }
    with patch.object(app, "call_groq", return_value=json.dumps(answer)):
        response = client.post("/ask", json={"question": "Suggest my next experiment"})
    assert response.status_code == 200
    return {
        "role": "assistant",
        "content": json.dumps(response.json["answer"]),
        "signature": response.json["assistant_signature"],
    }
