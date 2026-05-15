"""
myWealthPilot - Complete Technical Documentation PDF Generator
Generated: May 2026
"""
from fpdf import FPDF
from datetime import datetime


class DocPDF(FPDF):
    def header(self):
        if self.page_no() == 1:
            return
        self.set_font("Helvetica", "B", 9)
        self.set_text_color(108, 92, 231)
        self.cell(0, 7, "myWealthPilot - Technical Documentation", align="R")
        self.ln(3)
        self.set_draw_color(108, 92, 231)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(140, 140, 140)
        self.cell(0, 10, f"Page {self.page_no()}/{{nb}}", align="C")

    def chapter_title(self, num, title):
        self.set_font("Helvetica", "B", 16)
        self.set_text_color(108, 92, 231)
        self.cell(0, 12, f"{num}. {title}", new_x="LMARGIN", new_y="NEXT")
        self.set_draw_color(108, 92, 231)
        self.line(10, self.get_y(), 80, self.get_y())
        self.ln(4)

    def section_title(self, title):
        self.set_font("Helvetica", "B", 12)
        self.set_text_color(74, 0, 224)
        self.cell(0, 9, title, new_x="LMARGIN", new_y="NEXT")
        self.ln(1)

    def body_text(self, text):
        self.set_font("Helvetica", "", 10)
        self.set_text_color(50, 50, 50)
        self.multi_cell(0, 5.5, text)
        self.ln(2)

    def bullet(self, text, indent=10):
        self.set_font("Helvetica", "", 9)
        self.set_text_color(50, 50, 50)
        safe = text.encode('latin-1', 'replace').decode('latin-1')
        self.set_x(10)
        self.multi_cell(0, 5, f"  - {safe}")

    def table_row(self, key, value, header=False):
        col1_w = 58
        col2_w = 128
        if header:
            self.set_font("Helvetica", "B", 9)
            self.set_fill_color(108, 92, 231)
            self.set_text_color(255, 255, 255)
            self.cell(col1_w, 7, key, border=1, fill=True)
            self.cell(col2_w, 7, value, border=1, fill=True, new_x="LMARGIN", new_y="NEXT")
        else:
            self.set_fill_color(248, 246, 255)
            self.set_font("Helvetica", "B", 9)
            self.set_text_color(50, 50, 50)
            self.cell(col1_w, 7, key, border=1, fill=True)
            self.set_font("Helvetica", "", 9)
            self.cell(col2_w, 7, value, border=1, new_x="LMARGIN", new_y="NEXT")

    def table3(self, c1, c2, c3, header=False):
        w1, w2, w3 = 50, 68, 68
        if header:
            self.set_font("Helvetica", "B", 9)
            self.set_fill_color(108, 92, 231)
            self.set_text_color(255, 255, 255)
            self.cell(w1, 7, c1, border=1, fill=True)
            self.cell(w2, 7, c2, border=1, fill=True)
            self.cell(w3, 7, c3, border=1, fill=True, new_x="LMARGIN", new_y="NEXT")
        else:
            self.set_fill_color(248, 246, 255)
            self.set_font("Helvetica", "B", 9)
            self.set_text_color(50, 50, 50)
            self.cell(w1, 7, c1, border=1, fill=True)
            self.set_font("Helvetica", "", 9)
            self.cell(w2, 7, c2, border=1)
            self.cell(w3, 7, c3, border=1, new_x="LMARGIN", new_y="NEXT")

    def status_badge(self, text, color):
        self.set_font("Helvetica", "B", 8)
        r, g, b = color
        self.set_fill_color(r, g, b)
        self.set_text_color(255, 255, 255)
        w = self.get_string_width(text) + 8
        self.cell(w, 6, text, fill=True)
        self.set_text_color(50, 50, 50)


pdf = DocPDF()
pdf.alias_nb_pages()
pdf.set_auto_page_break(auto=True, margin=20)

# ==================== COVER PAGE ====================
pdf.add_page()
pdf.ln(30)
pdf.set_font("Helvetica", "B", 36)
pdf.set_text_color(108, 92, 231)
pdf.cell(0, 20, "myWealthPilot", align="C", new_x="LMARGIN", new_y="NEXT")
pdf.set_font("Helvetica", "", 14)
pdf.set_text_color(100, 100, 100)
pdf.cell(0, 8, "Complete Technical Documentation", align="C", new_x="LMARGIN", new_y="NEXT")
pdf.cell(0, 8, "Architecture | Features | Infrastructure | Future Roadmap", align="C", new_x="LMARGIN", new_y="NEXT")
pdf.ln(10)
pdf.set_draw_color(108, 92, 231)
pdf.line(60, pdf.get_y(), 150, pdf.get_y())
pdf.ln(10)
pdf.set_font("Helvetica", "", 11)
pdf.set_text_color(120, 120, 120)
pdf.cell(0, 7, f"Version 2.0 | Generated: {datetime.now().strftime('%d %B %Y')}", align="C", new_x="LMARGIN", new_y="NEXT")
pdf.cell(0, 7, "mywealthpilot.in", align="C", new_x="LMARGIN", new_y="NEXT")
pdf.ln(30)

# Table of Contents
pdf.set_font("Helvetica", "B", 14)
pdf.set_text_color(108, 92, 231)
pdf.cell(0, 10, "Table of Contents", new_x="LMARGIN", new_y="NEXT")
pdf.ln(3)
toc = [
    ("1", "Executive Summary"),
    ("2", "Technology Stack"),
    ("3", "Infrastructure & Hosting"),
    ("4", "Security Architecture"),
    ("5", "Database Schema (25 Models)"),
    ("6", "Core Features (Currently Live)"),
    ("7", "AI & ML Engine"),
    ("8", "WealthCard - Financial Trust Score"),
    ("9", "Subscription Plans & Pricing"),
    ("10", "PWA & Offline Capabilities"),
    ("11", "Internationalization (i18n)"),
    ("12", "Admin Panel"),
    ("13", "Architecture Flow"),
    ("14", "Current Limitations"),
    ("15", "FUTURE: Smart Statement Import"),
    ("16", "FUTURE: Passkey Authentication"),
    ("17", "FUTURE: Advanced Roadmap"),
    ("18", "Appendix: API Routes (151+)"),
]
for num, title in toc:
    pdf.set_font("Helvetica", "", 11)
    pdf.set_text_color(50, 50, 50)
    pdf.cell(12, 6, num + ".")
    pdf.cell(0, 6, title, new_x="LMARGIN", new_y="NEXT")
pdf.ln(5)

# ==================== 1. EXECUTIVE SUMMARY ====================
pdf.add_page()
pdf.chapter_title("1", "Executive Summary")
pdf.body_text(
    "myWealthPilot is a comprehensive personal finance management platform built for Indian users. "
    "It provides 30+ financial tools spanning expense tracking, investment portfolio management, "
    "insurance analysis, tax planning, AI-powered suggestions, and gamification - all within a "
    "Progressive Web App (PWA) that works offline and supports 4 Indian languages."
)
pdf.body_text(
    "The platform operates entirely on free-tier infrastructure (Rs.0/month excluding domain renewal), "
    "serving users through Render.com hosting with a Neon.tech PostgreSQL database. "
    "It features a unique WealthCard - Financial Trust Score system that no other Indian finance app offers."
)
pdf.section_title("Key Metrics")
for k, v in [
    ("Total Routes", "151+ API endpoints"),
    ("Templates", "67 HTML pages"),
    ("Database Models", "25 tables"),
    ("Languages", "4 (English, Tamil, Hindi, Telugu)"),
    ("Translation Keys", "850+"),
    ("Expense Categories", "16"),
    ("Investment Types", "20+"),
    ("Calculators", "15+"),
    ("Python Dependencies", "17 packages"),
    ("Monthly Cost", "Rs.0 (all free tiers)"),
]:
    pdf.table_row(k, v)
pdf.ln(5)

# ==================== 2. TECHNOLOGY STACK ====================
pdf.add_page()
pdf.chapter_title("2", "Technology Stack")

pdf.section_title("Backend")
for k, v in [
    ("Language", "Python 3.12"),
    ("Framework", "Flask 3.0"),
    ("ORM", "SQLAlchemy + Flask-SQLAlchemy 3.1.1"),
    ("Migration", "Flask-Migrate 4.0.5 (Alembic)"),
    ("Auth", "Flask-Login 0.6.3"),
    ("Forms/CSRF", "Flask-WTF 1.2.1 + WTForms 3.1.1"),
    ("Rate Limiting", "Flask-Limiter 3.5.0"),
    ("Email", "Flask-Mail 0.10.0"),
    ("WSGI Server", "Gunicorn 21.2.0"),
    ("PDF Parsing", "pdfplumber 0.11.9"),
    ("Image Processing", "Pillow 12.1.1"),
    ("HTTP Client", "requests 2.33.1"),
    ("HTML Parsing", "beautifulsoup4 4.14.3"),
    ("Date Utils", "python-dateutil 2.8.2"),
    ("Numerics", "numpy 1.26.2"),
    ("Validation", "email-validator 2.1.0"),
    ("PostgreSQL Driver", "psycopg[binary] >= 3.1.0"),
]:
    pdf.table_row(k, v)
pdf.ln(4)

pdf.section_title("Frontend")
for k, v in [
    ("CSS Framework", "Bootstrap 5.3.2"),
    ("Charts", "Chart.js 4.4.1"),
    ("Icons", "Material Icons Outlined (Google)"),
    ("Fonts", "Google Fonts - Inter"),
    ("Theme", "#6C5CE7 purple, gradient #4A00E0 to #8E2DE2"),
    ("Voice Input", "Web Speech API (browser-native)"),
    ("Offline Storage", "IndexedDB (browser-native)"),
    ("PWA", "Service Worker + manifest.json"),
    ("QR Codes", "goqr.me API (for WealthCard)"),
]:
    pdf.table_row(k, v)
pdf.ln(4)

pdf.section_title("Payment")
for k, v in [
    ("Gateway", "Razorpay (INR)"),
    ("Methods", "UPI, Cards, Wallets, Net Banking"),
    ("Webhooks", "Signature verification (HMAC-SHA256)"),
]:
    pdf.table_row(k, v)
pdf.ln(5)

# ==================== 3. INFRASTRUCTURE ====================
pdf.add_page()
pdf.chapter_title("3", "Infrastructure & Hosting")

pdf.section_title("Web Server - Render.com")
for k, v in [
    ("Plan", "Free ($0/month)"),
    ("CPU", "Shared CPU (0.1 vCPU)"),
    ("RAM", "512 MB (hard limit, SIGKILL on exceed)"),
    ("Workers", "2 Gunicorn sync workers, 120s timeout"),
    ("Bandwidth", "100 GB/month"),
    ("Auto-deploy", "Yes - on git push to main"),
    ("Sleep", "15 min idle -> sleep (cron-job.org keeps alive)"),
    ("Cold Start", "~30-50 seconds"),
    ("SSL", "Let's Encrypt (auto-managed)"),
    ("Region", "Oregon (US West)"),
    ("Health Check", "/health endpoint"),
    ("Runtime", "Python 3.12.0"),
]:
    pdf.table_row(k, v)
pdf.ln(4)

pdf.section_title("Database - Neon.tech")
for k, v in [
    ("Plan", "Free ($0/month, no expiry)"),
    ("Engine", "PostgreSQL 17"),
    ("Storage", "0.5 GB limit (~34 MB used)"),
    ("Compute", "Autoscaling up to 2 CU, scale-to-zero"),
    ("Tables", "25 (24 app + 1 Alembic)"),
    ("Branches", "10 per project"),
    ("Region", "US East 1 (N. Virginia, AWS)"),
    ("Connection", "SSL required (sslmode=require)"),
]:
    pdf.table_row(k, v)
pdf.ln(4)

pdf.section_title("Domain & DNS")
for k, v in [
    ("Domain", "mywealthpilot.in"),
    ("Render Subdomain", "wealthpilot-wcm7.onrender.com"),
    ("SSL", "Auto Let's Encrypt"),
    ("Cost", "~Rs.500-800/year (renewal only)"),
]:
    pdf.table_row(k, v)
pdf.ln(4)

pdf.section_title("CI/CD & Source Control")
for k, v in [
    ("Repository", "GitHub - vinothkumarmari/WealthPilot"),
    ("Plan", "GitHub Free"),
    ("Build", "pip install -r requirements.txt && flask db upgrade"),
    ("Start", "gunicorn run:application --bind 0.0.0.0:$PORT --workers 2 --timeout 120"),
]:
    pdf.table_row(k, v)
pdf.ln(4)

pdf.section_title("Keep-Alive")
for k, v in [
    ("Service", "cron-job.org (Free)"),
    ("Interval", "Every 14 minutes -> /login"),
    ("Purpose", "Prevent Render free tier sleep"),
]:
    pdf.table_row(k, v)
pdf.ln(4)

pdf.section_title("Monthly Cost Summary")
pdf.table3("Service", "Plan", "Cost", header=True)
for c1, c2, c3 in [
    ("Render Web Service", "Free", "$0"),
    ("Neon PostgreSQL", "Free", "$0"),
    ("GitHub", "Free", "$0"),
    ("cron-job.org", "Free", "$0"),
    ("Domain (annual)", "mywealthpilot.in", "~Rs.700/yr"),
    ("TOTAL", "", "Rs.0/month"),
]:
    pdf.table3(c1, c2, c3)
pdf.ln(5)

# ==================== 4. SECURITY ====================
pdf.add_page()
pdf.chapter_title("4", "Security Architecture")

pdf.section_title("Authentication & Authorization")
for k, v in [
    ("Password Hashing", "Werkzeug pbkdf2:sha256 (salted)"),
    ("OTP", "6-digit, HMAC-SHA256 hashed, 10-min expiry"),
    ("Session", "Flask-Login, server-side, 30-min idle timeout"),
    ("Max Session", "2 hours absolute"),
    ("Lockout", "5 failed login attempts"),
    ("Admin Bypass", "OTP skip for admin + trusted users"),
    ("Per-User OTP", "Toggleable from admin panel"),
]:
    pdf.table_row(k, v)
pdf.ln(3)

pdf.section_title("Transport & Data Security")
for k, v in [
    ("HTTPS", "TLS 1.3 via Let's Encrypt"),
    ("Database", "SSL (sslmode=require)"),
    ("CSRF", "Flask-WTF token on all forms"),
    ("Rate Limiting", "Flask-Limiter on sensitive endpoints"),
    ("IPv4 Forced", "socket.getaddrinfo patched for AF_INET"),
    ("Input Validation", "WTForms + server-side checks"),
    ("File Upload", "Type validation, size limits"),
    ("XSS Prevention", "Jinja2 auto-escaping"),
    ("SQL Injection", "SQLAlchemy ORM (parameterized)"),
]:
    pdf.table_row(k, v)
pdf.ln(3)

pdf.section_title("SMTP Status")
pdf.body_text(
    "Gmail SMTP (smtp.gmail.com:587) is configured but BLOCKED on Render Free tier "
    "(outbound ports 25/465/587 firewalled). Workaround: OTP bypass for admin and trusted users, "
    "with global and per-user OTP toggle from admin panel. "
    "All 12 OTP send calls use background threads (queue_otp_email) to prevent blocking."
)
pdf.ln(3)

# ==================== 5. DATABASE SCHEMA ====================
pdf.add_page()
pdf.chapter_title("5", "Database Schema (25 Models)")

models = [
    ("User", "40+ fields: credentials, profile, salary, risk appetite, budget ratios, language, photo"),
    ("Income", "source, type (Salary/Freelance/Business/Rental/Dividend), amount, frequency, date"),
    ("Expense", "category (16 types), amount, date, description, is_recurring, member"),
    ("Investment", "20+ types (FD/RD/MF/Stocks/Gold/PPF/NPS/etc), platform, current_value, returns"),
    ("Asset", "Car/Bike/House/Land/Farming/Jewelry/Electronics, purchase_price, current_value, EMI"),
    ("InsurancePolicy", "Life/Term/Health/ULIP, provider, premium, sum_assured, maturity_value"),
    ("PremiumPayment", "Tracks each insurance premium payment with date and amount"),
    ("Scheme", "Gold schemes, chit funds, bonds with installment tracking and maturity"),
    ("SIP", "Mutual fund SIPs with day-of-month, expected_return, total_invested"),
    ("Loan", "Home/Car/Personal/Education/Credit Card, EMI, interest_rate, outstanding"),
    ("BankAccount", "Savings/Current/FD/RD with balance and interest_rate"),
    ("ProvidentFund", "EPF/VPF/GPF/PPF with UAN, employee/employer contributions"),
    ("FinancialGoal", "goal_name, target_amount, current_saved, target_date, priority"),
    ("Budget", "Monthly budgets by category with limit amounts"),
    ("FamilyMember", "name, relationship, age, occupation, monthly_income"),
    ("Notification", "title, message, category, icon, link, is_read status"),
    ("GoldPriceAlert", "karat (24K/22K/18K/Silver), direction, target_price, triggered"),
    ("TrackedProduct", "E-commerce URL, platform, current_price, mrp, discount, target_price"),
    ("PriceHistory", "Price snapshots per tracked product over time"),
    ("GlobalPriceSnapshot", "Cross-user price cache by product_key & platform"),
    ("UserStreak", "expense_streak, login_streak, budget_streak + all-time bests"),
    ("UserBadge", "Achievement badges with key, name, icon, color, category"),
    ("WealthCard", "Trust score (0-1000), grade, personality, 6 dimension scores, public toggle"),
    ("PaymentTransaction", "Razorpay orders with plan_code, status, signature verification"),
    ("Feedback", "User ratings (1-5 stars), category, message"),
]

pdf.table_row("Model", "Key Fields & Purpose", header=True)
for name, desc in models:
    pdf.set_font("Helvetica", "B", 8)
    self = pdf
    col1_w = 58
    col2_w = 128
    pdf.set_fill_color(248, 246, 255)
    pdf.set_text_color(50, 50, 50)
    pdf.set_font("Helvetica", "B", 8)
    pdf.cell(col1_w, 7, name, border=1, fill=True)
    pdf.set_font("Helvetica", "", 7)
    pdf.cell(col2_w, 7, desc[:95], border=1, new_x="LMARGIN", new_y="NEXT")
pdf.ln(5)

# ==================== 6. CORE FEATURES ====================
pdf.add_page()
pdf.chapter_title("6", "Core Features (Currently Live)")

features = {
    "Financial Tracking": [
        "Income tracking - Salary, Freelance, Business, Rental, Dividends, Interest",
        "Expense tracking - 16 categories with voice input in 4 languages",
        "Budget Planner - 50/30/20 rule with customizable ratios",
        "Loan management - Home/Car/Personal/Education/Credit Card EMI tracking",
        "Bank account management - Savings, Current, FD, RD with balances",
    ],
    "Investment Portfolio": [
        "20+ investment types: FD, RD, MF, Stocks, Gold, Silver, PPF, NPS, REITs",
        "SIP Tracker - Monthly SIP with day-of-month reminders",
        "Provident Fund - EPF/VPF/GPF/PPF with contribution tracking",
        "Scheme & Bonds - Gold schemes, chit funds, government bonds",
        "Assets - Real estate, vehicles with appreciation/depreciation tracking",
    ],
    "Gold & Silver": [
        "Live IBJA gold/silver prices (24K, 22K, 18K)",
        "Global gold prices in multiple currencies",
        "ML-based gold price prediction",
        "Price alerts (above/below target)",
        "Portfolio management for physical & digital gold",
    ],
    "Insurance Management": [
        "Policy tracking - Life, Term, Health, ULIP, Endowment",
        "19 insurance provider integrations",
        "Premium payment tracking with due date reminders",
        "OCR scanning of policy documents",
        "Insurance gap analysis for individuals and families",
        "Coverage adequacy recommendations",
    ],
    "Tax & Government": [
        "ITR Guide with income tax calculator",
        "Tax planning with Section 80C/80D/80CCD deduction optimization",
        "Indian Union Budget tracker",
        "Government schemes directory (14+ schemes)",
        "Scheme eligibility calculator",
    ],
    "Planning & Goals": [
        "Financial goal setting with auto-calculation",
        "Future Planner (wealth projection to 2040+)",
        "What-If Simulator for financial scenarios",
        "Retirement corpus calculator",
        "Joint goals for couples/families",
    ],
    "AI-Powered Tools": [
        "Financial Health Score (0-100 with A+ to D grades)",
        "Budget analysis with actionable tips",
        "Investment suggestions based on age & risk",
        "Asset buying plans (car, house, land, farm)",
        "Expense trend prediction (ML)",
        "50+ business ideas (profession & state-specific)",
        "AI Playbooks for financial strategies",
        "Credit card recommendations by salary tier",
    ],
    "Family Features": [
        "Family member management",
        "Combined family dashboard",
        "Shared expense tracking",
        "Family retirement planner",
        "Collective insurance analyzer",
    ],
    "Engagement & Gamification": [
        "Daily streaks (expense, login, budget)",
        "Achievement badges for milestones",
        "WealthCard - Financial Trust Score (0-1000)",
        "Shareable verification link with QR code",
        "7 Money Personalities",
    ],
    "Reporting & Analytics": [
        "Custom date-range financial reports",
        "Portfolio performance analysis",
        "Expense trend analysis",
        "CSV/PDF/JSON export",
        "Download all data feature",
    ],
    "Calculators (15+)": [
        "EMI, SIP, Compound Interest, Retirement Corpus",
        "Home Loan, Personal Loan, RD, PPF, NPS",
        "Inflation Adjustment, Goal Planning",
        "Mutual Fund Returns, Savings Goal, Budget Planner, Income Tax",
    ],
    "Other Features": [
        "Price Tracker - E-commerce product monitoring",
        "Rate Monitor - FD/RD/PPF/EPF/NPS rates across banks",
        "Voice expense entry in 4 languages",
        "Document OCR scanning",
        "Notifications - Premium/EMI/SIP/Goal/Budget alerts",
    ],
}

for category, items in features.items():
    pdf.section_title(category)
    for item in items:
        pdf.bullet(item)
    pdf.ln(3)

# ==================== 7. AI & ML ENGINE ====================
pdf.add_page()
pdf.chapter_title("7", "AI & ML Engine")
pdf.body_text(
    "myWealthPilot includes 17 AI/ML-powered functions in app/ml_engine.py. "
    "These are rule-based and statistical models that run server-side with zero API cost."
)

ai_features = [
    ("Financial Health Score", "Scoring (0-100) based on savings, investments, debt, expense ratios"),
    ("Budget Analysis", "50/30/20 rule checking with category-wise breakdown and tips"),
    ("Investment Suggestions", "Age + risk-based allocation across 20+ instrument types"),
    ("Asset Buying Plans", "EMI capacity, budget limits (car=0.5x, house=5x annual salary)"),
    ("Expense Prediction", "Linear regression on historical expense data for next-month forecast"),
    ("Retirement Corpus", "Inflation-adjusted corpus + monthly SIP needed"),
    ("Investment Returns", "Lumpsum + SIP calculator with yearly breakdown"),
    ("Tax Saving", "Section 80C/80CCD/80D optimization with estimated tax saved"),
    ("Loan Analysis", "Interest rate vs benchmark, EMI-to-income ratio, good/bad verdict"),
    ("Credit Card Offers", "Salary-tier recommendations (SimplyCLICK to Infinia)"),
    ("Gold/Silver Analysis", "30-day/365-day/5-year trends with bullish/bearish classification"),
    ("Buy Timing Advisor", "Best months for car/bike/electronics with expected savings %"),
    ("Grocery Offers", "Platform-specific offers (BigBasket, Blinkit, Zepto, etc.)"),
    ("AI Playbooks", "Marketing, pricing, cash flow strategies by profession"),
    ("Future Readiness", "Asset allocation by risk level, projected corpus, 4 milestones"),
    ("Business Ideas", "50+ ideas by profession/state with govt scheme eligibility"),
    ("Commodity Suggestions", "SGB, Gold ETF, Silver ETF with allocation recommendations"),
]

pdf.table_row("Function", "Description", header=True)
for name, desc in ai_features:
    pdf.set_fill_color(248, 246, 255)
    pdf.set_text_color(50, 50, 50)
    pdf.set_font("Helvetica", "B", 8)
    pdf.cell(58, 7, name, border=1, fill=True)
    pdf.set_font("Helvetica", "", 7)
    pdf.cell(128, 7, desc[:90], border=1, new_x="LMARGIN", new_y="NEXT")
pdf.ln(5)

# ==================== 8. WEALTHCARD ====================
pdf.add_page()
pdf.chapter_title("8", "WealthCard - Financial Trust Score")
pdf.body_text(
    "WealthCard is myWealthPilot's signature feature - a comprehensive Financial Trust Score (0-1000) "
    "that measures overall financial health across 6 dimensions. Unlike CIBIL which only covers credit, "
    "WealthCard scores savings, investments, insurance, emergency preparedness, and financial discipline."
)

pdf.section_title("Score Dimensions (Total: 1000 points)")
for k, v in [
    ("Savings Discipline", "0-200 pts: Savings rate + month-over-month consistency"),
    ("Debt Health", "0-200 pts: Debt-to-income ratio, zero debt = full score"),
    ("Investment Maturity", "0-200 pts: Investment amount vs income + type diversity"),
    ("Insurance Coverage", "0-150 pts: Cover vs 10x income + health/term bonus"),
    ("Emergency Fund", "0-100 pts: Bank balance covering 1-12 months of expenses"),
    ("Discipline", "0-150 pts: Tracking tenure + modules used + streaks"),
]:
    pdf.table_row(k, v)
pdf.ln(3)

pdf.section_title("Grade System")
for k, v in [
    ("AAA (850-1000)", "Exceptional financial health"),
    ("AA (750-849)", "Excellent financial management"),
    ("A (650-749)", "Very good financial standing"),
    ("BBB (550-649)", "Good, room for improvement"),
    ("BB (450-549)", "Fair financial position"),
    ("B (350-449)", "Below average, needs attention"),
    ("C (200-349)", "Poor financial health"),
    ("D (0-199)", "Very poor, start tracking today"),
]:
    pdf.table_row(k, v)
pdf.ln(3)

pdf.section_title("Money Personalities (7 Types)")
for k, v in [
    ("The Saver", "Prioritizes building reserves, strong savings habit"),
    ("The Investor", "Grows wealth actively through diversified investments"),
    ("The Guardian", "Protects family with insurance & emergency funds"),
    ("The Strategist", "Balanced across all dimensions, data-driven"),
    ("The Builder", "Steady, goal-oriented, building wealth brick by brick"),
    ("The Spender", "Enjoys the present, needs savings focus"),
    ("The Explorer", "Getting started, great potential ahead"),
]:
    pdf.table_row(k, v)
pdf.ln(3)

pdf.section_title("Sharing & Verification")
pdf.body_text(
    "Users can make their WealthCard public, generating a unique verification link with QR code. "
    "Anyone can scan the QR or visit the link to see the card - no login required. "
    "The verification page shows trust score, grade, personality, and dimension bars "
    "but NEVER reveals exact financial amounts. Uses HMAC-SHA256 verification tokens."
)

# ==================== 9. SUBSCRIPTION PLANS ====================
pdf.add_page()
pdf.chapter_title("9", "Subscription Plans & Pricing")

pdf.section_title("Plan Tiers")
pdf.table3("Plan", "Price", "Key Features", header=True)
for c1, c2, c3 in [
    ("Starter (Free)", "Rs.0/month", "Dashboard, Income, Expenses, Budget, Loans"),
    ("", "", "Investments, Goals, Calculators, Achievements"),
    ("", "", "WealthCard, Gold/Silver, What-If Simulator"),
    ("Pro Monthly", "Rs.99/month", "Everything in Starter +"),
    ("", "", "Insurance, Schemes, SIPs, Assets, Tax Planning"),
    ("", "", "ITR Guide, AI Suggestions, AI Playbooks"),
    ("", "", "Reports, Rate Monitor, Business Ideas"),
    ("Family Monthly", "Rs.199/month", "Everything in Pro +"),
    ("", "", "Future Planner 2040+, Govt Schemes"),
    ("", "", "Family Members, Family Dashboard"),
    ("", "", "Joint Goals, Shared Expenses"),
]:
    pdf.table3(c1, c2, c3)
pdf.ln(3)

pdf.section_title("Payment Integration")
pdf.body_text(
    "Razorpay payment gateway handles INR transactions via UPI, credit/debit cards, "
    "wallets, and net banking. Server-side webhook verification ensures tamper-proof "
    "payment confirmation. Billing history available in user profile."
)

# ==================== 10. PWA ====================
pdf.chapter_title("10", "PWA & Offline Capabilities")
for k, v in [
    ("Service Worker", "Caches static assets for offline access"),
    ("Web Manifest", "Installable as native app (Add to Home Screen)"),
    ("Offline Dashboard", "Cached dashboard viewable without internet"),
    ("IndexedDB", "Local data storage for offline sync"),
    ("Background Sync", "Pending transactions synced on reconnect"),
    ("Theme", "Customizable light/dark mode"),
    ("Responsive", "Full mobile/tablet/desktop support"),
]:
    pdf.table_row(k, v)
pdf.ln(5)

# ==================== 11. I18N ====================
pdf.chapter_title("11", "Internationalization (i18n)")
pdf.body_text(
    "myWealthPilot supports 4 Indian languages with 850+ translation keys. "
    "Users can switch language from profile settings. Voice input also supports all 4 languages."
)
for k, v in [
    ("English (en)", "Default language"),
    ("Tamil (ta)", "Full translation + voice commands"),
    ("Hindi (hi)", "Full translation + voice commands"),
    ("Telugu (te)", "Full translation + voice commands"),
    ("Voice Speech API", "en-IN, ta-IN, hi-IN, te-IN locales"),
    ("Category Keywords", "Multi-language voice recognition per category"),
]:
    pdf.table_row(k, v)
pdf.ln(5)

# ==================== 12. ADMIN PANEL ====================
pdf.add_page()
pdf.chapter_title("12", "Admin Panel")
pdf.body_text("Accessible at /admin (admin users only). Provides full user and system management.")
for k, v in [
    ("User Management", "View all users, toggle active/verified status, delete users"),
    ("Password Reset", "Reset any user's password via modal (no OTP needed)"),
    ("OTP Toggle (Global)", "Enable/disable email OTP verification for all users"),
    ("OTP Toggle (Per-User)", "Skip OTP for specific trusted users"),
    ("DB Info Display", "Shows current DB host, name, provider (Neon/Render badge)"),
    ("Email Test", "Test SMTP configuration"),
    ("DB Migration", "One-click migration tool (Render -> Neon)"),
    ("Server Info", "App port, mail server, environment details"),
]:
    pdf.table_row(k, v)
pdf.ln(5)

# ==================== 13. ARCHITECTURE ====================
pdf.chapter_title("13", "Architecture Flow")
pdf.set_font("Courier", "", 9)
pdf.set_text_color(60, 60, 60)
lines = [
    "  User Browser / PWA (Mobile + Desktop)",
    "       |",
    "       v",
    "  mywealthpilot.in  (Custom Domain, HTTPS/TLS 1.3)",
    "       |",
    "       v",
    "  Render.com  (Gunicorn 2 workers, Flask 3.0, 512MB RAM)",
    "       |            |            |",
    "       v            v            v",
    "   Flask-Login    Flask-WTF    Flask-Limiter",
    "   (Sessions)     (CSRF)      (Rate Limit)",
    "       |",
    "       v",
    "  SQLAlchemy ORM (25 Models)",
    "       |",
    "       v",
    "  Neon.tech PostgreSQL 17 (0.5GB, SSL, US East 1)",
    "",
    "  External Services:",
    "  [cron-job.org] --ping--> /login (every 14 min)",
    "  [GitHub main]  --push--> Render auto-deploy",
    "  [Razorpay]     <-webhook-> /billing/webhook",
    "  [IBJA/MCX]     --> Gold/Silver live prices",
    "  [goqr.me]      --> QR code generation",
]
for line in lines:
    pdf.cell(0, 5, line, new_x="LMARGIN", new_y="NEXT")
pdf.ln(5)

# ==================== 14. LIMITATIONS ====================
pdf.add_page()
pdf.chapter_title("14", "Current Limitations")
for k, v in [
    ("RAM", "512 MB hard limit (OOM = SIGKILL)"),
    ("Workers", "2 sync workers = 2 concurrent requests max"),
    ("SMTP", "Blocked on Render Free (ports 25/465/587)"),
    ("Cold Start", "30-50 sec after idle sleep"),
    ("DB Storage", "0.5 GB Neon free tier"),
    ("No Load Balancer", "Single instance, no horizontal scaling"),
    ("No CDN", "Static assets served directly from app"),
    ("No Real-time", "No WebSocket support, polling only"),
    ("No UPI Sync", "No API available from GPay/PhonePe/Paytm"),
    ("No SMS Reading", "Web app cannot read device SMS"),
]:
    pdf.table_row(k, v)
pdf.ln(5)

# ==================== 15. FUTURE: SMART STATEMENT IMPORT ====================
pdf.add_page()
pdf.chapter_title("15", "FUTURE: Smart Statement Import")
pdf.body_text(
    "Auto-import expenses and income from bank/UPI statement files. "
    "Since no UPI app provides a public API, the solution is user-uploaded statement parsing."
)

pdf.section_title("Problem Statement")
pdf.body_text(
    "Users currently add expenses manually. No Indian UPI app (GPay, PhonePe, Paytm) "
    "offers a public API for third-party transaction access. SMS parsing requires a native mobile app. "
    "Account Aggregator (RBI-licensed) costs lakhs and requires NBFC registration."
)

pdf.section_title("Solution: Statement File Upload + AI Categorization")
pdf.body_text("User uploads bank statement or UPI export -> auto-parse -> auto-categorize -> review -> import.")

pdf.section_title("End-to-End Flow")
steps = [
    "Step 1: User clicks 'Import Statement' on Expenses page",
    "Step 2: Uploads PDF/CSV from bank app or UPI app",
    "   - GPay: Settings > Download statement (PDF)",
    "   - PhonePe: Transaction History > Download (PDF)",
    "   - Bank apps: Download statement (PDF/CSV/XLS)",
    "   - Net banking: Download account statement",
    "Step 3: Backend parses the file using pdfplumber (PDF) or csv module (CSV)",
    "   - Extracts: date, description, debit/credit, amount, balance",
    "   - Handles 10+ Indian bank formats (SBI, HDFC, ICICI, Axis, Kotak, etc.)",
    "Step 4: AI auto-categorizes each transaction",
    "   - Keyword matching: 'Swiggy' -> Food, 'Uber' -> Transport, 'Amazon' -> Shopping",
    "   - UPI ID parsing: 'paytm' -> identify merchant",
    "   - Amount-based: Large debits -> check if matches known EMI/premium",
    "   - Unknown -> 'Miscellaneous' (user can recategorize)",
    "Step 5: Preview page shows parsed transactions in a table",
    "   - User can edit category, description, toggle include/exclude",
    "   - Duplicate detection: skip if same date+amount already exists",
    "   - Credit entries -> auto-tag as Income",
    "   - Debit entries -> auto-tag as Expense",
    "Step 6: User clicks 'Import Selected' -> bulk insert into Expense/Income tables",
    "Step 7: Flash success message with count of imported transactions",
]
for step in steps:
    pdf.bullet(step)
pdf.ln(3)

pdf.section_title("Supported Bank Formats")
for k, v in [
    ("SBI", "PDF with table layout, date/narration/debit/credit/balance"),
    ("HDFC", "PDF/CSV, date/narration/chq/value/debit/credit/balance"),
    ("ICICI", "PDF/CSV, S.No/date/mode/particulars/deposits/withdrawals"),
    ("Axis", "PDF, date/description/debit/credit/balance"),
    ("Kotak", "PDF/CSV, date/description/debit/credit/balance"),
    ("GPay Export", "PDF, date/to-from/amount/status/UPI ref"),
    ("PhonePe Export", "PDF, date/description/amount/status"),
    ("Generic CSV", "Auto-detect columns: date, amount, description"),
]:
    pdf.table_row(k, v)
pdf.ln(3)

pdf.section_title("Technical Implementation")
for k, v in [
    ("File Parsing", "pdfplumber (PDF), csv module (CSV) - already in requirements"),
    ("Category Engine", "Keyword dict with 200+ merchant-to-category mappings"),
    ("Duplicate Check", "Hash of date+amount+description against existing entries"),
    ("Bulk Insert", "SQLAlchemy bulk_save_objects for performance"),
    ("File Size Limit", "Max 5 MB per upload"),
    ("Privacy", "File processed in memory, never stored on server"),
    ("Security", "CSRF token, login required, user_id scoping"),
]:
    pdf.table_row(k, v)
pdf.ln(3)

pdf.section_title("UX Flow")
pdf.body_text(
    "1. Expenses page -> 'Import Statement' button (next to 'Add Expense')\n"
    "2. Modal: drag-and-drop or file picker (PDF/CSV)\n"
    "3. Preview table with auto-categorized transactions\n"
    "4. Edit categories inline, toggle rows, select date range\n"
    "5. 'Import Selected' -> bulk save -> redirect to expenses with success flash"
)

# ==================== 16. FUTURE: PASSKEY AUTH ====================
pdf.add_page()
pdf.chapter_title("16", "FUTURE: Passkey Authentication (WebAuthn)")
pdf.body_text(
    "Replace email OTP with biometric authentication (fingerprint/face unlock). "
    "Solves the SMTP blocked problem permanently. Works on all modern browsers."
)

pdf.section_title("Problem")
pdf.body_text(
    "Render Free blocks SMTP ports -> OTP emails cannot be sent -> "
    "current workaround is OTP bypass for trusted users. "
    "Passkeys eliminate the need for OTP entirely."
)

pdf.section_title("Solution: WebAuthn / FIDO2 Passkeys")
steps = [
    "User registers a passkey (fingerprint/face/PIN) from Profile page",
    "Next login: 'Sign in with Passkey' button triggers biometric prompt",
    "Browser handles authentication locally (no network call needed)",
    "Server verifies the cryptographic signature",
    "No password, no OTP, no email required",
    "Works offline (biometric is local)",
    "Supported: Chrome, Safari, Firefox, Edge (all platforms)",
]
for step in steps:
    pdf.bullet(step)
pdf.ln(3)

pdf.section_title("Technical Implementation")
for k, v in [
    ("Library", "py_webauthn (Python WebAuthn server)"),
    ("Registration", "POST /auth/passkey/register -> challenge + credential"),
    ("Authentication", "POST /auth/passkey/login -> verify signature"),
    ("Storage", "New model: UserPasskey (credential_id, public_key, counter)"),
    ("Fallback", "Password login still available"),
    ("Cost", "$0 (no API keys, no SMTP needed)"),
]:
    pdf.table_row(k, v)
pdf.ln(5)

# ==================== 17. FUTURE ROADMAP ====================
pdf.add_page()
pdf.chapter_title("17", "FUTURE: Advanced Roadmap")

roadmap = [
    ("Smart Statement Import", "Auto-parse bank/UPI PDFs into expenses/income", "High", "Ready to build"),
    ("Passkey Authentication", "WebAuthn biometric login (replaces OTP)", "High", "Ready to build"),
    ("End-to-End Encryption", "Encrypt financial data with user's key", "Medium", "Research phase"),
    ("Zero-Knowledge Proofs", "Prove 'score > 700' without revealing score", "Low", "Future concept"),
    ("Native Mobile App", "React Native or Flutter wrapper for PWA", "Medium", "Post-scale"),
    ("SMS Parsing (Mobile)", "Read bank SMS for auto-expense (native only)", "Medium", "Needs mobile app"),
    ("Account Aggregator", "RBI-licensed direct bank data access", "Low", "Requires NBFC license"),
    ("Multi-Currency", "Support USD, GBP, EUR for NRI users", "Medium", "Schema change needed"),
    ("AI Chatbot", "Natural language financial queries", "Medium", "Needs AI API"),
    ("Social Features", "Compare anonymized scores with friends", "Low", "Privacy concerns"),
    ("WhatsApp Bot", "Expense entry via WhatsApp messages", "Medium", "Needs Meta API"),
    ("Scheduled Reports", "Weekly/monthly email summaries", "Low", "Needs working SMTP"),
    ("CDN Integration", "Cloudflare for static assets", "Low", "Performance boost"),
    ("Redis Cache", "Session + query caching", "Medium", "Needs paid tier"),
    ("WebSocket", "Real-time notifications", "Low", "Needs paid tier"),
]

pdf.set_font("Helvetica", "B", 9)
pdf.set_fill_color(108, 92, 231)
pdf.set_text_color(255, 255, 255)
pdf.cell(55, 7, "Feature", border=1, fill=True)
pdf.cell(65, 7, "Description", border=1, fill=True)
pdf.cell(22, 7, "Priority", border=1, fill=True)
pdf.cell(44, 7, "Status", border=1, fill=True, new_x="LMARGIN", new_y="NEXT")

for name, desc, priority, status in roadmap:
    pdf.set_fill_color(248, 246, 255)
    pdf.set_text_color(50, 50, 50)
    pdf.set_font("Helvetica", "B", 8)
    pdf.cell(55, 7, name, border=1, fill=True)
    pdf.set_font("Helvetica", "", 7)
    pdf.cell(65, 7, desc[:45], border=1)
    # Priority color
    if priority == "High":
        pdf.set_text_color(220, 50, 50)
    elif priority == "Medium":
        pdf.set_text_color(200, 150, 0)
    else:
        pdf.set_text_color(100, 100, 100)
    pdf.set_font("Helvetica", "B", 8)
    pdf.cell(22, 7, priority, border=1, align="C")
    pdf.set_text_color(50, 50, 50)
    pdf.set_font("Helvetica", "", 7)
    pdf.cell(44, 7, status, border=1, new_x="LMARGIN", new_y="NEXT")
pdf.ln(5)

# ==================== 18. APPENDIX: API ROUTES ====================
pdf.add_page()
pdf.chapter_title("18", "Appendix: Key API Routes")
pdf.body_text("Selected important routes from 151+ total endpoints:")

routes = [
    ("/", "GET", "Landing / login page"),
    ("/login", "GET/POST", "User login with OTP"),
    ("/register", "GET/POST", "User registration"),
    ("/dashboard", "GET", "Main financial dashboard"),
    ("/income", "GET", "Income tracking page"),
    ("/income/add", "POST", "Add income entry"),
    ("/expenses", "GET", "Expense tracking page"),
    ("/expenses/add", "POST", "Add expense"),
    ("/expenses/edit/<id>", "POST", "Edit expense"),
    ("/expenses/delete/<id>", "POST", "Delete expense"),
    ("/budget", "GET", "Budget planner"),
    ("/loans", "GET", "Loan management"),
    ("/investments", "GET", "Investment portfolio"),
    ("/policies", "GET", "Insurance policies"),
    ("/schemes", "GET", "Schemes & bonds"),
    ("/sips", "GET", "SIP tracker"),
    ("/gold-silver", "GET", "Gold & silver portfolio"),
    ("/global-gold", "GET", "Global gold prices"),
    ("/gold-prediction", "GET", "ML gold prediction"),
    ("/assets", "GET", "Asset management"),
    ("/goals", "GET", "Financial goals"),
    ("/bank-accounts", "GET", "Bank accounts"),
    ("/provident-fund", "GET", "PF tracking"),
    ("/tax-planning", "GET", "Tax planning tools"),
    ("/itr-guide", "GET", "ITR filing guide"),
    ("/calculators", "GET", "15+ calculators"),
    ("/suggestions", "GET", "AI suggestions"),
    ("/ai-playbooks", "GET", "AI business playbooks"),
    ("/future-planner", "GET", "Future wealth planner"),
    ("/business-ideas", "GET", "50+ business ideas"),
    ("/reports", "GET", "Financial reports"),
    ("/rate-monitor", "GET", "Rate monitor"),
    ("/govt-schemes", "GET", "Government schemes"),
    ("/indian-budget", "GET", "Indian budget tracker"),
    ("/achievements", "GET", "Badges & streaks"),
    ("/wealthcard", "GET", "Financial trust score card"),
    ("/wealthcard/calculate", "POST", "Calculate trust score"),
    ("/wealthcard/verify/<t>", "GET", "Public verification (no login)"),
    ("/what-if-simulator", "GET", "What-if scenarios"),
    ("/price-tracker", "GET", "Product price tracker"),
    ("/notifications", "GET", "Notification center"),
    ("/notifications/count", "GET", "Unread count (JSON)"),
    ("/profile", "GET/POST", "User profile"),
    ("/admin", "GET", "Admin panel"),
    ("/admin/reset-password/<id>", "POST", "Admin password reset"),
    ("/admin/toggle-otp", "POST", "Toggle global OTP"),
    ("/billing/create-order", "POST", "Razorpay order"),
    ("/billing/webhook", "POST", "Razorpay webhook"),
    ("/health", "GET", "Health check endpoint"),
]

pdf.set_font("Helvetica", "B", 9)
pdf.set_fill_color(108, 92, 231)
pdf.set_text_color(255, 255, 255)
pdf.cell(62, 7, "Route", border=1, fill=True)
pdf.cell(28, 7, "Method", border=1, fill=True)
pdf.cell(96, 7, "Purpose", border=1, fill=True, new_x="LMARGIN", new_y="NEXT")

for route, method, purpose in routes:
    pdf.set_fill_color(248, 246, 255)
    pdf.set_text_color(50, 50, 50)
    pdf.set_font("Courier", "", 7)
    pdf.cell(62, 6, route, border=1, fill=True)
    pdf.set_font("Helvetica", "", 7)
    pdf.cell(28, 6, method, border=1)
    pdf.cell(96, 6, purpose, border=1, new_x="LMARGIN", new_y="NEXT")

pdf.ln(8)
pdf.set_font("Helvetica", "I", 9)
pdf.set_text_color(140, 140, 140)
pdf.cell(0, 6, "End of Document - myWealthPilot Technical Documentation v2.0", align="C")
pdf.cell(0, 6, "", new_x="LMARGIN", new_y="NEXT")
pdf.cell(0, 6, f"Generated: {datetime.now().strftime('%d %B %Y, %I:%M %p')}", align="C")

out_path = r"D:\vinoth\money_manager\docs\myWealthPilot_Technical_Documentation.pdf"
pdf.output(out_path)
print(f"PDF saved: {out_path}")
