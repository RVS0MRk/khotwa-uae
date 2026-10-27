"""Gunicorn settings used by the Render start command."""

import os

bind = f"0.0.0.0:{os.environ.get('PORT', '10000')}"
workers = 1
threads = 2
timeout = 70
