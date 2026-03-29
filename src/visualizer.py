"""
visualizer.py
-------------
All Rich terminal output lives here.
Every panel, table, diagram, and color scheme is defined in this one file
so the rest of the codebase stays clean.
"""

import json
from datetime import datetime
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.rule import Rule
from rich.syntax import Syntax
from rich.columns import Columns
from rich import box
from rich.padding import Padding

console = Console()

# ─── HTTP method colors ───────────────────────────────────────────────────────
METHOD_STYLE = {
    "GET":    ("bold white on blue",    "GET   "),
    "POST":   ("bold white on green",   "POST  "),
    "PUT":    ("bold white on yellow",  "PUT   "),
    "PATCH":  ("bold white on magenta", "PATCH "),
    "DELETE": ("bold white on red",     "DELETE"),
}

# ─── HTTP status code colors ──────────────────────────────────────────────────
STATUS_INFO = {
    200: ("green",        "OK"),
    201: ("bright_green", "Created"),
    204: ("dim green",    "No Content"),
    400: ("red",          "Bad Request"),
    401: ("yellow",       "Unauthorized"),
    403: ("orange1",      "Forbidden"),
    404: ("orange1",      "Not Found"),
    409: ("magenta",      "Conflict"),
    500: ("bright_red",   "Internal Server Error"),
}

# ─── Audit event color mapping ────────────────────────────────────────────────
EVENT_COLORS = {
    "CREATED":       "green",
    "ACTIVATED":     "bright_green",
    "DEACTIVATED":   "yellow",
    "DELETED":       "red",
    "MEMBER_ADDED":  "cyan",
    "MEMBER_REMOVED":"orange1",
    "DRIFT_DETECTED":"red",
    "DRIFT_FIXED":   "bright_green",
    "ACCESS_REVOKED":"red",
    "ACCESS_APPROVED":"green",
    "REVIEW_STARTED":"cyan",
}


def _event_color(event: str) -> str:
    for key, color in EVENT_COLORS.items():
        if key in event:
            return color
    return "white"


# ─────────────────────────────────────────────────────────────────────────────
#  Banner
# ─────────────────────────────────────────────────────────────────────────────
def show_banner():
    console.print()
    banner = """
  ███████╗ ██████╗██╗███╗   ███╗    █████╗ ██████╗ ██╗
  ██╔════╝██╔════╝██║████╗ ████║   ██╔══██╗██╔══██╗██║
  ███████╗██║     ██║██╔████╔██║   ███████║██████╔╝██║
  ╚════██║██║     ██║██║╚██╔╝██║   ██╔══██║██╔═══╝ ██║
  ███████║╚██████╗██║██║ ╚═╝ ██║   ██║  ██║██║     ██║
  ╚══════╝ ╚═════╝╚═╝╚═╝     ╚═╝   ╚═╝  ╚═╝╚═╝     ╚═╝
    """
    console.print(Panel(
        f"[cyan]{banner}[/cyan]\n"
        "[bold white]  SCIM API Explorer[/bold white]  ·  "
        "[dim]Enterprise Identity Lifecycle Simulator[/dim]",
        border_style="cyan",
        padding=(0, 2),
    ))
    console.print()


# ─────────────────────────────────────────────────────────────────────────────
#  Layout helpers
# ─────────────────────────────────────────────────────────────────────────────
def show_section(title: str):
    console.print()
    console.print(Rule(f"[bold cyan]{title}[/bold cyan]", style="cyan"))
    console.print()


def show_step(n: int, title: str, detail: str = ""):
    console.print(f"\n  [bold yellow][ Step {n} ][/bold yellow]  [bold]{title}[/bold]")
    if detail:
        console.print(f"  [dim]{detail}[/dim]")


def show_explanation(icon: str, title: str, text: str, style: str = "cyan"):
    console.print(Panel(
        text,
        title=f"[bold {style}]{icon}  {title}[/bold {style}]",
        border_style=style,
        padding=(0, 2),
    ))


def pause(message: str = "Press [Enter] to continue…"):
    console.print(f"\n  [dim]{message}[/dim]")
    input()


# ─────────────────────────────────────────────────────────────────────────────
#  HTTP request / response panels
# ─────────────────────────────────────────────────────────────────────────────
def show_http_request(method: str, url: str, body=None):
    style, label = METHOD_STYLE.get(method, ("white", method))
    lines = []
    lines.append(f"  [{style}] {label} [/{style}]  [bold white]{url}[/bold white]")
    lines.append("")
    lines.append("  [dim]Headers:[/dim]")
    lines.append("    [cyan]Content-Type[/cyan]: application/scim+json")
    lines.append("    [cyan]Authorization[/cyan]: Bearer demo-token-***")
    if body:
        lines.append("")
        lines.append("  [dim]Request Body (JSON):[/dim]")
        for line in json.dumps(body, indent=4).split("\n"):
            lines.append(f"  [dim white]{line}[/dim white]")
    console.print(Panel(
        "\n".join(lines),
        title="[bold blue]→  Sending HTTP Request[/bold blue]",
        border_style="blue",
        padding=(0, 1),
    ))


def show_http_response(status_code: int, body=None, elapsed_ms: float = 0):
    color, status_text = STATUS_INFO.get(status_code, ("white", "Unknown"))
    border = "green" if status_code < 300 else "red"
    lines = []
    lines.append(
        f"  [bold {color}]{status_code} {status_text}[/bold {color}]"
        f"  [dim]({elapsed_ms:.0f} ms)[/dim]"
    )
    if body and status_code != 204:
        lines.append("")
        lines.append("  [dim]Response Body (JSON):[/dim]")
        for line in json.dumps(body, indent=4).split("\n"):
            lines.append(f"  [dim white]{line}[/dim white]")
    console.print(Panel(
        "\n".join(lines),
        title=f"[bold {border}]←  Server Response[/bold {border}]",
        border_style=border,
        padding=(0, 1),
    ))


# ─────────────────────────────────────────────────────────────────────────────
#  Directory tables
# ─────────────────────────────────────────────────────────────────────────────
def show_user_directory(users: dict):
    if not users:
        console.print(Panel(
            "  [dim italic]Directory is empty — no users yet[/dim italic]",
            title="[bold yellow]👥 User Directory (0 users)[/bold yellow]",
            border_style="yellow",
        ))
        return
    table = Table(box=box.SIMPLE_HEAVY, border_style="yellow", show_lines=False)
    table.add_column("Short ID",     style="dim",       width=10)
    table.add_column("Username",     style="bold cyan", width=18)
    table.add_column("Display Name", style="white",     width=20)
    table.add_column("Email",        style="blue",      width=28)
    table.add_column("Active",       style="green",     width=8)
    for uid, u in users.items():
        email  = u["emails"][0].get("value", "") if u.get("emails") else ""
        active = "[green]✓  Yes[/green]" if u.get("active", True) else "[red]✗  No[/red]"
        table.add_row(uid[:8] + "…", u.get("userName",""), u.get("displayName",""), email, active)
    console.print(Panel(
        table,
        title=f"[bold yellow]👥 User Directory ({len(users)} user{'s' if len(users)!=1 else ''})[/bold yellow]",
        border_style="yellow",
    ))


def show_groups_directory(groups: dict):
    if not groups:
        console.print(Panel(
            "  [dim italic]No groups yet[/dim italic]",
            title="[bold magenta]🏢 Groups Directory (0 groups)[/bold magenta]",
            border_style="magenta",
        ))
        return
    table = Table(box=box.SIMPLE_HEAVY, border_style="magenta", show_lines=False)
    table.add_column("Short ID",     style="dim",          width=10)
    table.add_column("Group Name",   style="bold magenta", width=28)
    table.add_column("Members",      style="white",        width=8)
    table.add_column("Member Names", style="cyan",         width=40)
    for gid, g in groups.items():
        members     = g.get("members", [])
        names       = ", ".join(m.get("display", m.get("value",""))[:12] for m in members)
        table.add_row(gid[:8]+"…", g.get("displayName",""), str(len(members)), names)
    console.print(Panel(
        table,
        title=f"[bold magenta]🏢 Groups Directory ({len(groups)} group{'s' if len(groups)!=1 else ''})[/bold magenta]",
        border_style="magenta",
    ))


# ─────────────────────────────────────────────────────────────────────────────
#  Access matrix
# ─────────────────────────────────────────────────────────────────────────────
def show_access_matrix(users: dict, groups: dict):
    if not users or not groups:
        console.print(Panel(
            "  [dim italic]No users or groups to display[/dim italic]",
            title="[bold green]🔐 Access Matrix[/bold green]",
            border_style="green",
        ))
        return

    # Build set of (user_id, group_id) membership pairs
    memberships: set[tuple[str, str]] = set()
    for gid, g in groups.items():
        for m in g.get("members", []):
            memberships.add((m["value"], gid))

    table = Table(
        title="Access Matrix — Who Has Access to What",
        box=box.ROUNDED,
        border_style="green",
        show_lines=True,
    )
    table.add_column("User", style="bold cyan", width=20)
    table.add_column("Status", width=10)
    group_ids = list(groups.keys())
    for gid in group_ids:
        name = groups[gid].get("displayName", gid[:8])
        table.add_column(name[:20], width=22, justify="center")

    for uid, u in users.items():
        active_badge = "[green]active[/green]" if u.get("active", True) else "[red]inactive[/red]"
        row = [u.get("displayName", u.get("userName","")), active_badge]
        for gid in group_ids:
            if (uid, gid) in memberships:
                row.append("[bold green]  ✓[/bold green]")
            else:
                row.append("[dim]  -[/dim]")
        table.add_row(*row)

    console.print(Panel(table, border_style="green", padding=(0, 1)))


# ─────────────────────────────────────────────────────────────────────────────
#  Audit log table
# ─────────────────────────────────────────────────────────────────────────────
def show_audit_log(entries: list, max_rows: int = 30):
    if not entries:
        console.print(Panel(
            "  [dim italic]Audit log is empty[/dim italic]",
            title="[bold white]📋 Audit Log[/bold white]",
            border_style="dim white",
        ))
        return
    table = Table(box=box.SIMPLE, border_style="dim white", show_lines=False)
    table.add_column("Time",          style="dim",   width=10)
    table.add_column("Event",                        width=28)
    table.add_column("Resource",      style="cyan",  width=22)
    table.add_column("Scenario",      style="dim",   width=16)
    table.add_column("Detail",        style="dim",   width=36)

    for e in entries[-max_rows:]:
        ts      = e.get("timestamp","")[-12:-4] if len(e.get("timestamp","")) >= 12 else ""
        event   = e.get("event","")
        color   = _event_color(event)
        name    = e.get("resource_name", e.get("resource_id",""))[:20]
        scenario= e.get("scenario","")
        detail  = e.get("detail","")[:34]
        table.add_row(
            ts,
            f"[{color}]{event}[/{color}]",
            name,
            scenario,
            detail,
        )

    console.print(Panel(
        table,
        title=f"[bold white]📋 Audit Log ({len(entries)} entries)[/bold white]",
        border_style="dim white",
        padding=(0, 1),
    ))


# ─────────────────────────────────────────────────────────────────────────────
#  Verification report
# ─────────────────────────────────────────────────────────────────────────────
def show_verification_report(drift_items: list, fixed: bool = False):
    today = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    if not drift_items:
        console.print(Panel(
            "\n  [bold green]✓  No drift detected — all systems in sync[/bold green]\n",
            title=f"[bold green]🌙 Nightly Verification Report — {today}[/bold green]",
            border_style="green",
        ))
        return

    table = Table(box=box.DOUBLE_EDGE, border_style="red" if not fixed else "green", show_lines=True)
    table.add_column("Drift Type",    style="bold",  width=26)
    table.add_column("Resource",      style="cyan",  width=20)
    table.add_column("Expected",      style="green", width=22)
    table.add_column("Actual",        style="red",   width=22)
    table.add_column("Action",                       width=20)

    for d in drift_items:
        action_style = "bright_green" if fixed else "yellow"
        action_text  = d.get("action_taken", "PENDING")
        table.add_row(
            d.get("drift_type",""),
            d.get("resource_name",""),
            d.get("expected",""),
            d.get("actual",""),
            f"[{action_style}]{action_text}[/{action_style}]",
        )

    status_line = (
        f"\n  [bold green]✓  {len(drift_items)} issue(s) — all resolved[/bold green]\n"
        if fixed else
        f"\n  [bold red]⚠  {len(drift_items)} drift issue(s) found[/bold red]\n"
    )
    border = "green" if fixed else "red"
    console.print(Panel(
        table,
        title=f"[bold {border}]🌙 Nightly Verification Report — {today}[/bold {border}]",
        border_style=border,
        padding=(0, 1),
    ))
    console.print(status_line)


# ─────────────────────────────────────────────────────────────────────────────
#  Recertification report
# ─────────────────────────────────────────────────────────────────────────────
def show_recert_report(entries: list):
    table = Table(
        title="90-Day Access Recertification Review",
        box=box.HEAVY_HEAD,
        border_style="cyan",
        show_lines=True,
    )
    table.add_column("User",            style="bold cyan", width=20)
    table.add_column("Group / Resource",style="magenta",   width=26)
    table.add_column("Last Certified",                     width=18)
    table.add_column("Manager Decision",                   width=20)

    for e in entries:
        days = e.get("days_since_cert", 0)
        cert_color  = "red" if days > 90 else "yellow" if days > 60 else "green"
        decision    = e.get("decision","pending").upper()
        dec_color   = "green" if decision == "APPROVED" else "red" if decision == "REVOKED" else "yellow"
        table.add_row(
            e.get("display_name", e.get("username","")),
            e.get("group",""),
            f"[{cert_color}]{days} days ago[/{cert_color}]",
            f"[bold {dec_color}]{decision}[/bold {dec_color}]",
        )

    console.print(Panel(table, border_style="cyan", padding=(0, 1)))


# ─────────────────────────────────────────────────────────────────────────────
#  Lifecycle scenario summary
# ─────────────────────────────────────────────────────────────────────────────
def show_lifecycle_summary(scenario_name: str, audit_entries: list, databricks_note: str = ""):
    scenario_entries = [e for e in audit_entries if e.get("scenario") == scenario_name]
    lines = [f"\n  [bold green]✓  Scenario complete:[/bold green]  [bold]{scenario_name.upper()}[/bold]\n"]
    lines.append(f"  [dim]SCIM operations executed:[/dim]  [bold]{len(scenario_entries)}[/bold]")
    if scenario_entries:
        lines.append("\n  [dim]Key events:[/dim]")
        for e in scenario_entries[-5:]:
            color = _event_color(e["event"])
            lines.append(f"    [{color}]•[/{color}]  {e['event']}  [dim]{e.get('resource_name','')}[/dim]")
    if databricks_note:
        lines.append(f"\n  [bold yellow]💡 What Databricks does:[/bold yellow]")
        lines.append(f"  [dim]{databricks_note}[/dim]")
    lines.append("")
    console.print(Panel(
        "\n".join(lines),
        title=f"[bold cyan]📊 Scenario Summary[/bold cyan]",
        border_style="cyan",
        padding=(0, 2),
    ))


# ─────────────────────────────────────────────────────────────────────────────
#  Diagram helpers (used by rest_explainer)
# ─────────────────────────────────────────────────────────────────────────────
def show_http_flow_diagram():
    diagram = """
    YOUR COMPUTER (Client)              SERVER (e.g. Okta, GitHub)
    ─────────────────────               ──────────────────────────

    ┌─────────────────┐                 ┌─────────────────────┐
    │                 │   ─────────►    │                     │
    │  Makes a        │   HTTP Request  │  Receives request   │
    │  REQUEST        │   (GET/POST/..) │  Processes it       │
    │                 │                 │  Looks up database  │
    │                 │   ◄─────────    │                     │
    │  Gets a         │   HTTP Response │  Sends back data    │
    │  RESPONSE       │   (200 OK / ..) │  as JSON            │
    └─────────────────┘                 └─────────────────────┘

    ↑ This is REST API in a nutshell — just asking and receiving data over HTTP
    """
    console.print(Panel(diagram, title="[bold yellow]📡 How HTTP / REST API Works[/bold yellow]", border_style="yellow"))


def show_scim_flow_diagram():
    diagram = """
    IDENTITY PROVIDER                    YOUR APPS (Service Providers)
    (Okta / Azure AD / etc.)             (Slack, GitHub, Databricks...)

    ┌──────────────────────┐             ┌──────────┐  ┌──────────┐
    │                      │  ─────────► │          │  │          │
    │  HR adds new         │  SCIM POST  │  Slack   │  │Databricks│
    │  employee "Alice"    │  /Users     │  creates │  │  creates │
    │                      │             │  account │  │  account │
    └──────────────────────┘             └──────────┘  └──────────┘
             │
             │  Same employee leaves...
             ▼
    ┌──────────────────────┐             ┌──────────┐  ┌──────────┐
    │                      │  ─────────► │          │  │          │
    │  HR deactivates      │  SCIM PATCH │  Slack   │  │Databricks│
    │  "Alice"             │  active=false│ disables │  │ disables │
    │                      │             │  account │  │  account │
    └──────────────────────┘             └──────────┘  └──────────┘

    ↑ SCIM automates user provisioning — no manual account management needed!
    """
    console.print(Panel(diagram, title="[bold green]🔄 How SCIM Works in the Real World[/bold green]", border_style="green"))


def show_enterprise_lifecycle_diagram():
    diagram = """
    HR System ──► Identity Provider (AD/Okta) ──► SCIM ──► Databricks
                                                    │
                         ┌──────────────────────────┼──────────────────────┐
                         │                          │                      │
                    [Onboard]                  [Transfer]            [Terminate]
                         │                          │                      │
                  POST /Users             PATCH /Groups              DELETE /Users
                  POST /Groups            (add + remove)             PATCH active=false
                  (add member)                                        + PATCH /Groups
                         │
            ─────────────────────────────────────────────────────────────
                    [Recertification — Every 90 Days]
                    Manager reviews access list → revoke stale accounts
                    SCIM: PATCH /Users (deactivate) + PATCH /Groups (remove)
                         │
            ─────────────────────────────────────────────────────────────
                    [Nightly Verification — Every Night at 2 AM]
                    Compare AD (expected) vs Databricks (actual)
                    Auto-fix drift via SCIM calls
    """
    console.print(Panel(
        diagram,
        title="[bold cyan]🏢 Enterprise Identity Lifecycle[/bold cyan]",
        border_style="cyan",
    ))


def show_http_methods_table():
    table = Table(
        title="HTTP Methods — The 5 Actions You Can Take",
        box=box.ROUNDED, border_style="blue", show_lines=True,
    )
    table.add_column("Method",            style="bold", width=8)
    table.add_column("What it does",                    width=20)
    table.add_column("Real-life analogy",               width=28)
    table.add_column("SCIM example",                    width=30)
    table.add_column("Status",                          width=10)
    rows = [
        ("GET",    "blue",    "Read / Fetch data",     "Looking up a name\nin a phone book",            "GET /scim/v2/Users\n→ List all users",        "200 OK"),
        ("POST",   "green",   "Create new data",       "Filling out a form\nto create an account",      "POST /scim/v2/Users\n→ Add new user",          "201 Created"),
        ("PUT",    "yellow",  "Replace ALL data",      "Throwing away an old\nform, writing new one",   "PUT /scim/v2/Users/123\n→ Overwrite user",     "200 OK"),
        ("PATCH",  "magenta", "Update PART of data",   "Crossing out one line\non a form and editing",  "PATCH /scim/v2/Users/123\n→ Disable user",     "200 OK"),
        ("DELETE", "red",     "Remove data",           "Shredding a file\nfrom the cabinet",            "DELETE /scim/v2/Users/123\n→ Remove user",     "204 No Content"),
    ]
    for method, color, what, analogy, example, status in rows:
        table.add_row(f"[bold {color}]{method}[/bold {color}]", what, analogy, example, f"[dim]{status}[/dim]")
    console.print(table)
    console.print()


def show_status_codes_table():
    table = Table(
        title="HTTP Status Codes — What the Server is Telling You",
        box=box.ROUNDED, border_style="cyan", show_lines=True,
    )
    table.add_column("Code",  style="bold", width=6)
    table.add_column("Name",               width=22)
    table.add_column("Meaning",            width=35)
    table.add_column("When you see it",    width=30)
    rows = [
        ("200","green",       "OK",                    "Success — data returned",         "GET request worked fine"),
        ("201","bright_green","Created",               "New resource was made",            "POST created a new user"),
        ("204","dim green",   "No Content",            "Success but nothing to return",    "DELETE worked, nothing to show"),
        ("400","red",         "Bad Request",           "You sent bad/missing data",        "Missing required field"),
        ("401","yellow",      "Unauthorized",          "No token / wrong token",           "Missing Bearer token"),
        ("403","orange1",     "Forbidden",             "Logged in but not allowed",        "No permission for this action"),
        ("404","orange1",     "Not Found",             "Resource doesn't exist",           "User ID doesn't exist"),
        ("409","magenta",     "Conflict",              "Duplicate / clash",                "Username already taken"),
        ("500","bright_red",  "Internal Server Error", "Server-side bug",                  "Bug in server code"),
    ]
    for code, color, name, meaning, when in rows:
        table.add_row(
            f"[bold {color}]{code}[/bold {color}]",
            f"[{color}]{name}[/{color}]",
            meaning, when,
        )
    console.print(table)
    console.print()
