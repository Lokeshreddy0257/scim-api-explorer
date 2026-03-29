"""
scim_client.py
--------------
The SCIM client — this is what *you* (or an Identity Provider like Okta)
would run to talk to a SCIM server.

Every function here:
  1. Shows you the HTTP request it's about to send  (so you can see it)
  2. Actually sends the real HTTP request
  3. Shows you the HTTP response that came back
  4. Returns (status_code, response_body) for further use

This makes the "invisible" HTTP traffic visible to you!
"""

import time
import requests
from src.visualizer import show_http_request, show_http_response

BASE_URL = "http://localhost:5000/scim/v2"

HEADERS = {
    "Content-Type": "application/scim+json",
    "Accept":       "application/scim+json",
    "Authorization": "Bearer demo-token-abc123",
}

SCIM_CORE_SCHEMA  = "urn:ietf:params:scim:schemas:core:2.0:User"
SCIM_PATCH_SCHEMA = "urn:ietf:params:scim:api:messages:2.0:PatchOp"


def _call(method: str, path: str, body: dict = None) -> tuple[int, dict | None]:
    """
    Internal helper: visualize → send → visualize response → return result.
    """
    url = BASE_URL + path
    show_http_request(method, url, body)

    start = time.perf_counter()
    resp  = requests.request(method, url, json=body, headers=HEADERS, timeout=10)
    ms    = (time.perf_counter() - start) * 1000

    try:
        resp_body = resp.json()
    except Exception:
        resp_body = None

    show_http_response(resp.status_code, resp_body, ms)
    return resp.status_code, resp_body


# ─────────────────────────────────────────────────────────────────────────────
#  List all users  →  GET /scim/v2/Users
# ─────────────────────────────────────────────────────────────────────────────
def list_users():
    """
    Fetch the full list of users from the SCIM server.
    HTTP method: GET
    """
    return _call("GET", "/Users")


# ─────────────────────────────────────────────────────────────────────────────
#  Create a user  →  POST /scim/v2/Users
# ─────────────────────────────────────────────────────────────────────────────
def create_user(
    username:     str,
    display_name: str,
    email:        str,
    first_name:   str = "",
    last_name:    str = "",
) -> tuple[int, dict | None]:
    """
    Create a new user on the SCIM server.
    HTTP method: POST  (always used for creating new things)
    """
    body = {
        "schemas":     [SCIM_CORE_SCHEMA],
        "userName":    username,
        "displayName": display_name,
        "name": {
            "givenName":  first_name,
            "familyName": last_name,
        },
        "emails": [
            {"value": email, "type": "work", "primary": True}
        ],
        "active": True,
    }
    return _call("POST", "/Users", body)


# ─────────────────────────────────────────────────────────────────────────────
#  Get one user  →  GET /scim/v2/Users/<id>
# ─────────────────────────────────────────────────────────────────────────────
def get_user(user_id: str) -> tuple[int, dict | None]:
    """
    Fetch a single user by their ID.
    HTTP method: GET
    """
    return _call("GET", f"/Users/{user_id}")


# ─────────────────────────────────────────────────────────────────────────────
#  Replace a user  →  PUT /scim/v2/Users/<id>
# ─────────────────────────────────────────────────────────────────────────────
def replace_user(user_id: str, username: str, display_name: str, email: str) -> tuple[int, dict | None]:
    """
    Completely REPLACE a user's data (PUT = full replacement).
    If you omit a field, it gets cleared — unlike PATCH!
    HTTP method: PUT
    """
    body = {
        "schemas":     [SCIM_CORE_SCHEMA],
        "userName":    username,
        "displayName": display_name,
        "emails": [{"value": email, "type": "work", "primary": True}],
        "active": True,
    }
    return _call("PUT", f"/Users/{user_id}", body)


# ─────────────────────────────────────────────────────────────────────────────
#  Deactivate a user  →  PATCH /scim/v2/Users/<id>
# ─────────────────────────────────────────────────────────────────────────────
def deactivate_user(user_id: str) -> tuple[int, dict | None]:
    """
    Disable a user's account without deleting them.
    This is the most common SCIM operation — when someone leaves a company!
    HTTP method: PATCH (only change the 'active' field)
    """
    body = {
        "schemas": [SCIM_PATCH_SCHEMA],
        "Operations": [
            {"op": "replace", "path": "active", "value": False}
        ],
    }
    return _call("PATCH", f"/Users/{user_id}", body)


# ─────────────────────────────────────────────────────────────────────────────
#  Update display name  →  PATCH /scim/v2/Users/<id>
# ─────────────────────────────────────────────────────────────────────────────
def update_display_name(user_id: str, new_name: str) -> tuple[int, dict | None]:
    """
    Change just the display name — leave everything else untouched.
    HTTP method: PATCH
    """
    body = {
        "schemas": [SCIM_PATCH_SCHEMA],
        "Operations": [
            {"op": "replace", "path": "displayName", "value": new_name}
        ],
    }
    return _call("PATCH", f"/Users/{user_id}", body)


# ─────────────────────────────────────────────────────────────────────────────
#  Delete a user  →  DELETE /scim/v2/Users/<id>
# ─────────────────────────────────────────────────────────────────────────────
def delete_user(user_id: str) -> tuple[int, dict | None]:
    """
    Permanently delete a user.
    HTTP method: DELETE
    Returns 204 No Content on success (nothing to show back).
    """
    return _call("DELETE", f"/Users/{user_id}")


# ─────────────────────────────────────────────────────────────────────────────
#  Get server capabilities  →  GET /scim/v2/ServiceProviderConfig
# ─────────────────────────────────────────────────────────────────────────────
def get_service_provider_config() -> tuple[int, dict | None]:
    """
    Ask the server what features it supports.
    Every proper SCIM server exposes this endpoint.
    """
    return _call("GET", "/ServiceProviderConfig")
