"""
scim_server.py
--------------
A real (but local) SCIM 2.0 server built with Flask.

SCIM 2.0 endpoints implemented:
  Users:
    GET    /scim/v2/ServiceProviderConfig
    GET    /scim/v2/Users
    POST   /scim/v2/Users
    GET    /scim/v2/Users/<id>
    PUT    /scim/v2/Users/<id>
    PATCH  /scim/v2/Users/<id>
    DELETE /scim/v2/Users/<id>

  Groups:
    GET    /scim/v2/Groups
    POST   /scim/v2/Groups
    GET    /scim/v2/Groups/<id>
    PATCH  /scim/v2/Groups/<id>
    DELETE /scim/v2/Groups/<id>

Data is stored in plain Python dicts in memory.
The audit_log is append-only and survives reset_state() calls.
"""

import re
import uuid
import logging
import threading
from datetime import datetime, timezone
from flask import Flask, jsonify, request

log = logging.getLogger("werkzeug")
log.setLevel(logging.ERROR)

app = Flask(__name__)

# ── In-memory stores ──────────────────────────────────────────────────────────
_users:     dict[str, dict] = {}
_groups:    dict[str, dict] = {}
_audit_log: list[dict]      = []   # append-only; NOT cleared by reset_state()
_lock = threading.Lock()

# ── SCIM schema URNs ──────────────────────────────────────────────────────────
SCIM_USER_SCHEMA  = "urn:ietf:params:scim:schemas:core:2.0:User"
SCIM_GROUP_SCHEMA = "urn:ietf:params:scim:schemas:core:2.0:Group"
SCIM_LIST_SCHEMA  = "urn:ietf:params:scim:api:messages:2.0:ListResponse"
SCIM_PATCH_SCHEMA = "urn:ietf:params:scim:api:messages:2.0:PatchOp"
SCIM_ERROR_SCHEMA = "urn:ietf:params:scim:api:messages:2.0:Error"
SCIM_SPC_SCHEMA   = "urn:ietf:params:scim:schemas:core:2.0:ServiceProviderConfig"

# ── Audit event constants ─────────────────────────────────────────────────────
USER_CREATED            = "USER_CREATED"
USER_UPDATED            = "USER_UPDATED"
USER_ACTIVATED          = "USER_ACTIVATED"
USER_DEACTIVATED        = "USER_DEACTIVATED"
USER_DELETED            = "USER_DELETED"
GROUP_CREATED           = "GROUP_CREATED"
GROUP_DELETED           = "GROUP_DELETED"
GROUP_MEMBER_ADDED      = "GROUP_MEMBER_ADDED"
GROUP_MEMBER_REMOVED    = "GROUP_MEMBER_REMOVED"
VERIFICATION_DRIFT_DETECTED = "VERIFICATION_DRIFT_DETECTED"
VERIFICATION_DRIFT_FIXED    = "VERIFICATION_DRIFT_FIXED"
RECERT_REVIEW_STARTED   = "RECERT_REVIEW_STARTED"
RECERT_ACCESS_REVOKED   = "RECERT_ACCESS_REVOKED"
RECERT_ACCESS_APPROVED  = "RECERT_ACCESS_APPROVED"


# ─────────────────────────────────────────────────────────────────────────────
#  Audit helper (exported — lifecycle.py also calls this)
# ─────────────────────────────────────────────────────────────────────────────
def audit(
    event:         str,
    resource_type: str,
    resource_id:   str,
    resource_name: str,
    detail:        str = "",
    actor:         str = "scim-provisioner",
    scenario:      str = "",
):
    entry = {
        "timestamp":     datetime.now(timezone.utc).isoformat(),
        "event":         event,
        "actor":         actor,
        "resource_type": resource_type,
        "resource_id":   resource_id,
        "resource_name": resource_name,
        "detail":        detail,
        "scenario":      scenario,
    }
    with _lock:
        _audit_log.append(entry)


# ─────────────────────────────────────────────────────────────────────────────
#  Object builders
# ─────────────────────────────────────────────────────────────────────────────
def _build_user(data: dict, user_id: str = None) -> tuple[str, dict]:
    uid = user_id or str(uuid.uuid4())
    return uid, {
        "schemas":     [SCIM_USER_SCHEMA],
        "id":          uid,
        "userName":    data.get("userName", ""),
        "displayName": data.get("displayName", ""),
        "name":        data.get("name", {}),
        "emails":      data.get("emails", []),
        "active":      data.get("active", True),
        "department":  data.get("department", ""),
        "meta": {
            "resourceType": "User",
            "location":     f"/scim/v2/Users/{uid}",
        },
    }


def _build_group(data: dict, group_id: str = None) -> tuple[str, dict]:
    gid = group_id or str(uuid.uuid4())
    return gid, {
        "schemas":     [SCIM_GROUP_SCHEMA],
        "id":          gid,
        "displayName": data.get("displayName", ""),
        "members":     list(data.get("members", [])),
        "meta": {
            "resourceType": "Group",
            "location":     f"/scim/v2/Groups/{gid}",
        },
    }


def _scim_error(status: int, detail: str):
    return jsonify({
        "schemas": [SCIM_ERROR_SCHEMA],
        "status":  str(status),
        "detail":  detail,
    }), status


# ─────────────────────────────────────────────────────────────────────────────
#  ServiceProviderConfig
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
        "authenticationSchemes": [{
            "name":        "OAuth Bearer Token",
            "description": "Authentication using the OAuth Bearer Token Standard",
            "type":        "oauthbearertoken",
        }],
    })


# ─────────────────────────────────────────────────────────────────────────────
#  Users
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


@app.route("/scim/v2/Users", methods=["POST"])
def create_user():
    data = request.get_json(silent=True)
    if not data:
        return _scim_error(400, "Request body must be valid JSON")
    if not data.get("userName"):
        return _scim_error(400, "'userName' is required")
    with _lock:
        for existing in _users.values():
            if existing["userName"] == data["userName"]:
                return _scim_error(409, f"User '{data['userName']}' already exists")
        uid, user = _build_user(data)
        _users[uid] = user
    audit(USER_CREATED, "User", uid, data["userName"])
    return jsonify(user), 201


@app.route("/scim/v2/Users/<user_id>", methods=["GET"])
def get_user(user_id):
    with _lock:
        user = _users.get(user_id)
    if not user:
        return _scim_error(404, f"User '{user_id}' not found")
    return jsonify(user)


@app.route("/scim/v2/Users/<user_id>", methods=["PUT"])
def replace_user(user_id):
    with _lock:
        if user_id not in _users:
            return _scim_error(404, f"User '{user_id}' not found")
        data = request.get_json(silent=True) or {}
        _, user = _build_user(data, user_id)
        _users[user_id] = user
    audit(USER_UPDATED, "User", user_id, user.get("userName", ""))
    return jsonify(user)


@app.route("/scim/v2/Users/<user_id>", methods=["PATCH"])
def patch_user(user_id):
    with _lock:
        if user_id not in _users:
            return _scim_error(404, f"User '{user_id}' not found")
        data       = request.get_json(silent=True) or {}
        operations = data.get("Operations", [])
        user       = _users[user_id]

        for op in operations:
            action = op.get("op", "").lower()
            path   = op.get("path", "")
            value  = op.get("value")
            if action == "replace":
                if path in ("active", "displayName", "userName", "department"):
                    user[path] = value
                elif not path and isinstance(value, dict):
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

    # Emit the most specific audit event
    for op in operations:
        pth = op.get("path", "")
        val = op.get("value")
        if pth == "active" and val is False:
            audit(USER_DEACTIVATED, "User", user_id, user.get("userName", ""))
        elif pth == "active" and val is True:
            audit(USER_ACTIVATED, "User", user_id, user.get("userName", ""))
        else:
            audit(USER_UPDATED, "User", user_id, user.get("userName", ""))
        break

    return jsonify(user)


@app.route("/scim/v2/Users/<user_id>", methods=["DELETE"])
def delete_user(user_id):
    with _lock:
        if user_id not in _users:
            return _scim_error(404, f"User '{user_id}' not found")
        username = _users[user_id].get("userName", "")
        del _users[user_id]
    audit(USER_DELETED, "User", user_id, username)
    return "", 204


# ─────────────────────────────────────────────────────────────────────────────
#  Groups
# ─────────────────────────────────────────────────────────────────────────────
@app.route("/scim/v2/Groups", methods=["GET"])
def list_groups():
    with _lock:
        group_list = list(_groups.values())
    return jsonify({
        "schemas":      [SCIM_LIST_SCHEMA],
        "totalResults": len(group_list),
        "startIndex":   1,
        "itemsPerPage": len(group_list),
        "Resources":    group_list,
    })


@app.route("/scim/v2/Groups", methods=["POST"])
def create_group():
    data = request.get_json(silent=True)
    if not data:
        return _scim_error(400, "Request body must be valid JSON")
    if not data.get("displayName"):
        return _scim_error(400, "'displayName' is required")
    with _lock:
        for existing in _groups.values():
            if existing["displayName"] == data["displayName"]:
                return _scim_error(409, f"Group '{data['displayName']}' already exists")
        gid, group = _build_group(data)
        _groups[gid] = group
    audit(GROUP_CREATED, "Group", gid, data["displayName"])
    return jsonify(group), 201


@app.route("/scim/v2/Groups/<group_id>", methods=["GET"])
def get_group(group_id):
    with _lock:
        group = _groups.get(group_id)
    if not group:
        return _scim_error(404, f"Group '{group_id}' not found")
    return jsonify(group)


@app.route("/scim/v2/Groups/<group_id>", methods=["PATCH"])
def patch_group(group_id):
    with _lock:
        if group_id not in _groups:
            return _scim_error(404, f"Group '{group_id}' not found")
        data       = request.get_json(silent=True) or {}
        operations = data.get("Operations", [])
        group      = _groups[group_id]

        for op in operations:
            action = op.get("op", "").lower()
            path   = op.get("path", "")
            value  = op.get("value")

            if action == "replace" and not path and isinstance(value, dict):
                group["displayName"] = value.get("displayName", group["displayName"])

            elif action == "add" and "members" in path:
                new_members  = value if isinstance(value, list) else [value]
                existing_ids = {m["value"] for m in group["members"]}
                for m in new_members:
                    if m.get("value") and m["value"] not in existing_ids:
                        group["members"].append(m)
                        audit(
                            GROUP_MEMBER_ADDED, "GroupMembership", group_id,
                            group["displayName"],
                            detail=f"Added {m.get('display', m.get('value',''))}",
                        )

            elif action == "remove" and "members" in path:
                # filter-path syntax: members[value eq "<user_id>"]
                filter_match = re.search(r'value eq "([^"]+)"', path)
                if filter_match:
                    remove_id = filter_match.group(1)
                    removed   = [m for m in group["members"] if m["value"] == remove_id]
                    group["members"] = [m for m in group["members"] if m["value"] != remove_id]
                    for m in removed:
                        audit(
                            GROUP_MEMBER_REMOVED, "GroupMembership", group_id,
                            group["displayName"],
                            detail=f"Removed {m.get('display', remove_id)}",
                        )
                elif value:
                    remove_ids = {m["value"] for m in (value if isinstance(value, list) else [value])}
                    removed    = [m for m in group["members"] if m["value"] in remove_ids]
                    group["members"] = [m for m in group["members"] if m["value"] not in remove_ids]
                    for m in removed:
                        audit(
                            GROUP_MEMBER_REMOVED, "GroupMembership", group_id,
                            group["displayName"],
                            detail=f"Removed {m.get('display', m['value'])}",
                        )

        _groups[group_id] = group
    return jsonify(group)


@app.route("/scim/v2/Groups/<group_id>", methods=["DELETE"])
def delete_group(group_id):
    with _lock:
        if group_id not in _groups:
            return _scim_error(404, f"Group '{group_id}' not found")
        name = _groups[group_id].get("displayName", "")
        del _groups[group_id]
    audit(GROUP_DELETED, "Group", group_id, name)
    return "", 204


# ─────────────────────────────────────────────────────────────────────────────
#  Exported snapshot helpers
# ─────────────────────────────────────────────────────────────────────────────
def get_users_snapshot() -> dict:
    with _lock:
        return dict(_users)


def get_groups_snapshot() -> dict:
    with _lock:
        return dict(_groups)


def get_audit_log_snapshot() -> list:
    with _lock:
        return list(_audit_log)


def get_group_members(group_id: str) -> list:
    with _lock:
        return list(_groups.get(group_id, {}).get("members", []))


def reset_state():
    """Clear users and groups for a fresh scenario. Audit log is preserved."""
    with _lock:
        _users.clear()
        _groups.clear()


# ─────────────────────────────────────────────────────────────────────────────
#  Server startup (background daemon thread)
# ─────────────────────────────────────────────────────────────────────────────
def start(port: int = 5000):
    t = threading.Thread(
        target=lambda: app.run(port=port, debug=False, use_reloader=False),
        daemon=True,
        name="scim-server",
    )
    t.start()
    return t
