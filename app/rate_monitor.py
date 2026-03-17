"""
Rate Monitor — Central source of truth for all government scheme rates,
investment interest rates, tax slabs, and important URLs.

Update this file quarterly or when the government announces changes.
All templates and AI engine read from these values.

Last verified: Q1 2025-26 (April 2025 – March 2026)
"""

# ======================== SMALL SAVINGS SCHEME RATES (Q1 2025-26) ========================
# Source: https://www.nsiindia.gov.in/ — Rates revised quarterly by Ministry of Finance

SCHEME_RATES = {
    'PPF': {
        'rate': 7.1,
        'min_deposit': 500,
        'max_deposit': 150000,
        'tenure': '15 years',
        'tax': 'EEE (Exempt-Exempt-Exempt)',
        'url': 'https://www.nsiindia.gov.in/',
        'last_updated': 'Q1 FY2025-26',
    },
    'SSY': {
        'rate': 8.2,
        'name': 'Sukanya Samriddhi Yojana',
        'min_deposit': 250,
        'max_deposit': 150000,
        'tenure': '21 years from opening',
        'tax': 'EEE',
        'url': 'https://www.nsiindia.gov.in/',
        'last_updated': 'Q1 FY2025-26',
    },
    'SCSS': {
        'rate': 8.2,
        'name': 'Senior Citizens Savings Scheme',
        'max_deposit': 3000000,
        'tenure': '5 years',
        'tax': 'Interest taxable, 80C deduction',
        'url': 'https://www.nsiindia.gov.in/',
        'last_updated': 'Q1 FY2025-26',
    },
    'NSC': {
        'rate': 7.7,
        'name': 'National Savings Certificate',
        'tenure': '5 years',
        'tax': '80C deduction, interest taxable',
        'url': 'https://www.nsiindia.gov.in/',
        'last_updated': 'Q1 FY2025-26',
    },
    'KVP': {
        'rate': 7.5,
        'name': 'Kisan Vikas Patra',
        'tenure': '115 months (doubles)',
        'tax': 'Interest taxable',
        'url': 'https://www.nsiindia.gov.in/',
        'last_updated': 'Q1 FY2025-26',
    },
    'MIS': {
        'rate': 7.4,
        'name': 'Monthly Income Scheme',
        'max_deposit': 900000,
        'tenure': '5 years',
        'tax': 'Interest taxable',
        'url': 'https://www.nsiindia.gov.in/',
        'last_updated': 'Q1 FY2025-26',
    },
    'TD_1yr': {'rate': 6.9, 'name': 'Time Deposit 1 Year', 'last_updated': 'Q1 FY2025-26'},
    'TD_2yr': {'rate': 7.0, 'name': 'Time Deposit 2 Year', 'last_updated': 'Q1 FY2025-26'},
    'TD_3yr': {'rate': 7.1, 'name': 'Time Deposit 3 Year', 'last_updated': 'Q1 FY2025-26'},
    'TD_5yr': {'rate': 7.5, 'name': 'Time Deposit 5 Year', 'last_updated': 'Q1 FY2025-26'},
    'RD': {'rate': 6.7, 'name': 'Recurring Deposit', 'last_updated': 'Q1 FY2025-26'},
    'SGB': {
        'rate': 2.5,
        'name': 'Sovereign Gold Bond',
        'note': '2.5% annual interest + gold price appreciation',
        'tenure': '8 years (exit after 5)',
        'url': 'https://www.rbi.org.in/',
        'last_updated': 'Q1 FY2025-26',
    },
}

# ======================== PROVIDENT FUND RATES ========================

PF_RATES = {
    'EPF': {'rate': 8.25, 'name': 'Employee Provident Fund', 'last_updated': 'FY2024-25'},
    'VPF': {'rate': 8.25, 'name': 'Voluntary Provident Fund', 'last_updated': 'FY2024-25'},
    'GPF': {'rate': 7.1, 'name': 'General Provident Fund', 'last_updated': 'FY2024-25'},
}

# ======================== NPS RETURNS (HISTORICAL AVERAGE) ========================

NPS_RETURNS = {
    'Equity_E': {'range': (9, 14), 'name': 'NPS Tier I - Equity (E)', 'last_updated': '2024'},
    'Corporate_C': {'range': (8, 10), 'name': 'NPS Tier I - Corporate Bond (C)', 'last_updated': '2024'},
    'Govt_G': {'range': (7, 9), 'name': 'NPS Tier I - Govt Securities (G)', 'last_updated': '2024'},
}

# ======================== TAX SLABS — NEW REGIME (FY 2025-26) ========================

NEW_TAX_SLABS = [
    (0, 400000, 0, 'Nil'),
    (400001, 800000, 5, '₹0 - ₹20,000'),
    (800001, 1200000, 10, '₹20,000 + 10% above ₹8L'),
    (1200001, 1600000, 15, '₹60,000 + 15% above ₹12L'),
    (1600001, 2000000, 20, '₹1,20,000 + 20% above ₹16L'),
    (2000001, 2400000, 25, '₹2,00,000 + 25% above ₹20L'),
    (2400001, float('inf'), 30, '₹3,00,000 + 30% above ₹24L'),
]

# Standard deduction: ₹75,000 under new regime

# ======================== IMPORTANT GOVERNMENT URLS ========================

GOVT_URLS = {
    'income_tax_filing': 'https://www.incometax.gov.in/iec/foportal/',
    'income_tax_calculator': 'https://www.incometax.gov.in/iec/foportal/tax-calculator',
    'epfo_passbook': 'https://passbook.epfindia.gov.in/MemberPassBook/Login',
    'epfo_uan': 'https://unifiedportal-mem.epfindia.gov.in/memberinterface/',
    'nps_apply': 'https://enps.nsdl.com/eNPS/NationalPensionSystem.html',
    'nps_trust': 'https://www.npscra.nsdl.co.in/',
    'nsi_india': 'https://www.nsiindia.gov.in/',
    'sbi_card': 'https://www.sbicard.com/',
    'rbi_sgb': 'https://www.rbi.org.in/',
    'mutual_funds': 'https://www.mutualfundssahihai.com/',
    'my_scheme': 'https://www.myscheme.gov.in/',
    'pmjjby': 'https://www.myscheme.gov.in/schemes/pmjjby',
    'pmsby': 'https://www.myscheme.gov.in/schemes/pmsby',
    'pmjdy': 'https://www.myscheme.gov.in/schemes/pmjdy',
    'pmvvy': 'https://www.myscheme.gov.in/search',
    'atal_pension': 'https://www.myscheme.gov.in/schemes/apy',
    'stand_up_india': 'https://www.myscheme.gov.in/schemes/sui',
    'mudra': 'https://www.mudra.org.in/',
}

# ======================== GOLD/SILVER BASE RATES (approx market, INR) ========================
# These are used as base for simulated daily fluctuation in ml_engine.py
# Update monthly or when major price movement happens

COMMODITY_BASE = {
    # Gold rates per gram — Mar 16, 2026 (source: goodreturns.in, Chennai)
    'gold_24k_per_gram': 16048,
    'gold_22k_per_gram': 14710,
    'gold_18k_per_gram': 12400,
    # Silver rate — Mar 16, 2026 (₹2,70,000/kg = ₹270/g)
    'silver_per_gram': 270,
    'silver_per_kg': 270000,
    # Daily fluctuation ranges
    'gold_24k_fluctuation': 150,
    'gold_22k_fluctuation': 135,
    'gold_18k_fluctuation': 110,
    'silver_fluctuation': 8,
}

# ======================== BANK FD RATES (TOP BANKS, GENERAL CITIZEN) ========================

BANK_FD_RATES = {
    'SBI': {'1yr': 6.80, '3yr': 7.00, '5yr': 6.50, 'last_updated': 'Mar 2025'},
    'HDFC': {'1yr': 6.60, '3yr': 7.00, '5yr': 7.00, 'last_updated': 'Mar 2025'},
    'ICICI': {'1yr': 6.70, '3yr': 7.00, '5yr': 7.00, 'last_updated': 'Mar 2025'},
    'Axis': {'1yr': 6.70, '3yr': 7.10, '5yr': 7.00, 'last_updated': 'Mar 2025'},
    'Kotak': {'1yr': 6.60, '3yr': 7.10, '5yr': 6.70, 'last_updated': 'Mar 2025'},
    'PNB': {'1yr': 6.80, '3yr': 7.00, '5yr': 6.50, 'last_updated': 'Mar 2025'},
}


def get_rate_summary():
    """Return a summary of all current rates for display."""
    return {
        'small_savings': SCHEME_RATES,
        'pf_rates': PF_RATES,
        'nps_returns': NPS_RETURNS,
        'tax_slabs': NEW_TAX_SLABS,
        'commodity': COMMODITY_BASE,
        'fd_rates': BANK_FD_RATES,
        'urls': GOVT_URLS,
    }
