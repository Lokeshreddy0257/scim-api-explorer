"""
visualizer.py
-------------
All the pretty terminal output lives here.
Rich library is used to draw tables, panels, colors, etc.
"""

import json
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

# ─── Colors for each HTTP method ─────────────────────────────────────────────
METHOD_STYLE = {
    "GET":    ("bold white on blue",   "GET   "),
    "POST":   ("bold white on green",  "POST  "),
    "PUT":    ("bold white on yellow", "PUT   "),
    "PATCH":  ("bold white on magenta","PATCH "),
    "DELETE": ("bold white on red",    "DELETE"),
}

# ─── Colors for HTTP status codes ────────────────────────────────────────────
STATUS_INFO = {
    200: ("green",       "OK"),
    201: ("bright_green","Created"),
    204: ("dim green",   "No Content"),
    400: ("red",         "Bad Request"),
    401: ("yellow",      "Unauthorized"),
    403: ("orange1",     "Forbidden"),
    404: ("orange1",     "Not Found"),
    409: ("magenta",     "Conflict"),
    500: ("bright_red",  "Internal Server Error"),
}


def show_banner():
    """Big welcome banner at startup."""
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
        "[dim]Learn RESTful APIs & SCIM visually — for beginners[/dim]",
        border_style="cyan",
        padding=(0, 2),
    ))
    console.print()


def show_section(title: str):
    """A visual section separator."""
    console.print()
    console.print(Rule(f"[bold cyan]{title}[/bold cyan]", style="cyan"))
    console.print()


def show_http_flow_diagram():
    """
    Draw an ASCII diagram of how HTTP request/response works.
    This is the core concept behind ALL REST APIs.
    """
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
    console.print(Panel(
        diagram,
        title="[bold yellow]📡 How HTTP / REST API Works[/bold yellow]",
        border_style="yellow",
    ))


def show_scim_flow_diagram():
    """
    Visual of how SCIM is used in the real world.
    """
    diagram = """
    IDENTITY PROVIDER                    YOUR APPS (Service Providers)
    (Okta / Azure AD / etc.)             (Slack, GitHub, Salesforce...)

    ┌──────────────────────┐             ┌──────────┐  ┌──────────┐
    │                      │  ─────────► │          │  │          │
    │  HR adds new         │  SCIM POST  │  Slack   │  │  GitHub  │
    │  employee "Alice"    │  /Users     │  creates │  │  creates │
    │                      │             │  account │  │  account │
    └──────────────────────┘             └──────────┘  └──────────┘
             │
             │  Same employee leaves...
             ▼
    ┌──────────────────────┐             ┌──────────┐  ┌──────────┐
    │                      │  ─────────► │          │  │          │
    │  HR deactivates      │  SCIM PATCH │  Slack   │  │  GitHub  │
    │  "Alice"             │  active=false│ disables │  │ disables │
    │                      │             │  account │  │  account │
    └──────────────────────┘             └──────────┘  └──────────┘

    ↑ SCIM automates user provisioning so you don't manually manage accounts!
    """
    console.print(Panel(
        diagram,
        title="[bold green]🔄 How SCIM Works in the Real World[/bold green]",
        border_style="green",
    ))


def show_http_methods_table():
    """Table explaining all 5 HTTP methods with real examples."""
    table = Table(
        title="HTTP Methods — The 5 Actions You Can Take",
        box=box.ROUNDED,
        border_style="blue",
        show_lines=True,
    )
    table.add_column("Method", style="bold", width=8)
    table.add_column("What it does", width=20)
    table.add_column("Real-life analogy", width=28)
    table.add_column("SCIM example", width=30)
    table.add_column("Status", width=10)

    rows = [
        ("GET",    "blue",    "Read / Fetch data",
         "Looking up a name\nin a phone book",
         "GET /scim/v2/Users\n→ List all users",
         "200 OK"),
        ("POST",   "green",   "Create new data",
         "Filling out a form\nto create an account",
         "POST /scim/v2/Users\n→ Add new user",
         "201 Created"),
        ("PUT",    "yellow",  "Replace ALL data",
         "Throwing away an old\nform and writing new one",
         "PUT /scim/v2/Users/123\n→ Overwrite user",
         "200 OK"),
        ("PATCH",  "magenta", "Update PART of data",
         "Crossing out one line\non a form and editing it",
         "PATCH /scim/v2/Users/123\n→ Disable user",
         "200 OK"),
        ("DELETE", "red",     "Remove data",
         "Shredding a file\nfrom the cabinet",
         "DELETE /scim/v2/Users/123\n→ Remove user",
         "204 No Content"),
    ]

    for method, color, what, analogy, example, status in rows:
        table.add_row(
            f"[bold {color}]{method}[/bold {color}]",
            what, analogy, example, f"[dim]{status}[/dim]"
        )

    console.print(table)
    console.print()


def show_status_codes_table():
    """Table of common HTTP status codes."""
    table = Table(
        title="HTTP Status Codes — What the Server is Telling You",
        box=box.ROUNDED,
        border_style="cyan",
        show_lines=True,
    )
    table.add_column("Code", style="bold", width=6)
    table.add_column("Name", width=22)
    table.add_column("Meaning", width=35)
    table.add_column("When you see it", width=30)

    rows = [
        ("200", "green",       "OK",                    "Success — data returned",        "GET request worked fine"),
        ("201", "bright_green","Created",               "New resource was made",           "POST created a new user"),
        ("204", "dim green",   "No Content",            "Success but nothing to return",   "DELETE worked, nothing to show"),
        ("400", "red",         "Bad Request",           "You sent bad/missing data",       "Missing required field"),
        ("401", "yellow",      "Unauthorized",          "You're not logged in / no token", "Missing Bearer token"),
        ("403", "orange1",     "Forbidden",             "Logged in but not allowed",       "No permission for this action"),
        ("404", "orange1",     "Not Found",             "Resource doesn't exist",          "User ID doesn't exist"),
        ("409", "magenta",     "Conflict",              "Duplicate / clash",               "Username already taken"),
        ("500", "bright_red",  "Internal Server Error", "Server-side bug",                 "Bug in server code"),
    ]

    for code, color, name, meaning, when in rows:
        table.add_row(
            f"[bold {color}]{code}[/bold {color}]",
            f"[{color}]{name}[/{color}]",
            meaning, when
        )

    console.print(table)
    console.print()


def show_http_request(method: str, url: str, body=None):
    """Show an HTTP request visually — like what your computer sends."""
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
        body_str = json.dumps(body, indent=4)
        for line in body_str.split("\n"):
            lines.append(f"  [dim white]{line}[/dim white]")

    console.print(Panel(
        "\n".join(lines),
        title="[bold blue]→  Sending HTTP Request[/bold blue]",
        border_style="blue",
        padding=(0, 1),
    ))


def show_http_response(status_code: int, body=None, elapsed_ms: float = 0):
    """Show an HTTP response visually — what the server sends back."""
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
        body_str = json.dumps(body, indent=4)
        for line in body_str.split("\n"):
            lines.append(f"  [dim white]{line}[/dim white]")

    console.print(Panel(
        "\n".join(lines),
        title=f"[bold {border}]←  Server Response[/bold {border}]",
        border_style=border,
        padding=(0, 1),
    ))


def show_user_directory(users: dict):
    """Show the current state of the user store as a pretty table."""
    if not users:
        console.print(Panel(
            "  [dim italic]Directory is empty — no users yet[/dim italic]",
            title="[bold yellow]👥 User Directory (0 users)[/bold yellow]",
            border_style="yellow",
        ))
        return

    table = Table(box=box.SIMPLE_HEAVY, border_style="yellow", show_lines=False)
    table.add_column("Short ID",   style="dim",         width=10)
    table.add_column("Username",   style="bold cyan",   width=18)
    table.add_column("Display Name", style="white",     width=20)
    table.add_column("Email",      style="blue",        width=28)
    table.add_column("Active",     style="green",       width=8)

    for uid, u in users.items():
        email = ""
        if u.get("emails"):
            email = u["emails"][0].get("value", "")
        active = "[green]✓  Yes[/green]" if u.get("active", True) else "[red]✗  No[/red]"
        table.add_row(
            uid[:8] + "…",
            u.get("userName", ""),
            u.get("displayName", ""),
            email,
            active,
        )

    console.print(Panel(
        table,
        title=f"[bold yellow]👥 User Directory ({len(users)} user{'s' if len(users) != 1 else ''})[/bold yellow]",
        border_style="yellow",
    ))


def show_explanation(icon: str, title: str, text: str, style: str = "cyan"):
    """Show a highlighted explanation box."""
    console.print(Panel(
        text,
        title=f"[bold {style}]{icon}  {title}[/bold {style}]",
        border_style=style,
        padding=(0, 2),
    ))


def show_step(n: int, title: str, detail: str = ""):
    """Show a numbered step."""
    console.print(f"\n  [bold yellow][ Step {n} ][/bold yellow]  [bold]{title}[/bold]")
    if detail:
        console.print(f"  [dim]{detail}[/dim]")


def pause(message: str = "Press [Enter] to continue…"):
    console.print(f"\n  [dim]{message}[/dim]")
    input()
