# MoneyManager Pro

AI-powered money management application built with Flask.

## Features
- Dashboard with financial health score
- Income & salary tracking
- Expense tracker with 50/30/20 budget analysis
- Investment portfolio manager (all platforms)
- AI-powered investment suggestions (Gold, Silver, Stocks, MF)
- Asset buying plans (Car, House, Land, Farming Land)
- SIP, Lumpsum, EMI, FD, Retirement calculators
- Financial goals tracking
- Reports & turnover analysis
- Dark/Light theme

## Local Setup
```bash
python -m venv .venv
.venv\Scripts\activate      # Windows
pip install -r requirements.txt
python app.py
```

## Deploy to Render
1. Push to GitHub
2. Create new Web Service on render.com
3. Build: `pip install -r requirements.txt`
4. Start: `gunicorn app:app --bind 0.0.0.0:$PORT`
