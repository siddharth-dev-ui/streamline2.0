# Streamline

AI-powered investment research platform built with Python and Streamlit.

## Project Structure

```
Streamline/
├── app.py              # Main Streamlit entry point
├── pages/              # Additional Streamlit pages
├── analysis/           # Technical & fundamental analysis
├── ai/                 # AI research & insights
├── portfolio/          # Portfolio tracking
├── watchlist/          # Watchlist management
├── data/               # Data fetching & storage
├── utils/              # Shared helpers
├── assets/             # Static assets (images, icons)
├── requirements.txt
├── .env.example
└── README.md
```

## Setup

1. Create and activate a virtual environment:

```bash
python -m venv .venv
```

**Windows (PowerShell):**

```powershell
.venv\Scripts\Activate.ps1
```

**macOS / Linux:**

```bash
source .venv/bin/activate
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Streamline uses a built-in local model (`StreamlineLLM`) by default — no API key required.

Optional: copy `.env.example` to `.env` only if you later reconnect a remote provider.

## Run

From the project root:

```bash
streamlit run app.py
```

The app opens at `http://localhost:8501` with the marketing landing page first.
Click **Get started** / **Start researching** to enter the workspace (`?app=1`).
Return to the landing anytime with `?landing=1`.

You can also open the static landing with the live demo API:

```bash
# from project root (uses yfinance for live recommendations)
python landing/server.py
```

Then visit `http://127.0.0.1:8080` and type a ticker in the hero demo.
