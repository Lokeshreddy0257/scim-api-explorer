"""
rest_explainer.py
-----------------
7 interactive lessons on REST, SCIM, and enterprise identity management.
All lessons use Rich panels so the terminal output is easy to read.
"""

from rich.table import Table
from rich import box
from src.visualizer import (
    console, show_section, show_http_flow_diagram, show_scim_flow_diagram,
    show_enterprise_lifecycle_diagram, show_http_methods_table,
    show_status_codes_table, show_explanation, pause,
)


# ─────────────────────────────────────────────────────────────────────────────
#  Lesson 1 — What is a REST API?
# ─────────────────────────────────────────────────────────────────────────────

def lesson_what_is_rest():
    show_section("Lesson 1 · What is a REST API?")

    show_explanation(
        "📖", "REST API — Plain English",
        """
  REST stands for  [bold]Representational State Transfer[/bold]

  In plain English:
    • A REST API is a way for two computers to talk over the internet.
    • It uses HTTP — the same protocol your browser uses every day.
    • One computer (the [bold cyan]Client[/bold cyan]) makes a [bold]request[/bold].
    • Another computer (the [bold green]Server[/bold green]) sends back a [bold]response[/bold].

  [bold yellow]Real world examples:[/bold yellow]
    • Your phone asks Twitter: "Give me the latest tweets"       → REST API
    • Your browser asks Google: "Search for cats"               → REST API
    • Okta tells Databricks: "Create an account for Alice"      → REST API (SCIM)
    • Okta tells Slack: "Disable Bob's account — he left"       → REST API (SCIM)

  Data is returned as [bold]JSON[/bold] — a simple text format
  both humans and machines can read easily.
        """,
        "cyan",
    )

    show_http_flow_diagram()
    pause()

    show_explanation(
        "🌐", "What is a URL / Endpoint?",
        """
  A URL is just an address — like a street address but for data.

  [bold]https://api.example.com/scim/v2/Users/abc-123[/bold]

  Breaking it down:
    [cyan]https://api.example.com[/cyan]   → Which server to talk to
    [cyan]/scim/v2[/cyan]                  → API version
    [cyan]/Users[/cyan]                    → The [bold]resource[/bold] (Users, Groups, Orders…)
    [cyan]/abc-123[/cyan]                  → A specific user's ID

  In REST, the URL is the [bold]noun[/bold]  ("the user Alice")
  and the HTTP method is the [bold]verb[/bold] ("GET" / "DELETE" / "CREATE")
        """,
        "blue",
    )
    pause()


# ─────────────────────────────────────────────────────────────────────────────
#  Lesson 2 — HTTP Methods
# ─────────────────────────────────────────────────────────────────────────────

def lesson_http_methods():
    show_section("Lesson 2 · HTTP Methods (The 5 Actions)")

    show_explanation(
        "🎯", "The Big Idea",
        """
  Every REST API operation uses one of [bold]5 HTTP methods[/bold]:

    [bold blue]GET[/bold blue]     →  [bold]Read[/bold]    data   (safe, never changes anything)
    [bold green]POST[/bold green]    →  [bold]Create[/bold]  data   (sends data in the request body)
    [bold yellow]PUT[/bold yellow]     →  [bold]Replace[/bold] data   (sends the FULL new version)
    [bold magenta]PATCH[/bold magenta]   →  [bold]Update[/bold]  data   (sends only the changed fields)
    [bold red]DELETE[/bold red]  →  [bold]Remove[/bold]  data   (permanently delete)

  These are often called [bold]CRUD[/bold] operations:
    C = Create  (POST)
    R = Read    (GET)
    U = Update  (PUT / PATCH)
    D = Delete  (DELETE)
        """,
        "yellow",
    )

    show_http_methods_table()
    pause()

    show_explanation(
        "🤔", "PUT vs PATCH — What's the difference?",
        """
  This confuses everyone at first. Here's the simplest way:

  Imagine a user form with 4 fields:  [Name] [Email] [Phone] [Active]

  ──────────────────────────────────────────────────────────────────

  [bold yellow]PUT (Full Replace)[/bold yellow] — you MUST send ALL 4 fields.
  If you only send [Name], the other 3 fields get wiped out.

  PUT /Users/123
  Body: { "name": "Alice", "email": "...", "phone": "...", "active": true }

  ──────────────────────────────────────────────────────────────────

  [bold magenta]PATCH (Partial Update)[/bold magenta] — send ONLY what changes.
  Everything else stays exactly as it was.

  PATCH /Users/123
  Body: { "active": false }    ← only active changes; name/email/phone untouched

  ──────────────────────────────────────────────────────────────────

  [bold]In SCIM, PATCH is used constantly:[/bold]
    • Deactivating a user when they leave   → PATCH active=false
    • Moving someone to a new team          → PATCH department
    • Adding/removing group members         → PATCH /Groups/<id>
        """,
        "magenta",
    )
    pause()


# ─────────────────────────────────────────────────────────────────────────────
#  Lesson 3 — HTTP Status Codes
# ─────────────────────────────────────────────────────────────────────────────

def lesson_status_codes():
    show_section("Lesson 3 · HTTP Status Codes")

    show_explanation(
        "🚦", "Status Codes — The Server's Reply",
        """
  Every HTTP response starts with a [bold]3-digit status code[/bold].
  It tells you immediately whether the request succeeded or failed.

  Groups:
    [bold bright_green]2xx[/bold bright_green]  →  ✅  [bold]Success![/bold]  The request worked.
    [bold yellow]3xx[/bold yellow]  →  🔄  [bold]Redirect[/bold] — try a different URL.
    [bold orange1]4xx[/bold orange1]  →  ❌  [bold]Client error[/bold] — YOU made a mistake.
    [bold red]5xx[/bold red]  →  💥  [bold]Server error[/bold] — the SERVER has a bug.

  Simple rule:
    4xx → you need to fix your request.
    5xx → they need to fix their server.
        """,
        "cyan",
    )

    show_status_codes_table()
    pause()


# ─────────────────────────────────────────────────────────────────────────────
#  Lesson 4 — What is SCIM?
# ─────────────────────────────────────────────────────────────────────────────

def lesson_what_is_scim():
    show_section("Lesson 4 · What is SCIM?")

    show_explanation(
        "🆔", "SCIM — System for Cross-domain Identity Management",
        """
  SCIM is [bold]just a REST API with a specific, agreed-upon format[/bold]
  for managing users and groups across different software systems.

  [bold yellow]The problem it solves:[/bold yellow]

  A company that uses Slack, GitHub, Jira, Zoom, AWS, Salesforce,
  Databricks, and 20 more apps has to manually:
    • Create accounts in all 25 apps when a new person joins
    • Disable accounts in all 25 apps when someone leaves

  That's slow, error-prone, and a security risk.

  [bold green]SCIM solution:[/bold green]
    • Company uses one [bold]Identity Provider[/bold] (Okta, Azure AD, Google Workspace)
    • All apps support SCIM
    • New hire added to IdP → all accounts created [bold]automatically[/bold]
    • Someone leaves → all accounts disabled [bold]automatically[/bold]

  [bold cyan]The key point:[/bold cyan]
  SCIM defines a [italic]standard format[/italic] everyone agreed on,
  so any IdP can talk to any app without writing custom code.
        """,
        "green",
    )

    show_scim_flow_diagram()
    pause()

    show_explanation(
        "📋", "SCIM Resources — Users and Groups",
        """
  SCIM works with two main [bold]resource types[/bold]:

  ────────────────────────────────────────────────────────────────

  [bold cyan]User[/bold cyan]  →  A person's account
    Endpoint:  /scim/v2/Users
    Key fields: userName, displayName, emails, name, active

  Example:
  {
    "userName":    "alice.smith",
    "displayName": "Alice Smith",
    "emails":      [{ "value": "alice@company.com", "primary": true }],
    "active":      true
  }

  ────────────────────────────────────────────────────────────────

  [bold yellow]Group[/bold yellow]  →  A team or role  (e.g. "data-engineering", "admin")
    Endpoint:  /scim/v2/Groups
    Key fields: displayName, members

  Example:
  {
    "displayName": "data-engineering",
    "members": [
      { "value": "user-id-abc", "display": "Alice Smith" }
    ]
  }

  ────────────────────────────────────────────────────────────────

  In this simulator we use [bold]both Users and Groups[/bold].
  Group membership is how Databricks workspace access is granted.
        """,
        "blue",
    )
    pause()


# ─────────────────────────────────────────────────────────────────────────────
#  Lesson 5 — SCIM vs Regular REST API
# ─────────────────────────────────────────────────────────────────────────────

def lesson_scim_vs_regular_api():
    show_section("Lesson 5 · SCIM vs Regular REST API")

    table = Table(
        title="SCIM vs a Regular Custom REST API",
        box=box.ROUNDED, border_style="cyan", show_lines=True,
    )
    table.add_column("Aspect",            style="bold",   width=22)
    table.add_column("Regular REST API",  style="yellow", width=30)
    table.add_column("SCIM API",          style="green",  width=30)

    rows = [
        ("Purpose",          "Anything you want",               "User/group management only"),
        ("Format",           "Whatever the developer decides",  "Strictly defined by RFC 7643"),
        ("Field names",      "user_name / login / uid",         "Always: userName (standard)"),
        ("Pagination",       "page=1&limit=10 (varies)",        "startIndex & count (fixed)"),
        ("Errors",           "Custom JSON format",              "Standard SCIM Error schema"),
        ("Discovery",        "Usually just docs",               "/ServiceProviderConfig"),
        ("Lifecycle ops",    "Custom webhooks / jobs",          "PATCH + group membership"),
        ("Who uses it",      "Any API",                         "Okta, Azure AD, Google, etc."),
    ]
    for row in rows:
        table.add_row(*row)

    console.print(table)
    console.print()

    show_explanation(
        "💡", "Key Takeaway",
        """
  SCIM is not a different kind of API — it IS a REST API.

  The difference is that SCIM is a [bold]standard[/bold]:
  everyone agreed on the same URL patterns, field names, and formats.

  So when Okta wants to create a user in Databricks, it doesn't
  need to read Databricks' custom docs — it just uses SCIM and it works.

  This is the power of standards: [bold]interoperability[/bold].
        """,
        "yellow",
    )
    pause()


# ─────────────────────────────────────────────────────────────────────────────
#  Lesson 6 — Enterprise Identity Lifecycle
# ─────────────────────────────────────────────────────────────────────────────

def lesson_enterprise_lifecycle():
    show_section("Lesson 6 · Enterprise Identity Lifecycle")

    show_explanation(
        "🏢", "The Full Lifecycle — Cradle to Grave",
        """
  In an enterprise, user access has a full lifecycle:

  ┌─────────────┐   ┌─────────────┐   ┌─────────────┐   ┌─────────────┐
  │  ONBOARDING │   │ OFFBOARDING │   │ TERMINATION │   │   ONGOING   │
  │             │   │  (transfer) │   │             │   │ MAINTENANCE │
  │ New hire    │   │ Team change │   │ Employee    │   │ Recert +    │
  │ → access    │   │ → swap      │   │ leaves →    │   │ Nightly     │
  │ granted     │   │   access    │   │ all access  │   │ Verify      │
  └─────────────┘   └─────────────┘   └─────────────┘   └─────────────┘
       │                  │                  │                  │
  POST /Users         PATCH /Groups      DELETE /Users    PATCH (fix drift)
  POST /Groups        (add + remove)     PATCH active=f   + remove stale
        """,
        "cyan",
    )

    show_enterprise_lifecycle_diagram()
    pause()

    table = Table(
        title="Lifecycle Event → SCIM Operation Mapping",
        box=box.ROUNDED, border_style="cyan", show_lines=True,
    )
    table.add_column("Event",          style="bold",    width=22)
    table.add_column("SCIM Operation",                  width=30)
    table.add_column("HTTP Method",    style="magenta", width=14)
    table.add_column("What changes",   style="dim",     width=28)

    rows = [
        ("New hire joins",          "POST /Users + POST /Groups",          "POST",         "User created, group registered"),
        ("Granted workspace access","PATCH /Groups — add member",          "PATCH",        "members[] grows by 1"),
        ("Team transfer",           "PATCH /Groups — remove + add",        "PATCH x2",     "Old group −1, new group +1"),
        ("Department change",       "PATCH /Users — department field",     "PATCH",        "user.department updated"),
        ("Employee exits",          "PATCH active=false + DELETE",         "PATCH+DELETE", "Immediate lockout then removal"),
        ("Access revoked (recert)", "PATCH active=false + remove member",  "PATCH x2",     "Deactivated + group cleanup"),
        ("Drift auto-corrected",    "Re-run create or remove member",      "POST/PATCH",   "State matches AD source of truth"),
    ]
    for row in rows:
        table.add_row(*row)

    console.print(table)
    pause()


# ─────────────────────────────────────────────────────────────────────────────
#  Lesson 7 — Groups, RBAC, and Access Control
# ─────────────────────────────────────────────────────────────────────────────

def lesson_groups_and_rbac():
    show_section("Lesson 7 · Groups, RBAC & Access Control")

    show_explanation(
        "🔐", "Why Groups (not individual grants) are the Right Pattern",
        """
  [bold]Imagine granting access one user at a time:[/bold]

    Alice  → Databricks workspace A  (admin action)
    Bob    → Databricks workspace A  (admin action)
    Carol  → Databricks workspace A  (admin action)
    ... 500 more engineers ...

  Problems:
    • When 'workspace A' is decommissioned, you have to find all 503 users
    • When Alice moves teams, you have to remember to revoke workspace A
    • No single place to see "who has access to workspace A"

  ──────────────────────────────────────────────────────────────────

  [bold green]The group-based pattern:[/bold green]

    AD Group: data-engineering
      → maps to Databricks workspace A (configured once)
      → all members get access automatically

    Now adding a new engineer = just add them to the AD group.
    Revoking all data-engineering access = delete the group mapping.
    Seeing who has access = look at group members.

  One SCIM PATCH call handles what used to take 500 admin actions.
        """,
        "green",
    )
    pause()

    show_explanation(
        "🏗️", "RBAC — Role-Based Access Control",
        """
  [bold]RBAC in plain English:[/bold]

  Instead of giving permissions directly to people, you:
    1. Define [bold]roles[/bold]    (e.g. "data-reader", "spark-admin")
    2. Assign [bold]groups[/bold]   to roles   (data-engineering → spark-admin)
    3. Add [bold]users[/bold]       to groups  (Alice → data-engineering)

  The chain:  User → Group → Role → Permissions

  [bold yellow]Why this matters for SCIM:[/bold yellow]

  When Okta sends:
    PATCH /Groups/data-engineering  →  add member: alice.smith

  Databricks interprets this as:
    Alice gets all permissions associated with the 'data-engineering' group
    (e.g. spark-admin role on workspace A, read access to catalog B, etc.)

  You configure the group → permission mapping ONCE in Databricks.
  After that, every SCIM group membership change automatically
  propagates the right permissions. No manual permission granting needed.
        """,
        "blue",
    )
    pause()

    show_explanation(
        "⚙️", "SCIM PATCH on Groups — The Technical Details",
        """
  [bold]Adding a member (what Okta sends):[/bold]

  PATCH /scim/v2/Groups/group-id-123
  {
    "schemas":    ["urn:ietf:params:scim:api:messages:2.0:PatchOp"],
    "Operations": [{
      "op":    "add",
      "path":  "members",
      "value": [{"value": "user-id-abc", "display": "Alice Smith"}]
    }]
  }

  ──────────────────────────────────────────────────────────────────

  [bold]Removing a member — filter-path syntax (what Azure AD sends):[/bold]

  PATCH /scim/v2/Groups/group-id-123
  {
    "Operations": [{
      "op":   "remove",
      "path": "members[value eq \\"user-id-abc\\"]"
    }]
  }

  The filter-path syntax [dim]members[value eq "..."][/dim] is part of
  RFC 7644 §3.5.2. Real IdPs send this exact syntax — our server
  handles it correctly using regex parsing.

  ──────────────────────────────────────────────────────────────────

  [bold]Why idempotency matters:[/bold]
    Sending the same PATCH twice must not cause an error.
    If Alice is already in the group, a second "add member: alice"
    must be ignored gracefully (not return 409 Conflict).
    Our server handles this correctly.
        """,
        "magenta",
    )
    pause()


# ─────────────────────────────────────────────────────────────────────────────
#  Run all lessons
# ─────────────────────────────────────────────────────────────────────────────

def run_all_lessons():
    """Run all 7 lessons in sequence."""
    lesson_what_is_rest()
    lesson_http_methods()
    lesson_status_codes()
    lesson_what_is_scim()
    lesson_scim_vs_regular_api()
    lesson_enterprise_lifecycle()
    lesson_groups_and_rbac()
    console.print("\n  [bold green]✓  All 7 lessons complete![/bold green]  "
                  "You now understand REST, SCIM, and enterprise identity management.\n")


def run_lesson_menu():
    """Let the user pick a single lesson by number."""
    lessons = [
        ("1", "What is a REST API?",          lesson_what_is_rest),
        ("2", "HTTP Methods",                 lesson_http_methods),
        ("3", "HTTP Status Codes",            lesson_status_codes),
        ("4", "What is SCIM?",                lesson_what_is_scim),
        ("5", "SCIM vs Regular REST API",     lesson_scim_vs_regular_api),
        ("6", "Enterprise Identity Lifecycle",lesson_enterprise_lifecycle),
        ("7", "Groups, RBAC & Access Control",lesson_groups_and_rbac),
        ("A", "All lessons in sequence",      run_all_lessons),
        ("B", "Back to main menu",            None),
    ]

    from rich.panel import Panel
    while True:
        lines = ["\n"]
        for key, title, _ in lessons:
            lines.append(f"  [bold cyan][{key}][/bold cyan]  {title}")
        lines.append("")
        console.print(Panel("\n".join(lines), title="[bold white]Lessons[/bold white]", border_style="white"))
        console.print("  Choose a lesson: ", end="")
        choice = input().strip().lower()
        match = next((fn for k, _, fn in lessons if k.lower() == choice), None)
        if choice == "b":
            return
        if match:
            match()
        else:
            console.print("  [red]Invalid choice[/red]")
