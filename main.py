"""
main.py
-------
SCIM API Explorer — interactive CLI entry point.

Usage:
    python main.py

What it does:
  1. Starts a real local SCIM 2.0 server in the background (Flask).
  2. Offers an interactive menu:
       [L] Lessons  — learn REST + SCIM concepts visually
       [D] Demo     — watch a live CRUD walkthrough (create/get/update/delete)
       [I] Interact — run individual SCIM operations yourself
       [Q] Quit
"""

import time
import sys

from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box

from src import scim_server, scim_client, rest_explainer
from src.visualizer import (
    console, show_banner, show_section, show_step,
    show_user_directory, show_explanation, pause,
)

load_dotenv()


# ─────────────────────────────────────────────────────────────────────────────
#  Menu helpers
# ─────────────────────────────────────────────────────────────────────────────

def _menu_choice(prompt: str, valid: set[str]) -> str:
    while True:
        console.print(f"\n  {prompt} ", end="")
        choice = input().strip().lower()
        if choice in valid:
            return choice
        console.print(f"  [red]Invalid choice — enter one of: {', '.join(sorted(valid))}[/red]")


def show_main_menu():
    console.print()
    console.print(Panel(
        "\n"
        "  [bold cyan][L][/bold cyan]  Lessons    — learn REST & SCIM concepts step-by-step\n"
        "  [bold green][D][/bold green]  Demo       — watch a live automated SCIM walkthrough\n"
        "  [bold yellow][I][/bold yellow]  Interact   — run individual SCIM operations yourself\n"
        "  [bold red][Q][/bold red]  Quit\n",
        title="[bold white]Main Menu[/bold white]",
        border_style="white",
        padding=(0, 2),
    ))


def show_interact_menu():
    console.print()
    console.print(Panel(
        "\n"
        "  [bold blue][1][/bold blue]  List all users              (GET  /scim/v2/Users)\n"
        "  [bold green][2][/bold green]  Create a user               (POST /scim/v2/Users)\n"
        "  [bold cyan][3][/bold cyan]  Get one user by ID          (GET  /scim/v2/Users/<id>)\n"
        "  [bold yellow][4][/bold yellow]  Deactivate a user           (PATCH — set active=false)\n"
        "  [bold magenta][5][/bold magenta]  Update display name         (PATCH — change displayName)\n"
        "  [bold red][6][/bold red]  Delete a user               (DELETE /scim/v2/Users/<id>)\n"
        "  [bold white][7][/bold white]  ServiceProviderConfig       (GET  — server capabilities)\n"
        "  [bold white][8][/bold white]  Show user directory         (local snapshot)\n"
        "  [bold white][B][/bold white]  Back to main menu\n",
        title="[bold yellow]Interactive SCIM Operations[/bold yellow]",
        border_style="yellow",
        padding=(0, 2),
    ))


# ─────────────────────────────────────────────────────────────────────────────
#  Live demo — a scripted walkthrough of all CRUD operations
# ─────────────────────────────────────────────────────────────────────────────

def run_demo():
    show_section("Live Demo · Full SCIM CRUD Walkthrough")

    show_explanation(
        "🎬", "What you are about to see",
        """
  This demo performs REAL HTTP requests against the local SCIM server.
  For every call you will see:
    • The exact HTTP request being sent  (method, URL, headers, body)
    • The exact HTTP response received   (status code, body, timing)

  Operations in order:
    1. Create three users  (POST)
    2. List all users      (GET)
    3. Fetch one user      (GET /<id>)
    4. Update display name (PATCH)
    5. Deactivate a user   (PATCH — active=false)
    6. Delete a user       (DELETE)
    7. List users again    (confirm changes)
        """,
        "cyan",
    )
    pause("Press [Enter] to start the demo…")

    # ── Step 1: Create three users ────────────────────────────────────────────
    show_step(1, "Create three users", "POST /scim/v2/Users")

    _, alice   = scim_client.create_user("alice.smith",  "Alice Smith",   "alice@company.com",   "Alice",  "Smith")
    _, bob     = scim_client.create_user("bob.jones",    "Bob Jones",     "bob@company.com",     "Bob",    "Jones")
    _, charlie = scim_client.create_user("charlie.chen", "Charlie Chen",  "charlie@company.com", "Charlie","Chen")

    pause()

    # ── Step 2: List all users ────────────────────────────────────────────────
    show_step(2, "List all users", "GET /scim/v2/Users")
    scim_client.list_users()
    show_user_directory(scim_server.get_users_snapshot())
    pause()

    # ── Step 3: Fetch one user ────────────────────────────────────────────────
    show_step(3, "Fetch Alice by her ID", "GET /scim/v2/Users/<id>")
    alice_id = alice["id"]
    scim_client.get_user(alice_id)
    pause()

    # ── Step 4: Update display name ───────────────────────────────────────────
    show_step(4, "Update Alice's display name", "PATCH — change displayName only")
    scim_client.update_display_name(alice_id, "Alice Smith-Williams")
    pause()

    # ── Step 5: Deactivate Bob ────────────────────────────────────────────────
    show_step(5, "Deactivate Bob (he left the company)", "PATCH — set active=false")
    bob_id = bob["id"]
    scim_client.deactivate_user(bob_id)
    show_user_directory(scim_server.get_users_snapshot())
    pause()

    # ── Step 6: Delete Charlie ────────────────────────────────────────────────
    show_step(6, "Delete Charlie permanently", "DELETE /scim/v2/Users/<id>")
    charlie_id = charlie["id"]
    scim_client.delete_user(charlie_id)
    pause()

    # ── Step 7: Final state ───────────────────────────────────────────────────
    show_step(7, "Final state — list remaining users", "GET /scim/v2/Users")
    scim_client.list_users()
    show_user_directory(scim_server.get_users_snapshot())

    console.print()
    console.print(Panel(
        "\n  [bold green]✓  Demo complete![/bold green]\n\n"
        "  You just performed real HTTP calls against a live SCIM 2.0 server.\n"
        "  Every request/response pair above is exactly what Okta / Azure AD\n"
        "  would send to provision and deprovision users in real life.\n",
        border_style="green",
        padding=(0, 2),
    ))
    pause()


# ─────────────────────────────────────────────────────────────────────────────
#  Interactive mode — user picks operations one at a time
# ─────────────────────────────────────────────────────────────────────────────

def _prompt(label: str) -> str:
    console.print(f"  [cyan]{label}:[/cyan] ", end="")
    return input().strip()


def run_interactive():
    while True:
        show_interact_menu()
        choice = _menu_choice("[bold yellow]Choose an operation [1-8/B]:[/bold yellow]",
                              {"1","2","3","4","5","6","7","8","b"})
        if choice == "b":
            return

        users = scim_server.get_users_snapshot()

        if choice == "1":
            scim_client.list_users()
            show_user_directory(users)

        elif choice == "2":
            console.print("\n  [dim]Fill in the new user details:[/dim]")
            username     = _prompt("userName (e.g. jane.doe)")
            display_name = _prompt("displayName (e.g. Jane Doe)")
            email        = _prompt("email")
            first        = _prompt("firstName (optional)")
            last         = _prompt("lastName  (optional)")
            if not username:
                console.print("  [red]userName is required[/red]")
                continue
            scim_client.create_user(username, display_name, email, first, last)
            show_user_directory(scim_server.get_users_snapshot())

        elif choice in ("3","4","5","6"):
            if not users:
                console.print("\n  [yellow]No users yet — create one first (option 2)[/yellow]")
                continue
            # Show a quick list so the user can pick an ID
            show_user_directory(users)
            uid = _prompt("Paste user ID (full UUID or the first 8 chars)")
            # Support short IDs
            if len(uid) < 36:
                matches = [k for k in users if k.startswith(uid)]
                if len(matches) == 1:
                    uid = matches[0]
                elif len(matches) == 0:
                    console.print("  [red]No user found with that ID prefix[/red]")
                    continue
                else:
                    console.print("  [red]Ambiguous prefix — matches multiple users[/red]")
                    continue

            if choice == "3":
                scim_client.get_user(uid)
            elif choice == "4":
                scim_client.deactivate_user(uid)
                show_user_directory(scim_server.get_users_snapshot())
            elif choice == "5":
                new_name = _prompt("New displayName")
                scim_client.update_display_name(uid, new_name)
                show_user_directory(scim_server.get_users_snapshot())
            elif choice == "6":
                confirm = _prompt("Type 'yes' to confirm permanent deletion")
                if confirm.lower() == "yes":
                    scim_client.delete_user(uid)
                    show_user_directory(scim_server.get_users_snapshot())
                else:
                    console.print("  [dim]Deletion cancelled.[/dim]")

        elif choice == "7":
            scim_client.get_service_provider_config()

        elif choice == "8":
            show_user_directory(scim_server.get_users_snapshot())

        pause("Press [Enter] to continue…")


# ─────────────────────────────────────────────────────────────────────────────
#  main
# ─────────────────────────────────────────────────────────────────────────────

def main():
    show_banner()

    # Start the SCIM server in the background
    console.print("  [dim]Starting local SCIM 2.0 server on port 5000…[/dim]")
    scim_server.start(port=5000)
    time.sleep(0.5)   # give Flask a moment to bind the port
    console.print("  [bold green]✓  Server running at http://localhost:5000/scim/v2[/bold green]\n")

    while True:
        show_main_menu()
        choice = _menu_choice("[bold white]Choose [L/D/I/Q]:[/bold white]", {"l","d","i","q"})

        if choice == "l":
            rest_explainer.run_all_lessons()
        elif choice == "d":
            run_demo()
        elif choice == "i":
            run_interactive()
        elif choice == "q":
            console.print("\n  [dim]Goodbye! The server will stop when this window closes.[/dim]\n")
            sys.exit(0)


if __name__ == "__main__":
    main()
