"""
examples/demo_crud.py
---------------------
Standalone script: start the server + run a full SCIM CRUD cycle.

Run from the project root:
    python examples/demo_crud.py
"""

import sys
import time
sys.path.insert(0, ".")   # make sure src/ is importable

from src import scim_server, scim_client
from src.visualizer import console, show_section, show_user_directory

# ── 1. Start server ───────────────────────────────────────────────────────────
console.print("\n[dim]Starting SCIM server…[/dim]")
scim_server.start(port=5000)
time.sleep(0.5)
console.print("[green]✓ Server ready at http://localhost:5000/scim/v2[/green]\n")

# ── 2. Create users ───────────────────────────────────────────────────────────
show_section("1 · Create Users  (POST)")
_, alice = scim_client.create_user(
    "alice.example", "Alice Example", "alice@example.com", "Alice", "Example"
)
_, bob = scim_client.create_user(
    "bob.example", "Bob Example", "bob@example.com", "Bob", "Example"
)

# ── 3. List users ─────────────────────────────────────────────────────────────
show_section("2 · List Users  (GET)")
scim_client.list_users()
show_user_directory(scim_server.get_users_snapshot())

# ── 4. Get one user ───────────────────────────────────────────────────────────
show_section("3 · Get Alice  (GET /<id>)")
scim_client.get_user(alice["id"])

# ── 5. PATCH — deactivate Bob ─────────────────────────────────────────────────
show_section("4 · Deactivate Bob  (PATCH active=false)")
scim_client.deactivate_user(bob["id"])
show_user_directory(scim_server.get_users_snapshot())

# ── 6. DELETE — remove Alice ──────────────────────────────────────────────────
show_section("5 · Delete Alice  (DELETE)")
scim_client.delete_user(alice["id"])
show_user_directory(scim_server.get_users_snapshot())

console.print("\n[bold green]✓ Demo complete![/bold green]\n")
