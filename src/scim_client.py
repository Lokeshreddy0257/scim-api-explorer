"""
scim_client.py
--------------
The SCIM client — what an Identity Provider (Okta, Azure AD) would run
to talk to the SCIM server.

Every function:
  1. Shows the HTTP request it's about to send   (method, URL, headers, body)
  2. Actually sends the real HTTP request
  3. Shows the HTTP response received             (status, body, timing)
  4. Returns (status_code, response_body) for further use
"""

import time
import requests
from src.visualizer import show_http_request, show_http_response

BASE_URL = "http://localhost:5000/scim/v2"

HEADERS = {
    "Content-Type":  "application/scim+json",
    "Accept":        "application/scim+json",
    "Authorization": "Bearer demo-token-abc123",
}

SCIM_USER_SCHEMA  = "urn:ietf:params:scim:schemas:core:2.0:User"
SCIM_GROUP_SCHEMA = "urn:ietf:params:scim:schemas:core:2.0:Group"
SCIM_PATCH_SCHEMA = "urn:ietf:params:scim:api:messages:2.0:PatchOp"


def _call(method: str, path: str, body: dict = None) -> tuple[int, dict | None]:
    url   = BASE_URL + path
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
#  Users
# ─────────────────────────────────────────────────────────────────────────────

def list_users() -> tuple[int, dict | None]:
    """GET /scim/v2/Users — fetch all users."""
    return _call("GET", "/Users")


def create_user(
    username:     str,
    display_name: str,
    email:        str,
    first_name:   str = "",
    last_name:    str = "",
    department:   str = "",
) -> tuple[int, dict | None]:
    """POST /scim/v2/Users — create a new user."""
    body = {
        "schemas":     [SCIM_USER_SCHEMA],
        "userName":    username,
        "displayName": display_name,
        "name":        {"givenName": first_name, "familyName": last_name},
        "emails":      [{"value": email, "type": "work", "primary": True}],
        "active":      True,
        "department":  department,
    }
    return _call("POST", "/Users", body)


def get_user(user_id: str) -> tuple[int, dict | None]:
    """GET /scim/v2/Users/<id> — fetch a single user."""
    return _call("GET", f"/Users/{user_id}")


def replace_user(user_id: str, username: str, display_name: str, email: str) -> tuple[int, dict | None]:
    """PUT /scim/v2/Users/<id> — full replacement."""
    body = {
        "schemas":     [SCIM_USER_SCHEMA],
        "userName":    username,
        "displayName": display_name,
        "emails":      [{"value": email, "type": "work", "primary": True}],
        "active":      True,
    }
    return _call("PUT", f"/Users/{user_id}", body)


def deactivate_user(user_id: str) -> tuple[int, dict | None]:
    """PATCH active=false — disable without deleting (offboarding/termination step 1)."""
    body = {
        "schemas":    [SCIM_PATCH_SCHEMA],
        "Operations": [{"op": "replace", "path": "active", "value": False}],
    }
    return _call("PATCH", f"/Users/{user_id}", body)


def activate_user(user_id: str) -> tuple[int, dict | None]:
    """PATCH active=true — re-enable a previously deactivated account."""
    body = {
        "schemas":    [SCIM_PATCH_SCHEMA],
        "Operations": [{"op": "replace", "path": "active", "value": True}],
    }
    return _call("PATCH", f"/Users/{user_id}", body)


def update_display_name(user_id: str, new_name: str) -> tuple[int, dict | None]:
    """PATCH displayName — change display name, leave everything else untouched."""
    body = {
        "schemas":    [SCIM_PATCH_SCHEMA],
        "Operations": [{"op": "replace", "path": "displayName", "value": new_name}],
    }
    return _call("PATCH", f"/Users/{user_id}", body)


def update_department(user_id: str, department: str) -> tuple[int, dict | None]:
    """PATCH department — used when an employee moves teams."""
    body = {
        "schemas":    [SCIM_PATCH_SCHEMA],
        "Operations": [{"op": "replace", "path": "department", "value": department}],
    }
    return _call("PATCH", f"/Users/{user_id}", body)


def delete_user(user_id: str) -> tuple[int, dict | None]:
    """DELETE /scim/v2/Users/<id> — permanent removal."""
    return _call("DELETE", f"/Users/{user_id}")


# ─────────────────────────────────────────────────────────────────────────────
#  Groups
# ─────────────────────────────────────────────────────────────────────────────

def list_groups() -> tuple[int, dict | None]:
    """GET /scim/v2/Groups — fetch all groups."""
    return _call("GET", "/Groups")


def create_group(
    display_name: str,
    member_ids:   list[str] | None = None,
) -> tuple[int, dict | None]:
    """POST /scim/v2/Groups — create an AD group (optionally with initial members)."""
    body = {
        "schemas":     [SCIM_GROUP_SCHEMA],
        "displayName": display_name,
        "members":     [{"value": uid} for uid in (member_ids or [])],
    }
    return _call("POST", "/Groups", body)


def get_group(group_id: str) -> tuple[int, dict | None]:
    """GET /scim/v2/Groups/<id> — fetch one group."""
    return _call("GET", f"/Groups/{group_id}")


def add_group_member(
    group_id:     str,
    user_id:      str,
    display_name: str = "",
) -> tuple[int, dict | None]:
    """
    PATCH /scim/v2/Groups/<id> — add a user to a group.
    This is what grants Databricks workspace access.
    """
    body = {
        "schemas":    [SCIM_PATCH_SCHEMA],
        "Operations": [{
            "op":    "add",
            "path":  "members",
            "value": [{"value": user_id, "display": display_name}],
        }],
    }
    return _call("PATCH", f"/Groups/{group_id}", body)


def remove_group_member(group_id: str, user_id: str) -> tuple[int, dict | None]:
    """
    PATCH /scim/v2/Groups/<id> — remove a user from a group.
    Uses the filter-path syntax that Okta/Azure AD send in production:
      members[value eq "<user_id>"]
    """
    body = {
        "schemas":    [SCIM_PATCH_SCHEMA],
        "Operations": [{
            "op":   "remove",
            "path": f'members[value eq "{user_id}"]',
        }],
    }
    return _call("PATCH", f"/Groups/{group_id}", body)


def delete_group(group_id: str) -> tuple[int, dict | None]:
    """DELETE /scim/v2/Groups/<id> — permanently delete a group."""
    return _call("DELETE", f"/Groups/{group_id}")


# ─────────────────────────────────────────────────────────────────────────────
#  Server capabilities
# ─────────────────────────────────────────────────────────────────────────────

def get_service_provider_config() -> tuple[int, dict | None]:
    """GET /scim/v2/ServiceProviderConfig — discover server features."""
    return _call("GET", "/ServiceProviderConfig")
