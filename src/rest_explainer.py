"""
rest_explainer.py
-----------------
Interactive, visual lessons about REST and SCIM concepts.
No code to run here — just learning material shown in a nice terminal UI.
"""

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box
from src.visualizer import (
    console, show_section, show_http_flow_diagram, show_scim_flow_diagram,
    show_http_methods_table, show_status_codes_table, show_explanation, pause
)


def lesson_what_is_rest():
    show_section("Lesson 1 · What is a REST API?")

    show_explanation(
        "📖", "REST API — Plain English",
        """
  REST stands for  [bold]Representational State Transfer[/bold]

  In plain English:

    • A REST API is a way for two computers to talk to each other over the internet.
    • It uses the same protocol (HTTP) that your web browser uses every day.
    • One computer (the [bold cyan]Client[/bold cyan]) makes a [bold]request[/bold].
    • Another computer (the [bold green]Server[/bold green]) sends back a [bold]response[/bold].

  [bold yellow]Real world examples:[/bold yellow]
    • Your phone app asks Twitter's server: "Give me the latest tweets" → REST API
    • Your browser asks Google: "Search for cats" → REST API
    • Okta tells Slack: "Create an account for Alice" → REST API (SCIM specifically)

  The data is almost always returned as [bold]JSON[/bold] — a simple text format
  that both humans and computers can read easily.
        """,
        "cyan",
    )

    show_http_flow_diagram()
    pause()

    show_explanation(
        "🌐", "What is a URL / Endpoint?",
        """
  A URL is just an address — like a house address but for data on the internet.

  [bold]https://api.example.com/scim/v2/Users/abc-123[/bold]

  Breaking it down:
    [cyan]https://api.example.com[/cyan]   → The domain (which server to talk to)
    [cyan]/scim/v2[/cyan]                  → The version of the API
    [cyan]/Users[/cyan]                    → The [bold]resource[/bold] you're working with
    [cyan]/abc-123[/cyan]                  → The specific user's ID

  In REST, URLs represent [bold]resources[/bold] (Users, Groups, Orders, Products, etc.)
  and HTTP methods (GET, POST, etc.) represent [bold]actions[/bold] on those resources.

  [bold yellow]Think of it like:[/bold yellow]
    URL    = the noun  ("the user named Alice")
    Method = the verb  ("GET" / "DELETE" / "CREATE")
        """,
        "blue",
    )
    pause()


def lesson_http_methods():
    show_section("Lesson 2 · HTTP Methods (The 5 Actions)")

    show_explanation(
        "🎯", "The Big Idea",
        """
  Every REST API operation uses one of [bold]5 HTTP methods[/bold].
  Together they cover everything you'd ever want to do with data:

    [bold blue]GET[/bold blue]     →  [bold]Read[/bold]   data     (safe, never changes anything)
    [bold green]POST[/bold green]    →  [bold]Create[/bold] new data (sends data in the request body)
    [bold yellow]PUT[/bold yellow]     →  [bold]Replace[/bold] data   (sends the FULL new version)
    [bold magenta]PATCH[/bold magenta]   →  [bold]Update[/bold] data    (sends only the fields that changed)
    [bold red]DELETE[/bold red]  →  [bold]Remove[/bold] data    (permanently delete)

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
  This confuses everyone at first!  Here's the simplest way to think about it:

  Imagine you have a form with 4 fields:  [Name] [Email] [Phone] [City]

  ─────────────────────────────────────────────────────────────────────

  [bold yellow]PUT (Full Replace)[/bold yellow] — you must send ALL 4 fields.
  If you only send [Name] and forget the others, [Email], [Phone], [City]
  get WIPED OUT.

  PUT /users/123
  Body: { "name": "Alice", "email": "alice@new.com", "phone": "...", "city": "..." }
                                                      ^^^^^^^^^^^^^^^^^^^^^^^^^^
                                                      must include EVERYTHING

  ─────────────────────────────────────────────────────────────────────

  [bold magenta]PATCH (Partial Update)[/bold magenta] — you only send what you want to change.
  Everything else stays exactly as it was.

  PATCH /users/123
  Body: { "email": "alice@new.com" }    ← only the email changes
                                          name, phone, city = untouched ✓

  ─────────────────────────────────────────────────────────────────────

  In SCIM, PATCH is used all the time — e.g. to disable just the 'active' field.
        """,
        "magenta",
    )
    pause()


def lesson_status_codes():
    show_section("Lesson 3 · HTTP Status Codes")

    show_explanation(
        "🚦", "Status Codes — The Server's Reply",
        """
  Every HTTP response starts with a [bold]3-digit status code[/bold].
  It tells you immediately whether your request succeeded or failed.

  They're grouped into ranges:

    [bold bright_green]2xx[/bold bright_green]  →  ✅  [bold]Success![/bold]  The request worked.
    [bold yellow]3xx[/bold yellow]  →  🔄  [bold]Redirect[/bold] — try a different URL.
    [bold orange1]4xx[/bold orange1]  →  ❌  [bold]Client error[/bold] — YOU made a mistake in the request.
    [bold red]5xx[/bold red]  →  💥  [bold]Server error[/bold] — the SERVER has a bug/problem.

  The most important rule:
    If it starts with [bold red]4[/bold red], [bold italic]you[/bold italic] need to fix your request.
    If it starts with [bold red]5[/bold red], [bold italic]they[/bold italic] (the server team) need to fix their code.
        """,
        "cyan",
    )

    show_status_codes_table()
    pause()


def lesson_what_is_scim():
    show_section("Lesson 4 · What is SCIM?")

    show_explanation(
        "🆔", "SCIM — System for Cross-domain Identity Management",
        """
  SCIM is [bold]just a REST API with a specific, agreed-upon format[/bold]
  for managing users and groups across different software systems.

  [bold yellow]The problem it solves:[/bold yellow]

  Imagine you work at a company that uses:
    • Slack  (chat)
    • GitHub (code)
    • Jira   (tickets)
    • Zoom   (calls)
    • AWS    (cloud)
    • Salesforce (CRM)
    • … and 20 more apps

  When a new employee joins, someone has to manually create accounts
  in each of those 25 apps.  When they leave, someone has to manually
  disable all 25 accounts.  This is slow, error-prone, and a security risk!

  [bold green]SCIM solution:[/bold green]
    • Company uses one [bold]Identity Provider[/bold] (e.g. Okta, Azure AD, Google Workspace)
    • All 25 apps support SCIM
    • New employee added to the Identity Provider → all 25 accounts created [bold]automatically[/bold]
    • Employee leaves → all 25 accounts disabled [bold]automatically[/bold]

  [bold cyan]The key point:[/bold cyan]  SCIM defines a [italic]standard format[/italic] everyone agreed on,
  so any IdP can talk to any app without custom code.
        """,
        "green",
    )

    show_scim_flow_diagram()
    pause()

    show_explanation(
        "📋", "SCIM Resources — Users and Groups",
        """
  SCIM works with two main [bold]resource types[/bold]:

  ─────────────────────────────────────────────────────────────────────

  [bold cyan]User[/bold cyan]  →  A person's account
    Endpoint:  /scim/v2/Users
    Fields:    userName, displayName, emails, name, active, …

    Example:
    {
      "userName":    "alice.smith",
      "displayName": "Alice Smith",
      "emails":      [{ "value": "alice@company.com", "primary": true }],
      "active":      true
    }

  ─────────────────────────────────────────────────────────────────────

  [bold yellow]Group[/bold yellow]  →  A team or role (e.g. "Engineering", "Admin")
    Endpoint:  /scim/v2/Groups
    Fields:    displayName, members

    Example:
    {
      "displayName": "Engineering",
      "members": [
        { "value": "user-id-abc", "display": "Alice Smith" }
      ]
    }

  ─────────────────────────────────────────────────────────────────────

  [bold]In this demo[/bold] we focus on Users — the most important SCIM resource.
        """,
        "blue",
    )
    pause()


def lesson_scim_vs_regular_api():
    show_section("Lesson 5 · SCIM vs Regular REST API")

    table = Table(
        title="SCIM vs a Regular Custom REST API",
        box=box.ROUNDED,
        border_style="cyan",
        show_lines=True,
    )
    table.add_column("Aspect",           style="bold",   width=22)
    table.add_column("Regular REST API", style="yellow", width=30)
    table.add_column("SCIM API",         style="green",  width=30)

    rows = [
        ("Purpose",           "Anything you want",                "Only user/group management"),
        ("Format",            "Whatever the developer decides",   "Strictly defined by RFC 7643"),
        ("Field names",       "e.g. user_name or login or uid",   "Always userName (standard)"),
        ("Pagination",        "page=1&limit=10 (varies)",         "startIndex & count (fixed)"),
        ("Errors",            "Custom JSON format",               "Standard SCIM Error schema"),
        ("Discovery",         "Usually docs only",                "/ServiceProviderConfig endpoint"),
        ("Who uses it",       "Any API",                          "Okta, Azure AD, Google, etc."),
        ("Complexity to add", "High (custom code per app)",       "Low (implement the standard)"),
    ]

    for aspect, regular, scim in rows:
        table.add_row(aspect, regular, scim)

    console.print(table)
    console.print()

    show_explanation(
        "💡", "Key Takeaway",
        """
  SCIM is not a different kind of API — it IS a REST API.

  The difference is that SCIM is a [bold]standard[/bold]:
  everyone agreed on the same URL patterns, field names, and response formats.

  So when Okta wants to create a user in Slack, it doesn't need to read
  Slack's custom docs — it just uses the SCIM standard and it works!

  This is the power of standards: [bold]interoperability[/bold].
        """,
        "yellow",
    )
    pause()


def run_all_lessons():
    """Run all 5 lessons in sequence."""
    lesson_what_is_rest()
    lesson_http_methods()
    lesson_status_codes()
    lesson_what_is_scim()
    lesson_scim_vs_regular_api()
    console.print("\n  [bold green]✓  All lessons complete![/bold green] You now know REST + SCIM.\n")
