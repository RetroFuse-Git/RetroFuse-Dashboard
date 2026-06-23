# RetroFuse OPS Dashboard

**Canonical root:** `D:\RETROFUSE_OPS\Dashboard`

The OPS Dashboard is a FastAPI-based operational status dashboard for the RetroFuse
ecosystem. It renders RFCC health, browser telemetry (RC1/RC2/RC3), SAFEPOINT engine
status, Alpha capture, model fleet health, wrapper registry, and OPS COO orchestrator
telemetry — all from local DailyCheck snapshots and live process scans.

## Quick Start

```powershell
# Activate virtual environment
.venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start the dashboard
python -m uvicorn server:app --host 127.0.0.1 --port 8101
```

Open `http://127.0.0.1:8101` in a browser.

## Project Structure

```
D:\RETROFUSE_OPS\Dashboard\
├── app/                    # Python application modules
│   ├── model_dashboard.py # Model dashboard, settings, routing, assets, wrappers
│   └── app_main.py        # Application entry point
├── templates/              # Jinja2/HTML templates
│   └── index.html          # Main dashboard template (canonical)
├── static/                 # Static assets
│   └── index.html           # Static fallback
├── Tools/
│   ├── maintenance/        # Maintenance receipts, registry data, phase docs
│   └── validation/         # Validation scripts (future)
├── docs/                   # Product documentation (future)
├── _Archive/               # Historical dashboard index snapshots
├── _Forensic/              # Forensic backups of mangled states
├── _Work/                  # Runtime work logs (gitignored)
├── server.py               # FastAPI server with embedded INDEX_HTML fallback
├── requirements.txt        # Python dependencies
├── README.md               # This file
├── CHANGELOG.md            # Version history
├── ROADMAP.md              # Planned work
├── DASHBOARD_PRODUCT_BOUNDARY.md  # Product boundary declaration
├── .gitignore              # Git ignore rules
├── BLUEPRINT.md            # Original project blueprint
├── RUN_CONTRACT.json       # Run contract
├── WORKER_BRIEF.md         # Worker brief
└── Start_*.ps1             # PowerShell startup scripts
```

## Architecture Notes

- **Dual-template architecture:** `server.py` embeds an `INDEX_HTML` fallback string.
  The canonical template is `templates/index.html`. Keeping them in sync is
  acknowledged design debt (see `DASHBOARD_PRODUCT_BOUNDARY.md`).
- **Read-only display:** The dashboard is read-only. Settings edits require explicit
  apply actions with receipt tracking.
- **No launch endpoint:** Wrapper/model launch is not wired in this phase.
- **Effective Settings Intelligence:** Phase 2 adds per-model effective settings with
  source stack (factory default, Modelfile, runtime override, wrapper profile),
  hazard profiles (cost-sensitive, settings-sensitive, needs profile), and Ollama
  parameter intelligence documentation. All read-only — no mutation.
- **Settings groups:** Core (home-visible), Sampling, Prompt/Session, Ollama Server,
  Persistence & Profiles. Home Mode shows simplified core values; Business Mode
  shows full source provenance.

## Dependencies

- Python 3.12+
- FastAPI
- uvicorn

See `requirements.txt` for full list.
