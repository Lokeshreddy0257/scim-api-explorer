"""
main.py
-------
SCIM API Explorer — Enterprise Identity Lifecycle Simulator

Usage:
    python main.py

Menu:
  [L]  Lessons        — 7 guided lessons on REST, SCIM & enterprise lifecycle
  [1]  Onboarding     — new hire → AD group → SCIM → Databricks access
  [2]  Offboarding    — team transfer → group swap → access updated
  [3]  Termination    — employee exits → full access revocation
  [4]  Recertification— 90-day review: approve or revoke stale access
  [5]  Verification   — nightly drift detection & auto-remediation
  [I]  Interactive    — run individual SCIM operations (Users + Groups)
  [Q]  Quit
"""

import sys
import time

from dotenv import load_dotenv
from rich.panel import Panel

from src import scim_server, scim_client, lifecycle
from src import rest_explainer
from src.visualizer import (
    console, show_banner, show_section,
    show_user_directory, show_groups_directory, show_access_matrix,
    show_audit_log, pause,
)

load_dotenv()


# ─────────────────────────────────────────────────────────────────────────────
#  Menu helpers
# ─────────────────────────────────────────────────────────────────────────────

def _prompt_choice(prompt: str, valid: set[str]) -> str:
    while True:
        console.print(f"\n  {prompt} ", end="")
        ch = input().strip().lower()
        if ch in valid:
            return ch
        console.print(f"  [red]Invalid — enter one of: {', '.join(sorted(valid))}[/red]")


def _input(label: str) -> str:
    console.print(f"  [cyan]{label}:[/cyan] ", end="")
    return input().strip()


def show_main_menu():
    console.print()
    console.print(Panel(
        "\n"
        "  [bold cyan][L][/bold cyan]  Lessons         — 7 lessons: REST, SCIM & enterprise lifecycle\n\n"
        "  [bold green][1][/bold green]  Onboarding      — new hire → AD group → SCIM → Databricks access\n"
        "  [bold yellow][2][/bold yellow]  Offboarding     — team transfer → group swap → access updated\n"
        "  [bold red][3][/bold red]  Termination     — employee exits → all access permanently revoked\n"
        "  [bold magenta][4][/bold magenta]  Recertification — 90-day review: approve or revoke stale access\n"
        "  [bold blue][5][/bold blue]  Verification    — nightly drift detection & auto-remediation\n\n"
        "  [bold white][I][/bold white]  Interactive     — run individual SCIM operations yourself\n"
        "  [bold white][Q][/bold white]  Quit\n",
        title="[bold white]⚡ Main Menu[/bold white]",
        border_style="white",
        padding=(0, 2),
    ))


# ─────────────────────────────────────────────────────────────────────────────
#  Interactive mode — run individual SCIM operations
# ─────────────────────────────────────────────────────────────────────────────

def show_interact_menu():
    console.print()
    console.print(Panel(
        "\n"
        "  [bold]── Users ──────────────────────────────────────────────[/bold]\n"
        "  [bold blue][1][/bold blue]  List all users              GET  /scim/v2/Users\n"
        "  [bold green][2][/bold green]  Create a user               POST /scim/v2/Users\n"
        "  [bold cyan][3][/bold cyan]  Get one user by ID          GET  /scim/v2/Users/<id>\n"
        "  [bold yellow][4][/bold yellow]  Deactivate a user           PATCH active=false\n"
        "  [bold magenta][5][/bold magenta]  Update display name         PATCH displayName\n"
        "  [bold red][6][/bold red]  Delete a user               DELETE /scim/v2/Users/<id>\n\n"
        "  [bold]── Groups ─────────────────────────────────────────────[/bold]\n"
        "  [bold blue][7][/bold blue]  List all groups             GET  /scim/v2/Groups\n"
        "  [bold green][8][/bold green]  Create a group              POST /scim/v2/Groups\n"
        "  [bold cyan][9][/bold cyan]  Add user to group           PATCH — add member\n"
        "  [bold red][0][/bold red]  Remove user from group      PATCH — remove member\n\n"
        "  [bold]── Views ──────────────────────────────────────────────[/bold]\n"
        "  [bold white][A][/bold white]  Access matrix               Users × Groups snapshot\n"
        "  [bold white][U][/bold white]  Audit log                   All SCIM events so far\n"
        "  [bold white][S][/bold white]  ServiceProviderConfig       Server capabilities\n"
        "  [bold white][B][/bold white]  Back to main menu\n",
        title="[bold yellow]Interactive SCIM Operations[/bold yellow]",
        border_style="yellow",
        padding=(0, 2),
    ))


def _pick_user(prompt: str = "Paste user ID (or first 8 chars)") -> str | None:
    users = scim_server.get_users_snapshot()
    if not users:
        console.print("\n  [yellow]No users yet — create one first (option 2)[/yellow]")
        return None
    show_user_directory(users)
    uid = _input(prompt)
    if len(uid) < 36:
        matches = [k for k in users if k.startswith(uid)]
        if len(matches) == 1:
            return matches[0]
        if len(matches) == 0:
            console.print("  [red]No user found with that ID prefix[/red]")
            return None
        console.print("  [red]Ambiguous prefix — matches multiple users[/red]")
        return None
    return uid if uid in users else None


def _pick_group(prompt: str = "Paste group ID (or first 8 chars)") -> str | None:
    groups = scim_server.get_groups_snapshot()
    if not groups:
        console.print("\n  [yellow]No groups yet — create one first (option 8)[/yellow]")
        return None
    show_groups_directory(groups)
    gid = _input(prompt)
    if len(gid) < 36:
        matches = [k for k in groups if k.startswith(gid)]
        if len(matches) == 1:
            return matches[0]
        console.print("  [red]Group not found[/red]")
        return None
    return gid if gid in groups else None


def run_interactive():
    valid = {"1","2","3","4","5","6","7","8","9","0","a","u","s","b"}
    while True:
        show_interact_menu()
        ch = _prompt_choice("[bold yellow]Choose [1-9/0/A/U/S/B]:[/bold yellow]", valid)

        if ch == "b":
            return

        # ── Users ──────────────────────────────────────────────────────────
        if ch == "1":
            scim_client.list_users()
            show_user_directory(scim_server.get_users_snapshot())

        elif ch == "2":
            console.print("\n  [dim]Fill in new user details:[/dim]")
            username = _input("userName  (e.g. jane.doe)")
            if not username:
                console.print("  [red]userName is required[/red]")
            else:
                dname = _input("displayName (e.g. Jane Doe)")
                email = _input("email")
                first = _input("firstName (optional)")
                last  = _input("lastName  (optional)")
                dept  = _input("department (optional)")
                scim_client.create_user(username, dname, email, first, last, dept)
                show_user_directory(scim_server.get_users_snapshot())

        elif ch == "3":
            uid = _pick_user()
            if uid:
                scim_client.get_user(uid)

        elif ch == "4":
            uid = _pick_user()
            if uid:
                scim_client.deactivate_user(uid)
                show_user_directory(scim_server.get_users_snapshot())

        elif ch == "5":
            uid = _pick_user()
            if uid:
                new_name = _input("New displayName")
                scim_client.update_display_name(uid, new_name)
                show_user_directory(scim_server.get_users_snapshot())

        elif ch == "6":
            uid = _pick_user()
            if uid:
                confirm = _input("Type 'yes' to confirm permanent deletion")
                if confirm.lower() == "yes":
                    scim_client.delete_user(uid)
                    show_user_directory(scim_server.get_users_snapshot())
                else:
                    console.print("  [dim]Deletion cancelled.[/dim]")

        # ── Groups ─────────────────────────────────────────────────────────
        elif ch == "7":
            scim_client.list_groups()
            show_groups_directory(scim_server.get_groups_snapshot())

        elif ch == "8":
            name = _input("Group displayName (e.g. data-engineering)")
            if name:
                scim_client.create_group(name)
                show_groups_directory(scim_server.get_groups_snapshot())

        elif ch == "9":
            gid = _pick_group("Group ID")
            if gid:
                uid = _pick_user("User ID to add")
                if uid:
                    users = scim_server.get_users_snapshot()
                    dname = users[uid].get("displayName","") if uid in users else ""
                    scim_client.add_group_member(gid, uid, dname)
                    show_access_matrix(scim_server.get_users_snapshot(), scim_server.get_groups_snapshot())

        elif ch == "0":
            gid = _pick_group("Group ID")
            if gid:
                uid = _pick_user("User ID to remove")
                if uid:
                    scim_client.remove_group_member(gid, uid)
                    show_access_matrix(scim_server.get_users_snapshot(), scim_server.get_groups_snapshot())

        # ── Views ──────────────────────────────────────────────────────────
        elif ch == "a":
            show_access_matrix(scim_server.get_users_snapshot(), scim_server.get_groups_snapshot())

        elif ch == "u":
            show_audit_log(scim_server.get_audit_log_snapshot())

        elif ch == "s":
            scim_client.get_service_provider_config()

        pause("Press [Enter] to continue…")


# ─────────────────────────────────────────────────────────────────────────────
#  main
# ─────────────────────────────────────────────────────────────────────────────

def main():
    show_banner()

    console.print("  [dim]Starting local SCIM 2.0 server on port 5000…[/dim]")
    scim_server.start(port=5000)
    time.sleep(0.5)
    console.print("  [bold green]✓  Server running at http://localhost:5000/scim/v2[/bold green]\n")

    ctx: dict = {}   # carries state between chained scenarios

    while True:
        show_main_menu()
        ch = _prompt_choice("[bold white]Choose [L/1-5/I/Q]:[/bold white]",
                            {"l","1","2","3","4","5","i","q"})

        if ch == "l":
            rest_explainer.run_lesson_menu()

        elif ch == "1":
            scim_server.reset_state()
            ctx = lifecycle.run_onboarding()

        elif ch == "2":
            scim_server.reset_state()
            lifecycle.run_offboarding(ctx)
            ctx = {}

        elif ch == "3":
            scim_server.reset_state()
            lifecycle.run_termination({})

        elif ch == "4":
            scim_server.reset_state()
            lifecycle.run_recertification()

        elif ch == "5":
            scim_server.reset_state()
            lifecycle.run_verification()

        elif ch == "i":
            run_interactive()

        elif ch == "q":
            console.print("\n  [dim]Goodbye! The server stops when this window closes.[/dim]\n")
            sys.exit(0)


if __name__ == "__main__":
    main()
