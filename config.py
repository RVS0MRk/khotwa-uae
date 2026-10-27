"""Shared Groq configuration for the Flask app and API smoke test."""

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
MODEL = "openai/gpt-oss-120b"
GROQ_COMPLETION_TOKENS = {"/ask": 1200, "/discover": 2500, "/generate": 5000, "test_api.py": 200}
import os

GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
