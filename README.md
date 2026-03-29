# SCIM API Explorer

An interactive CLI simulator for learning **REST APIs**, **SCIM 2.0**, and **enterprise identity lifecycle management** — the way it actually works at companies like Databricks.

Watch real HTTP requests fly between a local SCIM client and a live Flask server. Every request and response is displayed in color-coded panels so the invisible becomes visible.

---

## What You'll Learn

| Scenario | What it simulates |
|----------|-------------------|
| **Onboarding** | New hire → AD group created → SCIM provisions user → Databricks access granted |
| **Offboarding** | Team transfer → old group removed → new group added → access swapped |
| **Termination** | Employee exits → immediate deactivation → group cleanup → permanent deletion |
| **Recertification** | 90-day access review → manager approves 3, revokes 1 stale account |
| **Verification** | Nightly job detects drift vs AD source of truth → auto-remediates |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                          main.py  (CLI)                             │
│                                                                     │
│  [L] Lessons   [1] Onboard  [2] Offboard  [3] Terminate            │
│  [4] Recert    [5] Verify   [I] Interactive                        │
│       │              │            │                                 │
│       ▼              ▼            ▼                                 │
│  rest_explainer   lifecycle.py  (5 enterprise scenarios)           │
│  (7 lessons)       │                                                │
│                    │── scim_client.py  (HTTP client + visualizer)   │
│                    │                          │                     │
│                    │                          ▼  real HTTP calls    │
│                    └──────────── scim_server.py (Flask SCIM 2.0)   │
│                                    Users + Groups + Audit Log       │
│                                                                     │
│  visualizer.py — all Rich terminal output (panels, tables, etc.)   │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Quickstart

```bash
git clone https://github.com/Lokeshreddy0257/scim-api-explorer.git
cd scim-api-explorer
pip install -r requirements.txt
cp .env.example .env
python main.py
```

---

## Project Structure

```
scim-api-explorer/
├── main.py                     # CLI entry point — 8-option menu
├── requirements.txt
├── .env.example
├── src/
│   ├── __init__.py
│   ├── scim_server.py          # Flask SCIM 2.0 server (Users + Groups + Audit Log)
│   ├── scim_client.py          # HTTP client — shows every request + response
│   ├── lifecycle.py            # 5 enterprise lifecycle scenarios
│   ├── rest_explainer.py       # 7 beginner lessons (REST → SCIM → RBAC)
│   └── visualizer.py           # All Rich terminal UI (panels, tables, diagrams)
└── examples/
    └── demo_lifecycle.py       # Standalone: all 5 scenarios end-to-end
```

---

## SCIM Endpoints Implemented

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/scim/v2/ServiceProviderConfig` | Server capabilities |
| `GET` | `/scim/v2/Users` | List all users |
| `POST` | `/scim/v2/Users` | Create a user |
| `GET` | `/scim/v2/Users/<id>` | Get one user |
| `PUT` | `/scim/v2/Users/<id>` | Replace a user (full update) |
| `PATCH` | `/scim/v2/Users/<id>` | Partial update (deactivate, rename, dept) |
| `DELETE` | `/scim/v2/Users/<id>` | Delete a user |
| `GET` | `/scim/v2/Groups` | List all groups |
| `POST` | `/scim/v2/Groups` | Create a group (AD group) |
| `GET` | `/scim/v2/Groups/<id>` | Get one group |
| `PATCH` | `/scim/v2/Groups/<id>` | Add/remove members (filter-path syntax supported) |
| `DELETE` | `/scim/v2/Groups/<id>` | Delete a group |

---

## The Lifecycle Flow

```
HR System → Identity Provider (AD/Okta) → SCIM → Databricks
                                             │
              ┌──────────────────────────────┼─────────────────────┐
              │                              │                     │
         [Onboard]                     [Transfer]           [Terminate]
         POST /Users                   PATCH /Groups        DELETE /Users
         POST /Groups                  (add + remove)       PATCH active=f
         add member                                         + PATCH /Groups
              │
    ──────────────────────────────────────────────────────────────────
         [Recertification — Every 90 Days]
         Manager reviews who still needs access → revoke stale accounts
    ──────────────────────────────────────────────────────────────────
         [Nightly Verification — Every Night at 2 AM]
         Compare AD (expected) vs Databricks (actual) → fix drift
```

---

## Run the Full Demo

```bash
python examples/demo_lifecycle.py
```

---

## Requirements

- Python 3.10+
- `flask>=3.0.0`
- `requests>=2.31.0`
- `rich>=13.7.0`
- `python-dotenv>=1.0.0`

---

## License

MIT
