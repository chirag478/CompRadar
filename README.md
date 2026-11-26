<div align="center">

# 🎯 CompRadar
### Real-Time Competition Radar & Intelligence Terminal

*A lightweight, zero-dependency intelligence terminal to scrape, filter, and track product competitions, tech hackathons, consulting case studies, and marketing challenges from Unstop, Devpost, and curated B-School feeds.*

<br/>

[![Python 3.10+](https://img.shields.io/badge/Python-3.10+-black?style=for-the-badge&logo=python)](https://python.org)
[![Zero External Dependencies](https://img.shields.io/badge/Dependencies-Standard_Library-white?style=for-the-badge)](https://docs.python.org/3/)
[![License: MIT](https://img.shields.io/badge/License-MIT-zinc?style=for-the-badge)](LICENSE)
[![Platform: Cross-Platform](https://img.shields.io/badge/Platform-Windows_%7C_macOS_%7C_Linux-black?style=for-the-badge)]()

</div>

<br/>

---

## 📸 Interface Preview

### 1. High-Density Radar Table (Active Urgency & Monograms)
> *Swiss-style precision table view with active live tickers, deadline countdowns, organizer badges, and instant keyboard navigation.*

![CompRadar High-Density Table View](assets/screenshots/compradar-table.png)

<br/>

### 2. Precision Card Grid (Tactile Inspection)
> *Minimalist cards with organizer initials, prize pools, live status indicators, and one-click WhatsApp sharing.*

![CompRadar Card Grid View](assets/screenshots/compradar-cards.png)

<br/>

### 3. Track Specialization (Strategy, Consulting & Marketing)
> *Dedicated tracks for B-School case challenges, consulting problem statements, and brand growth competitions.*

![CompRadar Strategy & Case View](assets/screenshots/compradar-strategy.png)

---

## ⚡ Core Capabilities

- **Zero-Dependency Architecture**: Runs out-of-the-box on standard Python 3 (`http.server`, `urllib.request`, `sqlite3`). No `pip install`, virtualenvs, or C-compilers required.
- **Multi-Source Scraping**:
  - **Unstop**: Direct public API integration extracting Tech Hackathons, Product Case Studies, Strategy challenges, Brand competitions, and Hiring challenges.
  - **Devpost**: Global open hackathons, AI/ML engineering sprints, and builder summits.
  - **Curated Feeds & CSV Ingestion**: Built-in parser and UI importer for private college spreadsheets (IIMs, XLRI, IITs, corporate case books).
- **Strict Active Filter**: Automatically excludes competitions whose deadlines have passed (`remain_days < 0` or status `FINISHED`).
- **Live Urgency Radar**:
  - Real-time countdown clock calculating exact time remaining (`Xd Xh Xm Xs`) for upcoming deadlines.
  - Muted visual status tags for competitions expiring in $\le$ 3 days or $\le$ 7 days.
- **Application Stage CRM**: Track personal progress for each competition:
  - `Not Applied` $\rightarrow$ `Interested` $\rightarrow$ `Applied` $\rightarrow$ `Shortlisted`.
- **Keyboard-First Navigation** (Linear / Raycast power-user hotkeys):
  - `j` / `k` or `↓` / `↑` — Navigate opportunities
  - `Space` / `Enter` — Open inspection slide-over drawer
  - `s` — Star / Bookmark
  - `w` — Copy WhatsApp-formatted summary
  - `c` — Copy direct official portal URL
  - `o` — Open official challenge portal in new tab
  - `/` — Focus search command bar
  - `?` — View keyboard shortcuts cheat sheet
  - `Esc` — Close drawer / modal
- **One-Click Exports**: Download filtered directories directly as **CSV** or **JSON**.

---

## 🚀 Quickstart

### Prerequisites
- Python 3.10 or higher installed.

### Option 1: One-Click Launch (Windows)
Double-click `run.bat` in the repository root.

### Option 2: Command Line (Windows, macOS, Linux)
```bash
# Clone the repository
git clone https://github.com/chirag478/CompRadar.git
cd CompRadar

# Launch the server (Zero pip install needed!)
python server.py
```

Open your browser at:
👉 **[http://localhost:5000](http://localhost:5000)**

---

## 🔌 REST API Endpoints

CompRadar exposes a built-in REST API:

| Endpoint | Method | Description |
| :--- | :--- | :--- |
| `/api/opportunities` | `GET` | Query opportunities with filters (`source`, `category`, `q`, `sort`, `bookmarked`, `urgent`, `high_prize`) |
| `/api/stats` | `GET` | Returns active counts across categories and bookmark totals |
| `/api/scrape` | `POST` | Triggers concurrent scrapers across Unstop, Devpost, and local feeds |
| `/api/bookmark` | `POST` | Toggles bookmark status for a listing (`{ "id": "..." }`) |
| `/api/status` | `POST` | Updates CRM application stage (`{ "id": "...", "status": "Applied" }`) |
| `/api/import-csv` | `POST` | Ingests raw CSV or pasted competition tables into SQLite cache |
| `/api/export` | `GET` | Downloads current filtered selection as `.csv` or `.json` |

---

## 📁 Repository Structure

```
compradar/
├── assets/
│   └── screenshots/          # Application walkthrough previews
│       ├── compradar-table.png
│       ├── compradar-cards.png
│       └── compradar-strategy.png
├── data/
│   └── curated_competitions.csv  # Seeded B-School case competitions dataset
├── scrapers/
│   ├── aggregator.py         # Concurrent multi-threaded scraping coordinator
│   ├── curated.py            # Local CSV feed scraper & parser
│   ├── devpost.py            # Devpost public API scraper
│   └── unstop.py             # Unstop challenge & case competition scraper
├── static/
│   ├── app.js                # Reactive UI engine with keyboard navigation & tickers
│   ├── index.html            # High-density desktop & mobile layout
│   └── style.css             # Monochrome Swiss design system
├── database.py               # SQLite persistence & caching layer
├── opportunities.db          # Pre-seeded SQLite database with active competitions
├── run.bat                   # Windows launcher script
├── server.py                 # Multi-threaded Python HTTP REST API server
└── README.md
```

---

## 📜 License

Distributed under the MIT License. See `LICENSE` for details.
