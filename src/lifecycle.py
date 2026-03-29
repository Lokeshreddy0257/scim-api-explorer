"""
lifecycle.py
------------
The five enterprise identity lifecycle scenarios.

Each scenario:
  - Seeds its own data if no context is passed (so you can run any scenario
    independently from the main menu).
  - Makes real HTTP calls via scim_client (all requests/responses are shown).
  - Records events in the server-side audit log.
  - Ends with a visual summary.
"""

from src import scim_server, scim_client
from src.visualizer import (
    console, show_section, show_step, show_explanation,
    show_user_directory, show_groups_directory, show_access_matrix,
    show_audit_log, show_verification_report, show_recert_report,
    show_lifecycle_summary, pause,
)


# ─────────────────────────────────────────────────────────────────────────────
#  Scenario 1 — Onboarding
# ─────────────────────────────────────────────────────────────────────────────

def run_onboarding() -> dict:
    """
    Business story: Sarah Chen joins Databricks as a Data Engineer.
    HR triggers SCIM provisioning via the Identity Provider.

    What happens:
      1. The AD group 'data-engineering' is registered in SCIM (POST /Groups)
      2. Sarah's user account is created                  (POST /Users)
      3. Sarah is added to the group                      (PATCH /Groups/<id>)
      4. Databricks sees the group membership → grants workspace access
    """
    show_explanation(
        "🚀", "Scenario 1 — Onboarding",
        """
  [bold]Business story:[/bold]  Sarah Chen has just been hired as a Data Engineer.
  HR adds her to the company's Identity Provider (Okta / Azure AD).
  The IdP fires SCIM calls to register her in every connected system.

  [bold yellow]What you'll see:[/bold yellow]
    Step 1 → Create the AD group 'data-engineering'  (POST /Groups)
    Step 2 → Create Sarah's user account             (POST /Users)
    Step 3 → Add Sarah to the group                  (PATCH /Groups/<id>)
    Step 4 → Access matrix showing her new access
        """,
        "cyan",
    )
    pause("Press [Enter] to start onboarding…")

    # Step 1: Create the AD group
    show_step(1, "Register AD group in SCIM", "POST /scim/v2/Groups")
    _, grp = scim_client.create_group("data-engineering")
    group_id = grp["id"]
    scim_server.audit(
        scim_server.GROUP_CREATED, "Group", group_id, "data-engineering",
        detail="Registered for Databricks workspace access", scenario="onboarding",
    )

    # Step 2: Create the user
    show_step(2, "Provision Sarah Chen's account", "POST /scim/v2/Users")
    _, user = scim_client.create_user(
        "sarah.chen", "Sarah Chen", "sarah.chen@company.com",
        "Sarah", "Chen", "Data Engineering",
    )
    user_id = user["id"]
    scim_server.audit(
        scim_server.USER_CREATED, "User", user_id, "sarah.chen",
        detail="New hire — Data Engineering", scenario="onboarding",
    )

    # Step 3: Add Sarah to the group
    show_step(3, "Add Sarah to data-engineering group", "PATCH /scim/v2/Groups/<id>")
    scim_client.add_group_member(group_id, user_id, "Sarah Chen")
    scim_server.audit(
        scim_server.GROUP_MEMBER_ADDED, "GroupMembership", group_id, "data-engineering",
        detail="sarah.chen added — grants Databricks workspace access", scenario="onboarding",
    )

    # Step 4: Visual result
    show_step(4, "Access matrix — Sarah's current access")
    show_user_directory(scim_server.get_users_snapshot())
    show_groups_directory(scim_server.get_groups_snapshot())
    show_access_matrix(scim_server.get_users_snapshot(), scim_server.get_groups_snapshot())

    show_explanation(
        "💡", "What Databricks does on receiving group membership",
        """
  When Databricks receives a PATCH /Groups with a new member,
  it automatically:
    • Creates a workspace user (if not already present)
    • Assigns the default role configured for that AD group
    • Logs the provisioning event in Databricks' own audit log
    • Sends a welcome email (if configured)

  No manual action by a Databricks admin is needed.
        """,
        "green",
    )

    show_lifecycle_summary("onboarding", scim_server.get_audit_log_snapshot(),
        "Creates workspace user + assigns role based on AD group → Databricks access granted")
    pause()

    return {"user_id": user_id, "group_id": group_id, "username": "sarah.chen"}


# ─────────────────────────────────────────────────────────────────────────────
#  Scenario 2 — Offboarding (team transfer)
# ─────────────────────────────────────────────────────────────────────────────

def _seed_offboarding() -> dict:
    """Create prerequisite state for offboarding when run standalone."""
    _, grp_de  = scim_client.create_group("data-engineering")
    _, grp_ml  = scim_client.create_group("ml-platform")
    _, user    = scim_client.create_user(
        "sarah.chen", "Sarah Chen", "sarah.chen@company.com",
        "Sarah", "Chen", "Data Engineering",
    )
    uid = user["id"]
    scim_client.add_group_member(grp_de["id"], uid, "Sarah Chen")
    return {"user_id": uid, "group_id": grp_de["id"],
            "ml_group_id": grp_ml["id"], "username": "sarah.chen"}


def run_offboarding(context: dict) -> dict:
    """
    Business story: Sarah transfers from Data Engineering to ML Platform.
    She must lose DE Databricks access and gain ML Platform access.

    What happens:
      1. New group 'ml-platform' is created (or already exists)
      2. Sarah is removed from 'data-engineering'   (PATCH remove member)
      3. Sarah is added to 'ml-platform'             (PATCH add member)
      4. Her department is updated                   (PATCH /Users/<id>)
    """
    if not context.get("user_id"):
        console.print("  [dim]Seeding prerequisite state for offboarding demo…[/dim]")
        context = _seed_offboarding()

    user_id  = context["user_id"]
    de_gid   = context["group_id"]

    show_explanation(
        "🔄", "Scenario 2 — Offboarding (Team Transfer)",
        """
  [bold]Business story:[/bold]  Sarah Chen transfers from Data Engineering → ML Platform.
  The old team's Databricks workspace must be revoked; the new one granted.

  [bold yellow]What you'll see:[/bold yellow]
    Step 1 → Create ML Platform group                    (POST /Groups)
    Step 2 → Remove Sarah from data-engineering          (PATCH — remove member)
    Step 3 → Add Sarah to ml-platform                    (PATCH — add member)
    Step 4 → Update Sarah's department                   (PATCH /Users/<id>)
    Step 5 → Access matrix showing the swap
        """,
        "yellow",
    )
    pause("Press [Enter] to start offboarding…")

    # Step 1: Ensure ml-platform group exists
    show_step(1, "Create ML Platform AD group", "POST /scim/v2/Groups")
    if context.get("ml_group_id"):
        ml_gid = context["ml_group_id"]
        console.print("  [dim](Group already exists from seeded state)[/dim]")
    else:
        _, ml_grp = scim_client.create_group("ml-platform")
        ml_gid = ml_grp["id"]
    scim_server.audit(
        scim_server.GROUP_CREATED, "Group", ml_gid, "ml-platform",
        detail="New team group for ML Platform", scenario="offboarding",
    )

    # Step 2: Remove from old group
    show_step(2, "Remove Sarah from data-engineering", "PATCH — remove member")
    scim_client.remove_group_member(de_gid, user_id)
    scim_server.audit(
        scim_server.GROUP_MEMBER_REMOVED, "GroupMembership", de_gid, "data-engineering",
        detail="sarah.chen transferred out — DE access revoked", scenario="offboarding",
    )

    # Step 3: Add to new group
    show_step(3, "Add Sarah to ml-platform group", "PATCH — add member")
    scim_client.add_group_member(ml_gid, user_id, "Sarah Chen")
    scim_server.audit(
        scim_server.GROUP_MEMBER_ADDED, "GroupMembership", ml_gid, "ml-platform",
        detail="sarah.chen transferred in — ML Platform access granted", scenario="offboarding",
    )

    # Step 4: Update department
    show_step(4, "Update Sarah's department", "PATCH /scim/v2/Users/<id>")
    scim_client.update_department(user_id, "ML Platform")
    scim_server.audit(
        scim_server.USER_UPDATED, "User", user_id, "sarah.chen",
        detail="Department updated: Data Engineering → ML Platform", scenario="offboarding",
    )

    # Step 5: Visual result
    show_step(5, "Updated access matrix")
    show_access_matrix(scim_server.get_users_snapshot(), scim_server.get_groups_snapshot())

    show_explanation(
        "💡", "What Databricks does on a group membership change",
        """
  When Databricks receives a PATCH /Groups with a member removed:
    • It immediately revokes that user's access to the old workspace
    • Any active sessions are terminated (depending on SSO config)

  When a new group membership is added:
    • Access to the new workspace is provisioned automatically
    • The user's role/permissions are inherited from the group's policy
        """,
        "yellow",
    )

    show_lifecycle_summary("offboarding", scim_server.get_audit_log_snapshot(),
        "Revokes old workspace via group removal → grants new workspace via group add")
    pause()

    return {**context, "ml_group_id": ml_gid}


# ─────────────────────────────────────────────────────────────────────────────
#  Scenario 3 — Termination
# ─────────────────────────────────────────────────────────────────────────────

def _seed_termination() -> dict:
    """Create prerequisite state for termination when run standalone."""
    _, grp  = scim_client.create_group("data-engineering")
    _, grp2 = scim_client.create_group("ml-platform")
    _, user = scim_client.create_user(
        "marcus.webb", "Marcus Webb", "marcus.webb@company.com",
        "Marcus", "Webb", "Data Engineering",
    )
    uid = user["id"]
    scim_client.add_group_member(grp["id"],  uid, "Marcus Webb")
    scim_client.add_group_member(grp2["id"], uid, "Marcus Webb")
    return {"user_id": uid, "username": "marcus.webb",
            "groups": [grp["id"], grp2["id"]]}


def run_termination(context: dict):
    """
    Business story: Marcus Webb resigns. All system access must be
    revoked within the SLA. The safe two-step pattern is:
      1. Deactivate (immediate lockout — active=false)
      2. Remove from all groups
      3. Delete the user record

    Why two steps? Deactivation gives you a recovery window if it's
    a mistake. Deletion is permanent.
    """
    if not context.get("user_id"):
        console.print("  [dim]Seeding prerequisite state for termination demo…[/dim]")
        context = _seed_termination()

    user_id  = context["user_id"]
    username = context.get("username", "marcus.webb")

    # Resolve which groups this user belongs to
    all_groups = scim_server.get_groups_snapshot()
    user_groups = [
        (gid, g["displayName"])
        for gid, g in all_groups.items()
        if any(m["value"] == user_id for m in g.get("members", []))
    ]

    show_explanation(
        "🚪", "Scenario 3 — Termination",
        """
  [bold]Business story:[/bold]  Marcus Webb has resigned. Last day notification
  received from HR. All Databricks access must be revoked immediately.

  [bold yellow]What you'll see:[/bold yellow]
    Step 1 → Immediate lockout: deactivate account   (PATCH active=false)
    Step 2 → Remove from all groups                  (PATCH — remove member × N)
    Step 3 → Delete the user permanently             (DELETE /Users/<id>)
    Step 4 → Confirm: empty user list + audit trail
        """,
        "red",
    )
    pause("Press [Enter] to start termination…")

    # Step 1: Immediate deactivation
    show_step(1, "Immediate lockout — deactivate account", "PATCH active=false")
    scim_client.deactivate_user(user_id)
    scim_server.audit(
        scim_server.USER_DEACTIVATED, "User", user_id, username,
        detail="Termination — immediate lockout, active=false", scenario="termination",
    )

    # Step 2: Remove from every group
    show_step(2, f"Remove from {len(user_groups)} group(s)", "PATCH — remove member")
    for gid, gname in user_groups:
        scim_client.remove_group_member(gid, user_id)
        scim_server.audit(
            scim_server.GROUP_MEMBER_REMOVED, "GroupMembership", gid, gname,
            detail=f"Termination — {username} removed", scenario="termination",
        )

    # Step 3: Permanent deletion
    show_step(3, "Permanently delete user record", "DELETE /scim/v2/Users/<id>")
    scim_client.delete_user(user_id)
    scim_server.audit(
        scim_server.USER_DELETED, "User", user_id, username,
        detail="Termination — account permanently deleted", scenario="termination",
    )

    # Step 4: Final state
    show_step(4, "Final state — all access revoked")
    show_user_directory(scim_server.get_users_snapshot())
    show_groups_directory(scim_server.get_groups_snapshot())

    show_explanation(
        "💡", "Why deactivate-then-delete is the safe pattern",
        """
  [bold]Deactivate first (PATCH active=false):[/bold]
    • User is locked out immediately — no new logins possible
    • The record still exists, so the audit trail is intact
    • If it was a mistake (wrong person!), you can re-enable with PATCH active=true
    • Gives a grace period to export their work or reassign assets

  [bold]Delete after (DELETE /Users/<id>):[/bold]
    • Permanent — cannot be undone
    • Typically done after a waiting period (e.g. 30 days)
    • Removes the record from active directory sync

  [bold]Most compliance frameworks (SOC 2, ISO 27001) require:[/bold]
    • Deactivation within 24 hours of termination notice
    • Complete removal within 30 days
        """,
        "red",
    )

    show_lifecycle_summary("termination", scim_server.get_audit_log_snapshot(),
        "Immediate deactivation → group removal → permanent deletion. Audit trail preserved.")
    pause()


# ─────────────────────────────────────────────────────────────────────────────
#  Scenario 4 — Recertification
# ─────────────────────────────────────────────────────────────────────────────

def run_recertification():
    """
    Business story: Quarterly (90-day) access review.
    A manager reviews 4 employees' Databricks access.
    3 are approved. 1 stale account (hasn't used access in 95 days) is revoked.
    """
    # Seed state
    console.print("  [dim]Setting up 4 users and 2 groups for recertification review…[/dim]")
    _, grp_de  = scim_client.create_group("data-engineering")
    _, grp_ml  = scim_client.create_group("ml-platform")
    de_id  = grp_de["id"]
    ml_id  = grp_ml["id"]

    users_data = [
        ("alice.johnson", "Alice Johnson",  "alice@co.com",   "Alice",   "Johnson", "DE",  de_id),
        ("bob.smith",     "Bob Smith",      "bob@co.com",     "Bob",     "Smith",   "DE",  de_id),
        ("carol.white",   "Carol White",    "carol@co.com",   "Carol",   "White",   "ML",  ml_id),
        ("dan.old",       "Dan Old",        "dan@co.com",     "Dan",     "Old",     "DE",  de_id),
    ]

    created = []
    for uname, dname, email, fn, ln, dept, gid in users_data:
        _, u = scim_client.create_user(uname, dname, email, fn, ln, dept)
        scim_client.add_group_member(gid, u["id"], dname)
        created.append(u)

    scim_server.audit(
        scim_server.RECERT_REVIEW_STARTED, "Review", "q1-2026", "Q1 2026 Recertification",
        detail="Quarterly access review initiated", scenario="recertification",
    )

    show_explanation(
        "📋", "Scenario 4 — 90-Day Recertification",
        """
  [bold]Business story:[/bold]  It's the end of Q1. Compliance requires a 90-day
  access review for all Databricks users. A manager reviews each account.

  [bold yellow]What you'll see:[/bold yellow]
    Step 1 → Current access matrix (4 users, 2 groups)
    Step 2 → Recertification report: who gets approved vs revoked
    Step 3 → SCIM calls to revoke stale access
    Step 4 → Updated access matrix after review
        """,
        "cyan",
    )
    pause("Press [Enter] to start recertification review…")

    # Step 1: Current state
    show_step(1, "Current access before review")
    show_access_matrix(scim_server.get_users_snapshot(), scim_server.get_groups_snapshot())
    pause()

    # Step 2: Recertification report
    show_step(2, "Manager's recertification review")
    group_names = {"data-engineering": de_id, "ml-platform": ml_id}
    gid_to_name = {v: k for k, v in group_names.items()}

    recert_entries = [
        {"display_name": "Alice Johnson", "username": "alice.johnson",
         "group": "data-engineering", "days_since_cert": 45,  "decision": "approved"},
        {"display_name": "Bob Smith",     "username": "bob.smith",
         "group": "data-engineering", "days_since_cert": 62,  "decision": "approved"},
        {"display_name": "Carol White",   "username": "carol.white",
         "group": "ml-platform",      "days_since_cert": 30,  "decision": "approved"},
        {"display_name": "Dan Old",       "username": "dan.old",
         "group": "data-engineering", "days_since_cert": 95,  "decision": "revoked"},
    ]
    show_recert_report(recert_entries)
    console.print(
        "\n  [dim]Dan Old's access was last certified 95 days ago — [bold red]REVOKED[/bold red][/dim]\n"
    )
    pause()

    # Step 3: Revoke stale access
    show_step(3, "Revoke Dan Old's stale access")
    dan_user = next(u for u in created if u["userName"] == "dan.old")
    dan_id   = dan_user["id"]

    scim_client.deactivate_user(dan_id)
    scim_client.remove_group_member(de_id, dan_id)
    scim_server.audit(
        scim_server.RECERT_ACCESS_REVOKED, "User", dan_id, "dan.old",
        detail="Stale access (95 days) — revoked during Q1 recertification", scenario="recertification",
    )
    for e in recert_entries:
        if e["decision"] == "approved":
            scim_server.audit(
                scim_server.RECERT_ACCESS_APPROVED, "User", "N/A", e["username"],
                detail=f"Approved by manager — {e['days_since_cert']} days since last cert", scenario="recertification",
            )

    # Step 4: Updated access matrix
    show_step(4, "Access matrix after review")
    show_access_matrix(scim_server.get_users_snapshot(), scim_server.get_groups_snapshot())

    show_explanation(
        "💡", "Why recertification is required (SOC 2 / ISO 27001)",
        """
  [bold]Access creep:[/bold]
    Over time, people accumulate access they no longer use.
    Someone who moved teams, got a different role, or just stopped
    using Databricks still has active credentials — a security risk.

  [bold]Compliance requirement:[/bold]
    • SOC 2 Type II — periodic review of privileged access
    • ISO 27001 — A.9.2.5 Review of user access rights
    • Databricks internal policy — 90-day review cycle

  [bold]SCIM makes it easy:[/bold]
    One PATCH call per revocation, fully audited, no manual admin work.
        """,
        "cyan",
    )

    show_lifecycle_summary("recertification", scim_server.get_audit_log_snapshot(),
        "Stale accounts deactivated + removed from groups. All decisions logged for auditors.")
    pause()


# ─────────────────────────────────────────────────────────────────────────────
#  Scenario 5 — Nightly Verification
# ─────────────────────────────────────────────────────────────────────────────

def run_verification():
    """
    Business story: Nightly automated job (runs at 2 AM) compares the
    AD source of truth (expected state) against the live Databricks SCIM
    server (actual state). Detects drift and auto-corrects it.

    Two types of drift injected for the demo:
      A) A user exists in AD but was manually deleted from Databricks
         → re-provision them
      B) A user was manually added to a Databricks group without going
         through AD → remove them (unauthorized access)
    """
    # Seed expected state (the "AD source of truth")
    console.print("  [dim]Building expected state from AD source of truth…[/dim]")
    _, grp_de  = scim_client.create_group("data-engineering")
    _, grp_ml  = scim_client.create_group("ml-platform")
    de_id = grp_de["id"]
    ml_id = grp_ml["id"]

    _, alice  = scim_client.create_user("alice.johnson", "Alice Johnson", "alice@co.com", "Alice", "Johnson")
    _, bob    = scim_client.create_user("bob.smith",     "Bob Smith",     "bob@co.com",   "Bob",   "Smith")
    _, carol  = scim_client.create_user("carol.white",   "Carol White",   "carol@co.com", "Carol", "White")

    scim_client.add_group_member(de_id, alice["id"], "Alice Johnson")
    scim_client.add_group_member(de_id, bob["id"],   "Bob Smith")
    scim_client.add_group_member(ml_id, carol["id"], "Carol White")

    # Snapshot "expected state" before injecting drift
    expected_users  = dict(scim_server.get_users_snapshot())
    expected_groups = dict(scim_server.get_groups_snapshot())

    show_explanation(
        "🌙", "Scenario 5 — Nightly Verification",
        """
  [bold]Business story:[/bold]  Every night at 2 AM, an automated job compares:
    • AD source of truth (what access SHOULD exist)
    • Live Databricks SCIM server (what access ACTUALLY exists)

  Any mismatch = drift. Drift is flagged and auto-corrected.

  [bold yellow]Two drift types injected for this demo:[/bold yellow]
    A) Alice was manually deleted from Databricks by an admin
       → She still exists in AD → should be re-provisioned
    B) An unknown user was manually added to ml-platform in Databricks
       → Not in AD → unauthorized access → should be removed

  [bold yellow]What you'll see:[/bold yellow]
    Step 1 → Inject drift (simulate out-of-band changes)
    Step 2 → Run verification: compare expected vs actual
    Step 3 → Show drift report
    Step 4 → Auto-remediate: SCIM calls to fix each issue
    Step 5 → Re-verify: confirm clean state
        """,
        "magenta",
    )
    pause("Press [Enter] to start verification…")

    # Step 1: Inject drift directly (bypassing SCIM — simulating manual changes)
    show_step(1, "Injecting drift — simulating out-of-band changes")
    console.print("  [yellow]⚠  Injecting drift A: manually deleting Alice from Databricks...[/yellow]")
    with scim_server._lock:
        del scim_server._users[alice["id"]]
        # Also remove from her group (as Databricks would do on manual delete)
        grp = scim_server._groups[de_id]
        grp["members"] = [m for m in grp["members"] if m["value"] != alice["id"]]

    console.print("  [yellow]⚠  Injecting drift B: manually adding rogue user to ml-platform...[/yellow]")
    import uuid as _uuid
    rogue_id = str(_uuid.uuid4())
    with scim_server._lock:
        scim_server._groups[ml_id]["members"].append({
            "value":   rogue_id,
            "display": "rogue.user",
        })
    pause()

    # Step 2: Detect drift
    show_step(2, "Running verification — comparing expected vs actual")
    actual_users  = scim_server.get_users_snapshot()
    actual_groups = scim_server.get_groups_snapshot()

    drift_items = _detect_drift(expected_users, expected_groups, actual_users, actual_groups)
    scim_server.audit(
        scim_server.VERIFICATION_DRIFT_DETECTED, "System", "nightly-job", "Verification",
        detail=f"{len(drift_items)} drift item(s) detected", scenario="verification",
    )

    # Step 3: Show drift report
    show_step(3, "Drift report")
    show_verification_report(drift_items, fixed=False)
    pause()

    # Step 4: Auto-remediate
    show_step(4, "Auto-remediating drift")
    for item in drift_items:
        if item["drift_type"] == "MISSING_USER":
            console.print(f"  [cyan]Re-provisioning {item['resource_name']}…[/cyan]")
            uid_orig = item["resource_id"]
            user_data = expected_users[uid_orig]
            scim_client.create_user(
                user_data["userName"], user_data["displayName"],
                user_data["emails"][0]["value"] if user_data.get("emails") else "",
            )
            # Add back to their expected group
            for gid, g in expected_groups.items():
                if any(m["value"] == uid_orig for m in g.get("members", [])):
                    new_users = scim_server.get_users_snapshot()
                    new_uid = next((k for k, v in new_users.items() if v["userName"] == user_data["userName"]), None)
                    if new_uid:
                        scim_client.add_group_member(gid, new_uid, user_data["displayName"])
            item["action_taken"] = "RE_PROVISIONED"

        elif item["drift_type"] == "UNAUTHORIZED_GROUP_MEMBER":
            console.print(f"  [red]Removing unauthorized member from {item.get('group_name','')}…[/red]")
            scim_client.remove_group_member(item["group_id"], item["resource_id"])
            item["action_taken"] = "MEMBER_REMOVED"

        scim_server.audit(
            scim_server.VERIFICATION_DRIFT_FIXED, item["resource_type"],
            item["resource_id"], item["resource_name"],
            detail=f"Auto-remediated: {item['action_taken']}", scenario="verification",
        )
    pause()

    # Step 5: Clean verification report
    show_step(5, "Re-verification — confirming clean state")
    show_verification_report(drift_items, fixed=True)
    show_access_matrix(scim_server.get_users_snapshot(), scim_server.get_groups_snapshot())

    show_explanation(
        "💡", "Why nightly verification matters",
        """
  [bold]What causes drift?[/bold]
    • A Databricks admin manually creates or removes a user in the UI
    • A failed SCIM call that was never retried
    • A bug in the provisioning pipeline
    • Someone bypassing the IdP to grant emergency access

  [bold]Why idempotent reconciliation works:[/bold]
    The verification job just compares two lists and calls SCIM to
    make them match. It doesn't matter how the drift happened.
    Run it a hundred times — you always get the correct state.

  [bold]At Databricks:[/bold]
    The nightly sync is triggered by the Identity Provider (Okta/Azure AD).
    It re-syncs all group memberships to catch any manual changes.
        """,
        "magenta",
    )

    show_lifecycle_summary("verification", scim_server.get_audit_log_snapshot(),
        "Drift detected → auto-remediated via SCIM. AD is always the source of truth.")
    pause()


# ─────────────────────────────────────────────────────────────────────────────
#  Drift detection helper
# ─────────────────────────────────────────────────────────────────────────────

def _detect_drift(
    expected_users:  dict,
    expected_groups: dict,
    actual_users:    dict,
    actual_groups:   dict,
) -> list[dict]:
    items = []

    # Check for users that should exist but don't
    for uid, u in expected_users.items():
        actual_match = next(
            (v for v in actual_users.values() if v["userName"] == u["userName"]), None
        )
        if not actual_match:
            items.append({
                "drift_type":    "MISSING_USER",
                "resource_type": "User",
                "resource_id":   uid,
                "resource_name": u["userName"],
                "expected":      "active in Databricks",
                "actual":        "not found",
                "action_taken":  "PENDING",
            })

    # Check for unauthorized group members (in actual but not in expected)
    for gid, ag in actual_groups.items():
        eg = expected_groups.get(gid, {})
        expected_ids = {m["value"] for m in eg.get("members", [])}
        for m in ag.get("members", []):
            if m["value"] not in expected_ids and m["value"] not in expected_users:
                items.append({
                    "drift_type":    "UNAUTHORIZED_GROUP_MEMBER",
                    "resource_type": "GroupMembership",
                    "resource_id":   m["value"],
                    "resource_name": m.get("display", m["value"][:12]),
                    "group_id":      gid,
                    "group_name":    ag.get("displayName", ""),
                    "expected":      "not in AD group",
                    "actual":        f"member of {ag.get('displayName','')}",
                    "action_taken":  "PENDING",
                })

    return items
