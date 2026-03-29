"""
examples/demo_lifecycle.py
--------------------------
Standalone end-to-end script: runs all 5 enterprise lifecycle scenarios
in sequence without the interactive menu.

Run from the project root:
    python examples/demo_lifecycle.py

What you'll see:
  Scenario 1 — Onboarding      (new hire gets Databricks access)
  Scenario 2 — Offboarding     (team transfer, access swap)
  Scenario 3 — Termination     (employee exits, all access revoked)
  Scenario 4 — Recertification (90-day review, stale account revoked)
  Scenario 5 — Verification    (nightly drift detection + auto-fix)
  Final audit log              (all events across all scenarios)
"""

import sys
import time
sys.path.insert(0, ".")

from src import scim_server, lifecycle
from src.visualizer import console, show_banner, show_section, show_audit_log

# ── Start server ──────────────────────────────────────────────────────────────
console.print("\n[dim]Starting SCIM 2.0 server…[/dim]")
scim_server.start(port=5000)
time.sleep(0.5)
console.print("[green]✓ Server ready at http://localhost:5000/scim/v2[/green]\n")

show_banner()

# ── Scenario 1: Onboarding ────────────────────────────────────────────────────
show_section("SCENARIO 1 OF 5 — Onboarding")
scim_server.reset_state()
ctx = lifecycle.run_onboarding()

# ── Scenario 2: Offboarding ───────────────────────────────────────────────────
show_section("SCENARIO 2 OF 5 — Offboarding (Team Transfer)")
scim_server.reset_state()
lifecycle.run_offboarding(ctx)

# ── Scenario 3: Termination ───────────────────────────────────────────────────
show_section("SCENARIO 3 OF 5 — Termination")
scim_server.reset_state()
lifecycle.run_termination({})

# ── Scenario 4: Recertification ───────────────────────────────────────────────
show_section("SCENARIO 4 OF 5 — Recertification")
scim_server.reset_state()
lifecycle.run_recertification()

# ── Scenario 5: Nightly Verification ─────────────────────────────────────────
show_section("SCENARIO 5 OF 5 — Nightly Verification")
scim_server.reset_state()
lifecycle.run_verification()

# ── Final audit log (all scenarios — log survives resets) ─────────────────────
show_section("Complete Audit Trail — All Scenarios")
show_audit_log(scim_server.get_audit_log_snapshot())

console.print("\n[bold green]✓ Full enterprise lifecycle demo complete.[/bold green]\n")
