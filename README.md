# Fresh Finder

**Fresh Finder** is a modern Flask web app that lets users explore NBA player and team statistics with ease. It features clean design, smart search, and insightful metrics pulled directly from the NBA API.

## Features

- Autocomplete search for NBA players and teams
- Player game logs, averages, and efficiency stats (FG%, TS%)
- Team dashboards with recent games and advanced metrics (Off/Def Rating, Net Rating)
- Responsive, sleek UI built with HTML/CSS
- Player and team logos integrated throughout

## Tech Stack

- **Backend:** Python (Flask), NBA API (`nba_api`)
- **Frontend:** HTML, CSS, JavaScript (jQuery, Chart.js)
- **Hosting:** Render.com
- **Other:** python-dotenv for environment variable management

## Production Notes

- All routes support a debug JSON mode via `?debug=1` or `Accept: application/json`.
- Global error handler logs tracebacks and returns JSON if debug mode is enabled.
- HTTP retries configured for NBA API requests.
- Intelligent caching system reduces API calls and improves performance.
- Error logging and graceful fallbacks for API timeouts.

## Install

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
```

## Run

```bash
python app.py  # Runs on port 5002
```

## ⚙️ Setup (Local Development)

1. **Clone the repo:**
   ```bash
   git clone https://github.com/ShaunM042/Fresh-Finder.git
   cd Fresh-Finder
   ```
