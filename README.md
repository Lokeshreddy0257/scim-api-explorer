# SCIM API Explorer

An interactive, beginner-friendly CLI tool for learning **REST APIs** and **SCIM 2.0** — visually, in your terminal.

Run it and watch real HTTP requests fly between a local SCIM client and a live Flask server, with every request/response displayed in color-coded panels.

---

## What is SCIM?

SCIM (System for Cross-domain Identity Management) is a standard REST API used by enterprise Identity Providers (Okta, Azure AD, Google Workspace) to automatically provision and deprovision user accounts across SaaS apps like Slack, GitHub, Salesforce, and more.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        main.py (CLI)                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │  [L] Lessons  │  │  [D] Demo    │  │  [I] Interactive │  │
│  │ rest_explainer│  │ scim_client  │  │  scim_client     │  │
│  └──────────────┘  └──────┬───────┘  └────────┬─────────┘  │
│                            │  HTTP              │            │
│              ┌─────────────▼──────────────────▼──────────┐  │
│              │         scim_server (Flask, port 5000)     │  │
│              │   GET/POST/PUT/PATCH/DELETE /scim/v2/Users │  │
│              │         In-memory user store (dict)        │  │
│              └───────────────────────────────────────────┘  │
│                                                              │
│              visualizer.py — all Rich terminal output        │
└─────────────────────────────────────────────────────────────┘
```

---

## Features

| Mode | What it does |
|------|-------------|
| **Lessons** | 5 guided lessons on REST concepts, HTTP methods, status codes, and SCIM |
| **Demo** | Fully automated walkthrough: create 3 users → list → patch → deactivate → delete |
| **Interactive** | Pick any SCIM operation and run it live against the server |

---

## Quickstart

```bash
# 1. Clone
git clone https://github.com/Lokeshreddy0257/scim-api-explorer.git
cd scim-api-explorer

# 2. Install dependencies
pip install -r requirements.txt

# 3. Copy env file
cp .env.example .env

# 4. Run
python main.py
```

---

## Project Structure

```
scim-api-explorer/
├── main.py                    # CLI entry point + interactive menu
├── requirements.txt
├── .env.example
├── src/
│   ├── __init__.py
│   ├── scim_server.py         # Flask SCIM 2.0 server (in-memory)
│   ├── scim_client.py         # HTTP client with request/response visualizer
│   ├── rest_explainer.py      # 5 beginner lessons on REST + SCIM
│   └── visualizer.py          # Rich terminal UI helpers
└── examples/
    ├── demo_crud.py           # Standalone CRUD demo script
    └── demo_service_provider.py  # ServiceProviderConfig demo
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
| `PATCH` | `/scim/v2/Users/<id>` | Partial update (deactivate, rename…) |
| `DELETE` | `/scim/v2/Users/<id>` | Delete a user |

---

## Requirements

- Python 3.10+
- `flask>=3.0.0`
- `requests>=2.31.0`
- `rich>=13.7.0`
- `python-dotenv>=1.0.0`

---

## Examples

**Run the standalone CRUD demo:**
```bash
python examples/demo_crud.py
```

**Inspect ServiceProviderConfig:**
```bash
python examples/demo_service_provider.py
```

---

## License

MIT
