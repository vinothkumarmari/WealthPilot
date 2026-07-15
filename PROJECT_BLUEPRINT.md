# MyWealthPilot — Project Blueprint v1.1.0

**Date:** May 29, 2026  
**Version:** 1.1.0 (Build 4)  
**Domain:** https://mywealthpilot.in  
**Play Store Package:** in.mywealthpilot.twa  
**GitHub:** https://github.com/vinothkumarmari/WealthPilot

---

## 1. Infrastructure

| Layer | Service | Plan | Details |
|-------|---------|------|---------|
| **Web Hosting** | Render | Free | Auto-deploys from GitHub `main` branch |
| **Database** | Supabase PostgreSQL | Free | 500MB storage, unlimited compute, transaction pooler mode |
| **Domain** | mywealthpilot.in | Custom | DNS pointing to Render |
| **SSL/TLS** | Render (auto) | Free | HTTPS via Let's Encrypt, auto-renewal |
| **Android App** | Google Play Store (TWA) | $25 one-time | Trusted Web Activity wrapping the website |
| **Source Control** | GitHub | Free | Private repo, auto-deploy on push to `main` |
| **CDN Assets** | jsDelivr, Google Fonts | Free | Bootstrap 5.3, jQuery, Chart.js, DataTables, DM Sans |
| **Icons** | Google Material Icons | Free | Material Icons Outlined |

### Infrastructure Diagram

```
┌──────────────────┐     ┌──────────────────┐     ┌──────────────────┐
│   Android App    │     │   Web Browser     │     │   PWA (iOS)      │
│  (Play Store)    │     │   (Desktop)       │     │   (Add to Home)  │
│  TWA Wrapper     │     │                   │     │                   │
└───────┬──────────┘     └───────┬───────────┘     └───────┬───────────┘
        │                        │                          │
        └────────────────────────┼──────────────────────────┘
                                 │ HTTPS
                    ┌────────────▼────────────┐
                    │    Render Web Service   │
                    │    (Flask 3.0 / Gunicorn)│
                    │    Python 3.12.7        │
                    └────────────┬────────────┘
                                 │ PostgreSQL
                    ┌────────────▼────────────┐
                    │   Supabase PostgreSQL   │
                    │   (ap-southeast-2)      │
                    │   Transaction Pooler    │
                    └─────────────────────────┘
```

### Current Limitations (Free Tier)
- Render free tier sleeps after 15 min inactivity (cold start ~30 seconds)
- Supabase free tier: 500MB database, 1GB file storage
- No Redis configured (rate limiter uses in-memory storage)
- No email service configured (password reset, alert emails not sent)

### Recommended Upgrades for Scale
| Upgrade | Cost | Benefit |
|---------|------|---------|
| Render Starter | $7/mo | No sleep, faster deploys, persistent disk |
| UptimeRobot | Free | Keep Render awake with ping every 5 min |
| Resend / SendGrid | Free tier | Email notifications, password reset |
| Redis (Render) | $0-7/mo | Persistent rate limiter, session store |
| Supabase Pro | $25/mo | 8GB DB, daily backups, analytics |
| Custom domain email | ~$1/mo | noreply@mywealthpilot.in |

---

## 2. Technology Stack

| Component | Technology | Version |
|-----------|-----------|---------|
| **Backend Framework** | Flask | 3.0 |
| **Language** | Python | 3.12.7 |
| **ORM** | SQLAlchemy + Flask-SQLAlchemy | Latest |
| **Database** | PostgreSQL | 15 (Supabase) |
| **Migrations** | Flask-Migrate (Alembic) | Latest |
| **Auth** | Flask-Login | Latest |
| **CSRF** | Flask-WTF | Latest |
| **Rate Limiting** | Flask-Limiter | Latest |
| **WSGI Server** | Gunicorn | Latest |
| **Frontend** | Bootstrap 5.3.2 | CDN |
| **Charts** | Chart.js 4.4.1 | CDN |
| **Data Tables** | DataTables 1.13.7 | CDN |
| **Font** | DM Sans (mobile) / Inter (desktop) | Google Fonts |
| **Icons** | Material Icons Outlined | Google Fonts |
| **Android** | Bubblewrap TWA | 1.24.1 |
| **MFA** | TOTP + WebAuthn (py_webauthn) | Latest |

---

## 3. Project Structure

```
money_manager/
├── app/
│   ├── __init__.py              # App factory, Jinja filters, extensions
│   ├── models.py                # 26 SQLAlchemy models (~420 lines)
│   ├── routes.py                # 174 routes (~6,526 lines)
│   ├── translations.py          # 4-language translations (~1,005 lines)
│   ├── templates/               # 76 HTML templates
│   │   ├── base.html            # Master layout (sidebar, topbar, footer)
│   │   ├── dashboard.html       # Main dashboard
│   │   ├── landing.html         # Public landing page
│   │   ├── login.html           # Authentication
│   │   ├── register.html        # Registration
│   │   ├── help_guide.html      # Help documentation
│   │   └── ... (71 more)
│   └── static/
│       ├── css/style.css        # Responsive CSS (~900 lines)
│       ├── js/app.js            # Core JS (sidebar, theme, tooltips)
│       ├── js/offline.js        # Service worker offline support
│       ├── manifest.json        # PWA manifest
│       ├── sw.js                # Service worker
│       ├── favicon.svg          # App icon
│       └── icons/               # PWA icons (192x192, 512x512)
├── android/
│   ├── mywealthpilot.keystore   # Android signing key
│   ├── release/                 # Signed AAB/APK files
│   │   ├── MyWealthPilot-v1.0.0.aab
│   │   └── MyWealthPilot-v1.1.0.aab
│   └── twa/                     # Bubblewrap TWA project
│       ├── twa-manifest.json    # TWA configuration
│       ├── app/build.gradle     # Android build config
│       ├── gradlew.bat          # Gradle wrapper
│       └── ...
├── migrations/                  # Alembic migration scripts
├── requirements.txt             # Python dependencies
├── render.yaml                  # Render deployment config
├── Procfile                     # Gunicorn process file
└── .env                         # Environment variables (not in git)
```

---

## 4. Database Models (29 Tables)

| # | Model | Purpose |
|---|-------|---------|
| 1 | **User** | User accounts, profile, subscription, MFA settings |
| 2 | **Income** | Monthly income / salary records |
| 3 | **Expense** | Daily expense tracking with categories |
| 4 | **Budget** | Monthly budget allocations per category |
| 5 | **Loan** | Active loans (home, car, personal, education) |
| 6 | **Investment** | Stock, mutual fund, FD, RD investments |
| 7 | **InsurancePolicy** | Life, health, vehicle insurance policies |
| 8 | **Scheme** | Gold schemes, chit funds, bonds, recurring deposits |
| 9 | **SIP** | Systematic Investment Plans tracker |
| 10 | **Asset** | Physical and digital assets (property, vehicles) |
| 11 | **FinancialGoal** | Savings goals with target amounts |
| 12 | **BankAccount** | Bank account balances and statements |
| 13 | **ProvidentFund** | EPF / PPF / NPS tracking |
| 14 | **FamilyMember** | Family member profiles for shared planning |
| 15 | **Notification** | In-app notification system |
| 16 | **Feedback** | User feedback and suggestions |
| 17 | **GoldPriceAlert** | Gold/silver price alert thresholds |
| 18 | **TrackedProduct** | E-commerce product price tracking |
| 19 | **PriceHistory** | Historical price data for tracked products |
| 20 | **GlobalPriceSnapshot** | Global gold/silver price snapshots |
| 21 | **PremiumPayment** | Insurance premium payment records |
| 22 | **PaymentTransaction** | Subscription payment transactions |
| 23 | **UserStreak** | Daily login streak tracking |
| 24 | **UserBadge** | Achievement badges earned by users |
| 25 | **WealthCard** | Financial trust score (0-1000) |
| 26 | **CrisisAlert** | Admin-published financial crisis advisories |
| 27 | **FarmerProfile** | Farmer profile details including land, soil, irrigation types, crop, and capital availability |
| 28 | **FarmerSeasonPlan** | Seasonal crop sowing plans with detailed cost-breakdown budgets and expected yields |
| 29 | **FarmerLog** | Operational farm ledger logging daily agricultural expenditures, cash inflows, and volumes |

---

## 5. Feature Modules (45+ Features)

### 5.1 Finance (Free)
| Feature | Route | Description |
|---------|-------|-------------|
| Dashboard | `/dashboard` | Financial overview with charts and health score |
| Income & Salary | `/income` | Track monthly income sources |
| Expenses | `/expenses` | Daily expense tracking with categories |
| Bank Statement | `/bank-statement` | CSV/PDF import with auto-categorization |
| Budget Planner | `/budget` | Monthly budget vs actual spending |
| Loans | `/loans` | Loan tracking with EMI schedules |

### 5.2 Investments (Mixed Access)
| Feature | Route | Access | Description |
|---------|-------|--------|-------------|
| Investments | `/investments` | Free | Stock, MF, FD, RD portfolio |
| Policies | `/policies` | Pro | Insurance policy management |
| Schemes & Bonds | `/schemes` | Pro | Gold schemes, chit funds, bonds |
| SIP Tracker | `/sips` | Pro | SIP tracking with returns |
| Gold & Silver | `/gold-silver` | Free | Live gold/silver prices (India) |
| Global Gold | `/global-gold-prices` | Free | International gold prices |
| Gold Prediction | `/gold-prediction` | Pro | AI-based gold price forecast |
| Assets | `/assets` | Pro | Physical asset management |
| Goals | `/goals` | Free | Financial goal tracking |

### 5.3 Tools & Info (Mixed Access)
| Feature | Route | Access | Description |
|---------|-------|--------|-------------|
| Tax Planning | `/tax-planning` | Pro | Section 80C/80D deduction planner |
| ITR Guide | `/itr-guide` | Pro | Income tax return filing guide |
| Calculators | `/calculators` | Free | SIP, EMI, FD, compound interest |
| Price Tracker | `/price-tracker` | Free | E-commerce product price tracking |
| AI Suggestions | `/suggestions` | Pro | Personalized financial advice |
| AI Playbooks | `/ai-playbooks` | Pro | Step-by-step financial strategies |
| Future Planner | `/future-planner` | Pro | Long-term wealth projection |
| Business Ideas | `/business-ideas` | Pro | AI-generated business ideas |
| Reports | `/reports` | Pro | Financial reports and analytics |
| Rate Monitor | `/rate-monitor` | Pro | FD/RD/savings interest rate tracker |
| Govt Schemes | `/govt-schemes` | Pro | Central & state government schemes |
| Indian Budget | `/indian-budget` | Free | Union budget highlights |
| Achievements | `/achievements` | Free | Gamification badges and streaks |
| WealthCard | `/wealthcard` | Free | Financial trust score card |
| What-If Simulator | `/what-if-simulator` | Free | Financial scenario analysis |

### 5.4 Planning (New in v1.1.0)
| Feature | Route | Access | Description |
|---------|-------|--------|-------------|
| Net Worth | `/net-worth` | Free | Asset vs liability dashboard |
| Emergency Fund | `/emergency-fund` | Free | 6-month expense coverage tracker |
| Education Fund | `/education-fund` | Pro | Inflation-adjusted education cost planner |
| Debt Planner | `/debt-planner` | Pro | Snowball/avalanche debt payoff strategies |
| Budget Splitter | `/budget-splitter` | Pro | 50/30/20 rule income allocation |
| Expense Forecast | `/expense-forecast` | Pro | 6-month trend with linear regression forecast |
| Crisis Alerts | `/crisis-alerts` | Free | Admin-published financial crisis advisories |

### 5.5 Family (Family Plan)
| Feature | Route | Description |
|---------|-------|-------------|
| Family Members | `/family-members` | Add/manage family member profiles |
| Family Dashboard | `/family-dashboard` | Combined family financial view |
| Joint Goals | `/joint-goals` | Shared savings goals |
| Shared Expenses | `/shared-expenses` | Split expenses among family |
| Member Investments | `/member-investments` | Per-member investment tracking |
| Retirement Planner | `/retirement-planner` | Retirement corpus calculator |
| Insurance Analyzer | `/insurance-analyzer` | Coverage adequacy analysis |
| Custom Reports | `/custom-reports` | Custom financial reports |
| Priority Support | `/priority-support` | Priority support channel |

### 5.6 Farmer (Farmer Smart Plan)
| Feature | Route | Description |
|---------|-------|-------------|
| Farmer Profile | `/farmer-package` | Manage cultivation location, acreage, primary crops, soil types, water supply profiles, and startup capital |
| Season Crop Sowing & Budgets | `/farmer-package` | Seed, fertilizer, pesticide, water, labor, machinery, and logistics costing budget with revenue projections |
| Crop Economics & Break-Even | `/farmer-package` | Automated break-even points on unit pricing and crop yields, with risk warnings for negative projections |
| Daily Farm Log Ledger | `/farmer-package` | Agricultural ledger to audit logging daily farm expenditures and cash inflows with weights/units |
| wttr.in Climate Advisory | `/farmer-package` | Climate-sensitive recommendations on fungicide drift windows, heat-stress irrigation, and rain safety |
| Farmers AI Assistant | `/farmer-package` | Intelligent domain conversational assistant answering loan limits, irrigation frequencies, and soil care |

### 5.7 Retail Business POS & Billing (Retail Smart Plan)
| Feature | Route | Description |
|---------|-------|-------------|
| Outlet Store Registry | `/retail-billing` | Register multi-branch retail outlets and shopping mall chains with separate GSTIN, revenue metrics, and profiles |
| Product Catalog Ledger | `/retail-billing` | Track retail pricing, raw purchase costs, SKU identifiers / barcodes, reorder level alerts, and custom GST tax brackets |
| POS Billing Terminal | `/retail-billing` | Client invoice generating interface with tax (CGST + SGST) calculators and digital/cash payment settling |
| Automatic Cash Transfer | `/retail-billing` | Auto-adds successfully generated shop invoices and receipt totals directly into overall WealthPilot Income ledgers |

---

## 6. Subscription System

### Tiers
| Tier | Price | Key Features |
|------|-------|-------------|
| **Starter** | Free | Dashboard, Income, Expenses, Budget, Loans, Investments, Goals, Calculators, Net Worth, Emergency Fund, Crisis Alerts, Credit Cards |
| **Pro Monthly** | ₹99/mo | All Starter + AI tools, Tax Planning, Reports, Education Fund, Debt Planner, Budget Splitter, Expense Forecast, CAS MF Analyzer |
| **Farmer Smart Monthly** | ₹149/mo | All Starter + Farmer Profile, Crop Budgets & Break-Even calculators, Farm Ledger entries, wttr.in Climate advisory, Farmers AI Assistant |
| **Retail Smart Monthly** | ₹299/mo | All Starter + Outlet Registries, Product Stock Catalogs, POS Billing Terminal invoices, Automatic Revenue-to-Income ledgers integration |
| **Family Monthly** | ₹199/mo | All Pro + Farmer Smart + Succession & Wills estate planners + Family features, Custom Reports, Priority Support |

### Access Control
- `@subscription_required('pro_monthly')` decorator on pro routes
- `has_access()` template function for UI lock icons
- `MODULE_PLAN_REQUIREMENTS` dict in routes.py maps features to plans

---

## 7. Localization

| Language | Code | Coverage |
|----------|------|----------|
| English | en | 100% (default) |
| Tamil | ta | 100% |
| Hindi | hi | 100% |
| Telugu | te | 100% |

- 1,005 lines in `translations.py`
- `t()` function in templates for translation
- Language selection in user profile

---

## 8. Security

| Feature | Implementation |
|---------|---------------|
| Authentication | Flask-Login session-based |
| Password Hashing | Werkzeug (pbkdf2:sha256) |
| CSRF Protection | Flask-WTF CSRFProtect |
| Rate Limiting | Flask-Limiter (in-memory) |
| MFA (2FA) | TOTP (Google Authenticator) + WebAuthn (fingerprint/security key) |
| HTTPS | Render auto-SSL (Let's Encrypt) |
| Cookie Consent | Essential cookies only, GDPR-style banner |
| Input Validation | WTForms + SQLAlchemy parameterized queries |

---

## 9. Android App (TWA)

| Property | Value |
|----------|-------|
| Package ID | `in.mywealthpilot.twa` |
| Version Name | 1.1.0 |
| Version Code | 4 |
| Min SDK | 21 (Android 5.0) |
| Target SDK | 35 (Android 15) |
| Orientation | Portrait |
| Start URL | `/dashboard` |
| Theme Color | #6C5CE7 |
| Keystore | `android/mywealthpilot.keystore` (alias: mywealthpilot) |
| Build Tool | Bubblewrap CLI 1.24.1 |
| Digital Asset Links | `/.well-known/assetlinks.json` served from Flask |

### Build Commands
```bash
cd android/twa
bubblewrap build
# Enter keystore password when prompted
# Outputs: app-release-bundle.aab + app-release-signed.apk
```

---

## 10. Deployment Workflow

### Normal Bug Fix / Feature Update (No AAB needed)
```
1. Edit code locally
2. git add -A && git commit -m "fix: description"
3. git push origin main
4. Render auto-deploys in ~2 minutes
5. All users (web + Android) see changes immediately
```

### Android TWA Update (New AAB needed)
```
1. Edit twa-manifest.json (version, icon, theme, etc.)
2. cd android/twa && bubblewrap build
3. Enter keystore password
4. Upload app-release-bundle.aab to Play Console
5. Create new release with release notes
6. Review and rollout
```

### When You Need a New AAB
| Change Type | New AAB? |
|-------------|----------|
| Backend bug fix | No |
| New feature (routes/templates) | No |
| CSS/JS/UI changes | No |
| Translation updates | No |
| App icon or splash screen | Yes |
| TWA theme color | Yes |
| Package name or signing key | Yes |
| Target SDK bump | Yes |

---

## 11. Play Store Status

| Item | Status |
|------|--------|
| Developer Account | Active (ID: 8075499607894623235) |
| App ID | 4975403180105862969 |
| Internal Testing | Active (2 testers) |
| Production Release | Pending (ready to publish) |
| Store Listing | Needs completion |
| Content Rating | Needs questionnaire |
| Data Safety | Needs declaration |
| Privacy Policy | https://mywealthpilot.in/privacy-policy |

---

## 12. Version History

| Version | Date | Key Changes |
|---------|------|-------------|
| 1.0.0 | May 18, 2026 | Initial release — 33 features, 4 languages, TWA setup |
| 1.1.0 | May 29, 2026 | 7 planning features, crisis alerts, mobile UI overhaul, DM Sans font |
| 1.2.0 | June 24, 2026 | Farmer Smart Package release — Crop budgeting, farm logs, weather advisor, and interactive AI assistant |

---

*Generated: July 13, 2026 | MyWealthPilot™ by Vinoth Kumar*
