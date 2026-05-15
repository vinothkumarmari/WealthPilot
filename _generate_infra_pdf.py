"""Generate myWealthPilot Infrastructure Overview PDF"""
from fpdf import FPDF

class InfraPDF(FPDF):
    def header(self):
        self.set_font("Helvetica", "B", 10)
        self.set_text_color(108, 92, 231)
        self.cell(0, 8, "myWealthPilot - Infrastructure Overview", align="R")
        self.ln(4)
        self.set_draw_color(108, 92, 231)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(6)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, f"Page {self.page_no()}/{{nb}}", align="C")

    def section_title(self, num, title):
        self.set_font("Helvetica", "B", 13)
        self.set_text_color(108, 92, 231)
        self.cell(0, 10, f"{num}. {title}", new_x="LMARGIN", new_y="NEXT")
        self.ln(1)

    def table_row(self, key, value, header=False):
        self.set_font("Helvetica", "B" if header else "", 9 if not header else 10)
        col1_w = 55
        col2_w = 130
        if header:
            self.set_fill_color(108, 92, 231)
            self.set_text_color(255, 255, 255)
            self.cell(col1_w, 7, key, border=1, fill=True)
            self.cell(col2_w, 7, value, border=1, fill=True, new_x="LMARGIN", new_y="NEXT")
        else:
            self.set_fill_color(245, 243, 255)
            self.set_text_color(50, 50, 50)
            self.set_font("Helvetica", "B", 9)
            self.cell(col1_w, 7, key, border=1, fill=True)
            self.set_font("Helvetica", "", 9)
            self.cell(col2_w, 7, value, border=1, new_x="LMARGIN", new_y="NEXT")

    def table_row3(self, c1, c2, c3, header=False):
        w1, w2, w3 = 55, 65, 65
        if header:
            self.set_font("Helvetica", "B", 10)
            self.set_fill_color(108, 92, 231)
            self.set_text_color(255, 255, 255)
            self.cell(w1, 7, c1, border=1, fill=True)
            self.cell(w2, 7, c2, border=1, fill=True)
            self.cell(w3, 7, c3, border=1, fill=True, new_x="LMARGIN", new_y="NEXT")
        else:
            self.set_fill_color(245, 243, 255)
            self.set_text_color(50, 50, 50)
            self.set_font("Helvetica", "B", 9)
            self.cell(w1, 7, c1, border=1, fill=True)
            self.set_font("Helvetica", "", 9)
            self.cell(w2, 7, c2, border=1)
            self.cell(w3, 7, c3, border=1, new_x="LMARGIN", new_y="NEXT")


pdf = InfraPDF()
pdf.alias_nb_pages()
pdf.set_auto_page_break(auto=True, margin=20)
pdf.add_page()

# Title
pdf.set_font("Helvetica", "B", 22)
pdf.set_text_color(108, 92, 231)
pdf.cell(0, 15, "myWealthPilot", align="C", new_x="LMARGIN", new_y="NEXT")
pdf.set_font("Helvetica", "", 12)
pdf.set_text_color(80, 80, 80)
pdf.cell(0, 8, "Infrastructure & Platform Overview", align="C", new_x="LMARGIN", new_y="NEXT")
pdf.set_font("Helvetica", "I", 9)
pdf.set_text_color(140, 140, 140)
pdf.cell(0, 6, "Generated: May 11, 2026  |  All services on Free Tier", align="C", new_x="LMARGIN", new_y="NEXT")
pdf.ln(8)

# 1. Web Hosting
pdf.section_title(1, "Web Hosting - Render.com")
for k, v in [
    ("Platform", "Render.com (Free Plan)"),
    ("CPU", "Shared CPU (0.1 vCPU)"),
    ("RAM", "512 MB (hard limit, SIGKILL on exceed)"),
    ("Workers", "2 Gunicorn sync workers, 120s timeout"),
    ("Bandwidth", "100 GB/month"),
    ("Auto-deploy", "Yes - on git push to main branch"),
    ("Sleep Behavior", "Spins down after 15 min idle"),
    ("Keep-Alive", "cron-job.org pings /login every 14 min"),
    ("Cold Start", "~30-50 seconds after idle sleep"),
    ("SSL", "Auto (Let's Encrypt)"),
    ("Region", "Oregon (US West)"),
    ("Health Check", "/health endpoint"),
    ("Runtime", "Python 3.12.0"),
]:
    pdf.table_row(k, v)
pdf.ln(6)

# 2. Database
pdf.section_title(2, "Database - Neon.tech PostgreSQL")
for k, v in [
    ("Platform", "Neon.tech (Free Plan, no expiry)"),
    ("Engine", "PostgreSQL 17"),
    ("Storage", "0.5 GB limit (~34 MB used, 6.77%)"),
    ("Tables", "24 tables"),
    ("Records", "61+ rows"),
    ("Compute", "Autoscaling up to 2 Compute Units"),
    ("Scale-to-Zero", "Yes - scales down when idle"),
    ("Branches", "Up to 10 per project"),
    ("Region", "US East 1 (N. Virginia, AWS)"),
    ("Connection", "SSL required (sslmode=require)"),
    ("Previous DB", "Render PostgreSQL (migrated, expires May 12, 2026)"),
]:
    pdf.table_row(k, v)
pdf.ln(6)

# 3. Domain
pdf.section_title(3, "Domain & DNS")
for k, v in [
    ("Domain", "mywealthpilot.in"),
    ("Render Subdomain", "wealthpilot-wcm7.onrender.com"),
    ("SSL Certificate", "Auto-managed by Render (Let's Encrypt)"),
    ("DNS Target", "Render Web Service"),
    ("Cost", "~Rs.500-800/year (domain renewal only)"),
]:
    pdf.table_row(k, v)
pdf.ln(6)

# 4. Source Code & CI/CD
pdf.section_title(4, "Source Code & CI/CD")
for k, v in [
    ("Repository", "GitHub - vinothkumarmari/WealthPilot"),
    ("Plan", "GitHub Free"),
    ("Branch", "main (auto-deploys to Render)"),
    ("Build Command", "pip install -r requirements.txt && flask db upgrade"),
    ("Start Command", "gunicorn run:application --bind 0.0.0.0:$PORT --workers 2 --timeout 120"),
]:
    pdf.table_row(k, v)
pdf.ln(6)

# 5. Email (SMTP)
pdf.section_title(5, "Email / SMTP")
for k, v in [
    ("Provider", "Gmail SMTP (smtp.gmail.com:587)"),
    ("Status", "BLOCKED - Render Free blocks outbound ports 25/465/587"),
    ("Workaround", "Admin & trusted users skip OTP verification"),
    ("OTP Toggle", "Global enable/disable + per-user skip from admin panel"),
]:
    pdf.table_row(k, v)
pdf.ln(6)

# 6. Payments
pdf.section_title(6, "Payment Gateway")
for k, v in [
    ("Provider", "Razorpay"),
    ("Plan", "Standard (pay-per-transaction)"),
    ("Integration", "Server-side webhook verification"),
]:
    pdf.table_row(k, v)
pdf.ln(6)

# 7. Application Stack
pdf.section_title(7, "Application Stack")
pdf.table_row("Component", "Technology", header=True)
for k, v in [
    ("Backend", "Flask 3.0, Python 3.12"),
    ("ORM", "SQLAlchemy + Flask-Migrate (Alembic)"),
    ("Authentication", "Flask-Login + OTP (SHA-256 hashed)"),
    ("Rate Limiting", "Flask-Limiter"),
    ("CSRF Protection", "Flask-WTF"),
    ("Frontend CSS", "Bootstrap 5.3.2"),
    ("Charts", "Chart.js 4.4.1"),
    ("Icons", "Material Icons Outlined"),
    ("Fonts", "Google Fonts - Inter"),
    ("Theme Color", "#6C5CE7 (purple gradient)"),
    ("PWA", "Service Worker + manifest.json"),
    ("Voice Input", "Web Speech API (free, no API key)"),
    ("Offline Storage", "IndexedDB for local data sync"),
    ("Languages", "4 - English, Tamil, Hindi, Telugu (850+ keys)"),
    ("PDF Processing", "pdfplumber + Pillow"),
    ("Dependencies", "17 Python packages"),
]:
    pdf.table_row(k, v)
pdf.ln(6)

# 8. Limits & Constraints
pdf.section_title(8, "Limits & Constraints")
pdf.table_row("Resource", "Limit", header=True)
for k, v in [
    ("RAM", "512 MB (hard limit)"),
    ("DB Storage", "0.5 GB (Neon free tier)"),
    ("Cold Start", "~30-50 sec after idle"),
    ("SMTP", "Blocked (all outbound mail ports)"),
    ("Concurrent Requests", "2 (sync workers)"),
    ("Load Balancer", "None (single instance)"),
    ("CPU Cores", "Shared (no dedicated cores)"),
    ("Horizontal Scaling", "Not available on Free tier"),
    ("CDN", "None"),
    ("Bandwidth", "100 GB/month"),
]:
    pdf.table_row(k, v)
pdf.ln(6)

# 9. Monthly Cost Summary
pdf.section_title(9, "Monthly Cost Summary")
pdf.table_row3("Service", "Plan", "Cost", header=True)
for c1, c2, c3 in [
    ("Render Web Service", "Free", "$0"),
    ("Neon PostgreSQL", "Free", "$0"),
    ("GitHub Repository", "Free", "$0"),
    ("cron-job.org", "Free", "$0"),
    ("Gmail SMTP", "Free (blocked)", "$0"),
    ("Razorpay", "Pay-per-txn", "~2% per txn"),
    ("Domain (annual)", "mywealthpilot.in", "~Rs.500-800/yr"),
]:
    pdf.table_row3(c1, c2, c3)

pdf.ln(4)
pdf.set_font("Helvetica", "B", 11)
pdf.set_text_color(34, 139, 34)
pdf.cell(0, 8, "Total Monthly Cost:  Rs.0/month  (only domain renewal annually)", align="C", new_x="LMARGIN", new_y="NEXT")
pdf.ln(6)

# 10. Architecture Diagram (text)
pdf.section_title(10, "Architecture Flow")
pdf.set_font("Courier", "", 9)
pdf.set_text_color(60, 60, 60)
lines = [
    "  User (Browser/PWA)",
    "       |",
    "       v",
    "  mywealthpilot.in  (Custom Domain)",
    "       |",
    "       v",
    "  Render.com  (Gunicorn + Flask, 2 workers, 512MB RAM)",
    "       |",
    "       v",
    "  Neon.tech  (PostgreSQL 17, 0.5GB, US East 1)",
    "",
    "  [cron-job.org] --ping--> [Render /login]  (every 14 min)",
    "  [GitHub main]  --push--> [Render auto-deploy]",
    "  [Razorpay]     <-webhook-> [Flask /webhook]",
]
for line in lines:
    pdf.cell(0, 5, line, new_x="LMARGIN", new_y="NEXT")

pdf.ln(8)
pdf.set_font("Helvetica", "I", 8)
pdf.set_text_color(150, 150, 150)
pdf.cell(0, 5, "Document generated for internal reference - myWealthPilot Project", align="C")

out_path = r"D:\vinoth\money_manager\myWealthPilot_Infrastructure_Overview.pdf"
pdf.output(out_path)
print(f"PDF saved to: {out_path}")
