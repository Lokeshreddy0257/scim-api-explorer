"""
api/index.py
------------
Vercel serverless entry point.
Exposes the Flask SCIM 2.0 app as a WSGI handler.

Note: Vercel functions are stateless — the in-memory user/group store
resets on each cold start. This is expected for a demo/educational tool.
All SCIM endpoints are fully functional within a single session.
"""

import sys
import os

# Make the project root importable so `src/` resolves correctly
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from src.scim_server import app  # noqa: F401  (Vercel looks for `app`)
