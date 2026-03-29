"""
examples/demo_service_provider.py
----------------------------------
Shows the SCIM ServiceProviderConfig endpoint — the "capabilities" document
every real SCIM server exposes so clients know what features are supported.

Run from the project root:
    python examples/demo_service_provider.py
"""

import sys
import time
sys.path.insert(0, ".")

from src import scim_server, scim_client
from src.visualizer import console, show_section, show_explanation

console.print("\n[dim]Starting SCIM server…[/dim]")
scim_server.start(port=5000)
time.sleep(0.5)
console.print("[green]✓ Server ready[/green]\n")

show_section("ServiceProviderConfig  (GET /scim/v2/ServiceProviderConfig)")

show_explanation(
    "ℹ️", "What is ServiceProviderConfig?",
    """
  Every SCIM server must expose a /ServiceProviderConfig endpoint.
  It's a discovery document that tells the client (e.g. Okta) what
  optional SCIM features this server supports:

    • patch        — does it support PATCH operations?
    • bulk         — does it support batching many ops in one request?
    • filter       — can you filter users with ?filter=userName eq "alice"?
    • sort         — can results be sorted?
    • etag          — does it support HTTP caching via ETags?

  Clients use this to adapt their behaviour — no manual docs required!
    """,
    "cyan",
)

scim_client.get_service_provider_config()

console.print("\n[bold green]✓ Done![/bold green]\n")
