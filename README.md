# inv2digikey

![Python](https://img.shields.io/badge/Python-3776AB?logo=python&logoColor=white) ![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white) ![React](https://img.shields.io/badge/React-61DAFB?logo=react&logoColor=black) ![PostgreSQL](https://img.shields.io/badge/PostgreSQL-4169E1?logo=postgresql&logoColor=white) ![Docker](https://img.shields.io/badge/Docker-2496ED?logo=docker&logoColor=white) ![OpenSpec](https://img.shields.io/badge/OpenSpec-enforced-blueviolet) ![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)

Mobile-friendly web app to scan QR codes and barcodes from electronic components, store inventory data, and match parts with DigiKey listings.

---

## Features

- **Barcode & QR Code scanning** — uses your device camera to scan DigiKey Data Matrix codes, QR codes, and standard barcodes
- **Auto-parsing** — extracts DigiKey PN, manufacturer PN, quantity, and description directly from scanned labels
- **Inventory management** — store, search, edit, and delete component entries with quantities and locations
- **DigiKey integration** — stores DigiKey and manufacturer part numbers for easy cross-reference
- **Authentication** — username/password protected; first user registers freely, subsequent users require a setup token
- **Mobile-first UI** — responsive design optimized for smartphone use in the field
- **Railway-ready** — deploys in one click with PostgreSQL add-on

---

## How it works

```mermaid
flowchart LR
    A([Open camera]) --> B[Scan label barcode]
    B --> C{Parse format}
    C -->|DigiKey 2D| D[Extract PN + Mfr PN + Qty]
    C -->|Plain barcode| E[Use as part number]
    D --> F[Review & edit parsed data]
    E --> F
    F --> G([Save to inventory])
    G --> H[Search & browse components]
    H --> I[Match with DigiKey store]
```

---

## Quick start

### Local development

```bash
# 1. Clone and install dependencies
git clone https://github.com/arananet/inv2digikey.git
cd inv2digikey
pip install -r requirements.txt

# 2. Configure environment
cp .env.example .env
# Edit .env: set SECRET_KEY and DATABASE_URL

# 3. Run the app
uvicorn main:app --reload

# 4. Open http://localhost:8000 — register your first user
```

### Run tests

```bash
pytest
```

---

## Deployment on Railway

1. Create a new Railway project and link this repo
2. Add a **PostgreSQL** plugin — Railway sets `DATABASE_URL` automatically
3. Set environment variables:
   | Variable | Description |
   |---|---|
   | `SECRET_KEY` | Random secret for JWT signing (generate with `openssl rand -hex 32`) |
   | `DATABASE_URL` | Set automatically by Railway PostgreSQL plugin |
   | `SETUP_TOKEN` | *(optional)* Token required for registering users after the first |
4. Deploy — Railway auto-detects `Procfile` and starts the app

---

## Environment variables

| Variable | Required | Description |
|---|---|---|
| `DATABASE_URL` | Yes | PostgreSQL connection string |
| `SECRET_KEY` | Yes | JWT signing secret |
| `SETUP_TOKEN` | No | If set, blocks new user registration unless this token is provided |

---

## Scanning DigiKey labels

DigiKey bag labels include a **2D Data Matrix** barcode that encodes structured data:

- `K` prefix — DigiKey part number (e.g. `RHM33.0AFCT-ND`)
- `1P` prefix — Manufacturer part number (e.g. `ESR18EZPF33R0`)
- `30P` prefix — Quantity
- `4L` prefix — Manufacturer name

The app parses this automatically. You can also scan regular Code 128 / EAN barcodes and enter additional fields manually.

---

## Project structure

```
inv2digikey/
├── main.py          # FastAPI app — all routes
├── models.py        # SQLAlchemy database models
├── database.py      # Database connection & session
├── auth.py          # JWT authentication helpers
├── schemas.py       # Pydantic request/response schemas
├── requirements.txt
├── Procfile         # Railway / Heroku start command
├── railway.json     # Railway deployment config
├── .env.example     # Environment variable template
├── static/
│   └── index.html   # Single-page application (vanilla JS + Tailwind)
└── tests/
    └── test_api.py  # Pytest API tests
```

---

## OpenSpec

Every feature in this repo is spec-driven. See `.openspec/specs/` for active specs.

```bash
# Install git hooks that enforce spec coverage on commit
bash setup.sh
```

---

**Developer:** Eduardo Arana  
**License:** [MIT](LICENSE)

---

[![ko-fi](https://ko-fi.com/img/githubbutton_sm.svg)](https://ko-fi.com/H2H51MPWG)
