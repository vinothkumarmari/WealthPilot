# WealthPilot — AI-Powered Personal Finance Platform

WealthPilot is a comprehensive personal finance management application built with Flask. It helps users track income, expenses, investments, insurance, loans, and more — with AI-powered recommendations, live commodity rates, and multi-language support.

## Key Features

- **Dashboard** — Financial health score, net worth, 6-month trends, quick actions
- **Income & Expenses** — 8 income types, 15 expense categories, 50/30/20 budget analysis
- **Investments** — Portfolio tracker with unified view (stocks, MF, FD, policies, SIPs, schemes)
- **Insurance Policies** — 19 providers, 11 policy types, premium tracking, OCR document scanning
- **Schemes & Bonds** — 13 scheme types, government & corporate bond directory
- **SIP Tracker** — Fund tracking with performance analysis
- **Loans** — EMI tracking, AI loan scoring (Good/Average/Bad), prepayment tips
- **Gold, Silver & Platinum** — Live rates (5 gold purities), AM/PM comparison, 80+ day charts, 12-month & 5-year history
- **Budget Planner** — Category-wise monthly budgeting
- **Tax Planning** — 80C/80D/80CCD deductions, old vs new regime comparison
- **Financial Calculators** — SIP, Lumpsum, EMI, FD, Retirement
- **AI Suggestions** — Investment plans, asset buying timing, commodity recommendations
- **Business Ideas** — AI-powered business recommendations with govt entrepreneurship schemes
- **Government Schemes** — Central & state schemes, subsidies with apply links
- **Goals** — Target-based tracking with SIP calculations
- **Notifications** — Auto-generated alerts for premiums, EMIs, SIPs, goals
- **Reports** — Monthly reports, category analysis, turnover
- **Multi-Language** — English, Tamil, Hindi, Telugu
- **PWA** — Installable as native app on mobile & desktop
- **Dark/Light Theme** — Automatic preference saving

## Security

- CSRF protection on all forms & AJAX calls
- Password hashing (Werkzeug/bcrypt)
- Email OTP verification (6-digit, 5-min expiry)
- Rate limiting (login, registration, OTP)
- Security headers (X-Frame-Options, X-Content-Type-Options, HSTS)
- File upload validation & sanitization

## Tech Stack

- **Backend:** Flask 3.0, SQLAlchemy, Flask-Login, Flask-WTF, Flask-Mail, Flask-Limiter
- **Database:** SQLite (development), PostgreSQL-ready
- **Frontend:** Bootstrap 5.3, Chart.js, Material Icons
- **AI Engine:** Custom ML-based financial advisor (numpy)
- **PWA:** Service worker, manifest.json, 8 icon sizes

## Local Setup

```bash
git clone https://github.com/vinothkumarmari/WealthPilot.git
cd WealthPilot
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # Linux/Mac
pip install -r requirements.txt
cp .env.example .env          # Edit with your values
python run.py
```

Open http://localhost:7777

## Deploy to Production

### Render.com
1. Push to GitHub
2. Create new Web Service on render.com
3. Build: `pip install -r requirements.txt`
4. Start: `gunicorn run:application --bind 0.0.0.0:$PORT --workers 2`
5. Set environment variables from `.env.example`

### Docker
```bash
cp .env.example .env    # Edit values
docker-compose up -d
```

### Railway / Fly.io
Use the included `Procfile` and set environment variables from `.env.example`.

## Environment Variables

See `.env.example` for all required variables:
- `SECRET_KEY` — Flask session secret (change in production!)
- `DATABASE_URL` — Database connection string
- `MAIL_USERNAME` / `MAIL_PASSWORD` — SMTP credentials for OTP emails
- `ADMIN_USERNAME` / `ADMIN_PASSWORD` — Initial admin credentials

## Project Structure

```
app/
├── __init__.py          # App factory, extensions, security headers
├── config.py            # Configuration constants
├── models.py            # 16 SQLAlchemy models
├── routes.py            # 88+ route endpoints
├── ml_engine.py         # AI financial advisor engine
├── ibja_rates.py        # Live commodity rate engine
├── translations.py      # Multi-language support
├── templates/           # 36 Jinja2 templates
└── static/              # CSS, JS, PWA icons, manifest
```

## License

All rights reserved. © 2026 WealthPilot.
