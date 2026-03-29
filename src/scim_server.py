"""
scim_server.py
--------------
A real (but local) SCIM 2.0 server built with Flask.

SCIM 2.0 endpoints implemented:
  GET    /scim/v2/ServiceProviderConfig  → server capabilities
  GET    /scim/v2/Users                  → list all users
  POST   /scim/v2/Users                  → create a user
  GET    /scim/v2/Users/<id>             → get one user
  PUT    /scim/v2/Users/<id>             → replace a user
  PATCH  /scim/v2/Users/<id>             → partially update a user
  DELETE /scim/v2/Users/<id>             → delete a user

The "database" is just a plain Python dictionary in memory.
Every time you restart the server the data resets — that's fine for learning!
"""

import uuid
import logging
import threading
from flask import Flask, jsonify, request

# ── Silence Flask's noisy request logs so our rich output stays clean ─────────
log = logging.getLogger("werkzeug")
log.setLevel(logging.ERROR)

app = Flask(__name__)

# ── In-memory "database" ──────────────────────────────────────────────────────
# Key   = user UUID string
# Value = full SCIM User object (a dict)
_users: dict[str, dict] = {}
_lock = threading.Lock()   # thread-safe access

SCIM_CORE_SCHEMA    = "urn:ietf:params:scim:schemas:core:2.0:User"
SCIM_LIST_SCHEMA    = "urn:ietf:params:scim:api:messages:2.0:ListResponse"
SCIM_PATCH_SCHEMA   = "urn:ietf:params:scim:api:messages:2.0:PatchOp"
SCIM_ERROR_SCHEMA   = "urn:ietf:params:scim:api:messages:2.0:Error"
SCIM_SPC_SCHEMA     = "urn:ietf:params:scim:schemas:core:2.0:ServiceProviderConfig"


def _build_user(data: dict, user_id: str = None) -> tuple[str, dict]:
    """
    Turn raw request data into a proper SCIM User object.
    Returns (user_id, user_dict).
    """
    uid = user_id or str(uuid.uuid4())
    user = {
        "schemas":     [SCIM_CORE_SCHEMA],
        "id":          uid,
        "userName":    data.get("userName", ""),
        "displayName": data.get("displayName", ""),
        "name":        data.get("name", {}),
        "emails":      data.get("emails", []),
        "active":      data.get("active", True),
        "meta": {
            "resourceType": "User",
            "location":     f"/scim/v2/Users/{uid}",
        },
    }
    return uid, user


def _scim_error(status: int, detail: str):
    """Return a standard SCIM error response."""
    return jsonify({
        "schemas": [SCIM_ERROR_SCHEMA],
        "status":  str(status),
        "detail":  detail,
    }), status


# ─────────────────────────────────────────────────────────────────────────────
#  ServiceProviderConfig — tells clients what features this server supports
# ─────────────────────────────────────────────────────────────────────────────
@app.route("/scim/v2/ServiceProviderConfig", methods=["GET"])
def service_provider_config():
    return jsonify({
        "schemas":          [SCIM_SPC_SCHEMA],
        "documentationUri": "https://github.com/Lokeshreddy0257/scim-api-explorer",
        "patch":            {"supported": True},
        "bulk":             {"supported": False, "maxOperations": 0, "maxPayloadSize": 0},
        "filter":           {"supported": True, "maxResults": 200},
        "changePassword":   {"supported": False},
        "sort":             {"supported": False},
        "etag":             {"supported": False},
        "authenticationSchemes": [
            {
                "name":        "OAuth Bearer Token",
                "description": "Authentication scheme using the OAuth Bearer Token Standard",
                "type":        "oauthbearertoken",
            }
        ],
    })


# ─────────────────────────────────────────────────────────────────────────────
#  GET /scim/v2/Users  →  list all users
# ─────────────────────────────────────────────────────────────────────────────
@app.route("/scim/v2/Users", methods=["GET"])
def list_users():
    with _lock:
        user_list = list(_users.values())

    return jsonify({
        "schemas":      [SCIM_LIST_SCHEMA],
        "totalResults": len(user_list),
        "startIndex":   1,
        "itemsPerPage": len(user_list),
        "Resources":    user_list,
    })


# ─────────────────────────────────────────────────────────────────────────────
#  POST /scim/v2/Users  →  create a new user
# ─────────────────────────────────────────────────────────────────────────────
@app.route("/scim/v2/Users", methods=["POST"])
def create_user():
    data = request.get_json(silent=True)
    if not data:
        return _scim_error(400, "Request body must be valid JSON")

    if not data.get("userName"):
        return _scim_error(400, "'userName' is required")

    # Enforce unique userName
    with _lock:
        for existing in _users.values():
            if existing["userName"] == data["userName"]:
                return _scim_error(
                    409,
                    f"User with userName '{data['userName']}' already exists"
                )

        uid, user = _build_user(data)
        _users[uid] = user

    return jsonify(user), 201


# ─────────────────────────────────────────────────────────────────────────────
#  GET /scim/v2/Users/<id>  →  fetch one user
# ─────────────────────────────────────────────────────────────────────────────
@app.route("/scim/v2/Users/<user_id>", methods=["GET"])
def get_user(user_id):
    with _lock:
        user = _users.get(user_id)
    if not user:
        return _scim_error(404, f"User '{user_id}' not found")
    return jsonify(user)


# ─────────────────────────────────────────────────────────────────────────────
#  PUT /scim/v2/Users/<id>  →  REPLACE the whole user (full update)
# ─────────────────────────────────────────────────────────────────────────────
@app.route("/scim/v2/Users/<user_id>", methods=["PUT"])
def replace_user(user_id):
    with _lock:
        if user_id not in _users:
            return _scim_error(404, f"User '{user_id}' not found")
        data = request.get_json(silent=True) or {}
        _, user = _build_user(data, user_id)
        _users[user_id] = user
    return jsonify(user)


# ─────────────────────────────────────────────────────────────────────────────
#  PATCH /scim/v2/Users/<id>  →  partial update (only change what you specify)
# ─────────────────────────────────────────────────────────────────────────────
@app.route("/scim/v2/Users/<user_id>", methods=["PATCH"])
def patch_user(user_id):
    with _lock:
        if user_id not in _users:
            return _scim_error(404, f"User '{user_id}' not found")

        data = request.get_json(silent=True) or {}
        operations = data.get("Operations", [])
        user = _users[user_id]

        for op in operations:
            action = op.get("op", "").lower()
            path   = op.get("path", "")
            value  = op.get("value")

            if action == "replace":
                if path == "active":
                    user["active"] = value
                elif path == "displayName":
                    user["displayName"] = value
                elif path == "userName":
                    user["userName"] = value
                elif not path and isinstance(value, dict):
                    # Replace multiple fields at once
                    for k, v in value.items():
                        if k not in ("id", "schemas", "meta"):
                            user[k] = v
            elif action == "add":
                if path and value is not None:
                    user[path] = value
            elif action == "remove":
                if path and path in user:
                    del user[path]

        _users[user_id] = user

    return jsonify(user)


# ─────────────────────────────────────────────────────────────────────────────
#  DELETE /scim/v2/Users/<id>  →  permanently delete a user
# ─────────────────────────────────────────────────────────────────────────────
@app.route("/scim/v2/Users/<user_id>", methods=["DELETE"])
def delete_user(user_id):
    with _lock:
        if user_id not in _users:
            return _scim_error(404, f"User '{user_id}' not found")
        del _users[user_id]
    return "", 204


# ─────────────────────────────────────────────────────────────────────────────
#  Helper to expose the in-memory store to the main script
# ─────────────────────────────────────────────────────────────────────────────
def get_users_snapshot() -> dict:
    with _lock:
        return dict(_users)


# ─────────────────────────────────────────────────────────────────────────────
#  Start the server in a background daemon thread
# ─────────────────────────────────────────────────────────────────────────────
def start(port: int = 5000):
    t = threading.Thread(
        target=lambda: app.run(port=port, debug=False, use_reloader=False),
        daemon=True,
        name="scim-server",
    )
    t.start()
    return t
