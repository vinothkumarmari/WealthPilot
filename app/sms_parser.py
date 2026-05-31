"""SMS Transaction Parser — AI-powered extraction using Google Gemini Flash.

Parses Indian bank SMS messages to automatically extract transaction details:
- Amount, type (debit/credit), merchant, account, date, UPI ref, etc.
- Falls back to regex-based parsing when Gemini is unavailable.
"""

import re
import json
import logging
from datetime import datetime, date

import requests

log = logging.getLogger(__name__)

# ── Regex patterns for common Indian bank SMS formats ──────────────────

_AMOUNT_PATTERNS = [
    r'Rs\.?\s*([\d,]+\.?\d*)',
    r'INR\s*([\d,]+\.?\d*)',
    r'₹\s*([\d,]+\.?\d*)',
    r'Rupees\s*([\d,]+\.?\d*)',
]

_DEBIT_KEYWORDS = [
    'debited', 'spent', 'paid', 'withdrawn', 'purchase', 'deducted',
    'sent', 'transferred', 'txn of rs', 'payment of', 'used at',
    'has been used', 'charged', 'debit', 'dr', 'outgoing',
]

_CREDIT_KEYWORDS = [
    'credited', 'received', 'deposited', 'refund', 'cashback',
    'credit', 'cr', 'incoming', 'added', 'reversed',
    'salary', 'interest',
]

# Category mapping for merchants/keywords in SMS
_SMS_CATEGORY_MAP = {
    'Food & Groceries': ['swiggy', 'zomato', 'bigbasket', 'blinkit', 'zepto', 'dunzo',
                         'dmart', 'grocery', 'restaurant', 'cafe', 'food', 'instamart',
                         'dominos', 'pizza', 'mcdonald', 'kfc', 'burger'],
    'Transportation': ['uber', 'ola', 'rapido', 'metro', 'petrol', 'fuel', 'irctc',
                       'redbus', 'fastag', 'parking', 'toll', 'makemytrip', 'goibibo'],
    'Shopping': ['amazon', 'flipkart', 'myntra', 'meesho', 'ajio', 'nykaa', 'croma',
                 'snapdeal', 'jiomart', 'reliance', 'tatacliq', 'decathlon'],
    'Utilities': ['electricity', 'water', 'gas', 'broadband', 'jio', 'airtel', 'bsnl',
                  'recharge', 'prepaid', 'postpaid', 'dth', 'tata play', 'dish tv', 'wifi'],
    'Entertainment': ['netflix', 'hotstar', 'prime video', 'spotify', 'youtube',
                      'bookmyshow', 'pvr', 'inox', 'gaming', 'subscription'],
    'Healthcare': ['apollo', 'hospital', 'pharmacy', 'medical', 'pharmeasy', 'netmeds',
                   '1mg', 'clinic', 'doctor', 'diagnostic', 'medplus'],
    'Insurance': ['lic', 'insurance', 'premium', 'bajaj allianz', 'star health',
                  'hdfc life', 'icici pru', 'policy'],
    'Education': ['school', 'college', 'tuition', 'coaching', 'udemy', 'coursera',
                  'unacademy', 'byju', 'exam', 'fee'],
    'Loan': ['emi', 'loan', 'instalment', 'repayment', 'lending'],
    'Investments': ['mutual fund', 'sip', 'zerodha', 'groww', 'upstox', 'kuvera',
                    'stock', 'nps', 'gold bond'],
    'Housing': ['rent', 'maintenance', 'society', 'property'],
    'Personal Care': ['salon', 'spa', 'gym', 'fitness', 'laundry'],
    'Charity': ['donation', 'charity', 'temple', 'trust'],
}

_INCOME_TYPE_MAP = {
    'Salary': ['salary', 'sal cr', 'payroll', 'stipend', 'wage'],
    'Freelance': ['freelance', 'consulting', 'contract'],
    'Interest': ['interest', 'int cr', 'int.cr'],
    'Dividends': ['dividend'],
    'Rental Income': ['rent received', 'rental'],
    'Investment Returns': ['redemption', 'maturity', 'returns'],
    'Other': [],
}


def _get_gemini_key():
    """Get Gemini API key from Flask config or env."""
    try:
        from flask import current_app
        return current_app.config.get('GEMINI_API_KEY', '')
    except RuntimeError:
        import os
        return os.environ.get('GEMINI_API_KEY', '')


# ── Gemini AI SMS Parser ──────────────────────────────────────────────

_SMS_PARSE_PROMPT = """You are an Indian bank SMS parser. Given one or more SMS messages, extract transaction details.

For EACH SMS, return a JSON object with these fields:
- "type": "debit" or "credit" (expense or income)
- "amount": number (the transaction amount in INR, no commas)
- "merchant": string (merchant/payee/payer name if available, otherwise "")
- "category": string (one of: Housing, Food & Groceries, Transportation, Utilities, Healthcare, Insurance, Education, Entertainment, Shopping, Personal Care, Loan, Debt Payments, Savings, Investments, Charity, Miscellaneous)
- "income_type": string (if credit: one of Salary, Freelance, Business, Rental Income, Investment Returns, Dividends, Interest, Other)
- "account": string (last 4 digits of account/card if mentioned, otherwise "")
- "date": string (date in YYYY-MM-DD format if found in SMS, otherwise "")
- "upi_ref": string (UPI reference number if present, otherwise "")
- "description": string (brief description of the transaction)
- "balance": number or null (available balance after transaction if mentioned)
- "original_sms": string (the original SMS text)

Return a JSON array of objects, one per SMS message. If an SMS is not a transaction (like OTP, promo, etc.), skip it.

Important rules:
- Indian banks: SBI, HDFC, ICICI, Axis, Kotak, PNB, BOB, Canara, etc.
- UPI apps: GPay, PhonePe, Paytm, BHIM, etc.
- Amount can be in formats: Rs.1000, INR 1,000.00, Rs 500, ₹1500
- Dates can be in formats: 01-Jan-25, 01/01/2025, 2025-01-01, 01Jan25, Jan 01 2025
- For salary credits, set category to "Salary" and income_type to "Salary"
- For refunds, set type to "credit" and category same as the original purchase category if identifiable

SMS messages to parse:
"""


def _ai_parse_sms(sms_text):
    """Use Gemini Flash to parse SMS messages into structured transactions."""
    api_key = _get_gemini_key()
    if not api_key:
        return None

    prompt = _SMS_PARSE_PROMPT + sms_text

    try:
        resp = requests.post(
            f'https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}',
            json={
                'contents': [{'parts': [{'text': prompt}]}],
                'generationConfig': {
                    'temperature': 0.1,
                    'maxOutputTokens': 4096,
                    'responseMimeType': 'application/json',
                }
            },
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()

        text = data['candidates'][0]['content']['parts'][0]['text']
        text = re.sub(r'^```json\s*', '', text.strip())
        text = re.sub(r'\s*```$', '', text.strip())
        result = json.loads(text)

        if isinstance(result, dict):
            result = [result]

        log.info('Gemini parsed %d transactions from SMS', len(result))
        return result

    except Exception as e:
        log.warning('Gemini SMS parse failed: %s', e)
        return None


# ── Regex Fallback Parser ─────────────────────────────────────────────

def _regex_parse_single_sms(sms):
    """Parse a single SMS using regex patterns. Returns dict or None."""
    sms_lower = sms.lower()

    # Determine transaction type
    txn_type = None
    for kw in _DEBIT_KEYWORDS:
        if kw in sms_lower:
            txn_type = 'debit'
            break
    if not txn_type:
        for kw in _CREDIT_KEYWORDS:
            if kw in sms_lower:
                txn_type = 'credit'
                break
    if not txn_type:
        return None  # Not a transaction SMS

    # Extract amount
    amount = None
    for pattern in _AMOUNT_PATTERNS:
        m = re.search(pattern, sms, re.IGNORECASE)
        if m:
            amount = float(m.group(1).replace(',', ''))
            break
    if not amount or amount <= 0:
        return None

    # Extract balance
    balance = None
    bal_match = re.search(r'(?:bal|balance|avl bal|avbl bal|available)[:\s]*(?:Rs\.?|INR|₹)\s*([\d,]+\.?\d*)', sms, re.IGNORECASE)
    if bal_match:
        balance = float(bal_match.group(1).replace(',', ''))

    # Extract account/card
    account = ''
    acc_match = re.search(r'(?:a/c|ac|acct|account|card)[:\s]*[xX*]*(\d{4})', sms, re.IGNORECASE)
    if acc_match:
        account = acc_match.group(1)

    # Extract UPI ref
    upi_ref = ''
    upi_match = re.search(r'(?:UPI[:\s]*|ref[:\s.#]*)(\d{10,12})', sms, re.IGNORECASE)
    if upi_match:
        upi_ref = upi_match.group(1)

    # Extract date
    txn_date = ''
    date_patterns = [
        (r'(\d{4})[/-](\d{1,2})[/-](\d{1,2})', '%Y-%m-%d'),
        (r'(\d{1,2})[/-](\w{3})[/-](\d{2,4})', '%d-%b-%y'),
        (r'(\d{1,2})(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)(\d{2,4})', None),
        (r'(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})', None),  # dd-mm-yy or dd-mm-yyyy
    ]
    for pat, fmt in date_patterns:
        dm = re.search(pat, sms, re.IGNORECASE)
        if dm:
            try:
                raw = dm.group(0)
                if fmt is None:
                    # Handle no-separator or ambiguous-length year
                    d, m, y = dm.group(1), dm.group(2), dm.group(3)
                    raw = f'{d}-{m}-{y}'
                    if m.isdigit():
                        fmt = '%d-%m-%y' if len(y) == 2 else '%d-%m-%Y'
                    else:
                        fmt = '%d-%b-%y' if len(y) == 2 else '%d-%b-%Y'
                else:
                    raw = raw.replace('/', '-')
                parsed = datetime.strptime(raw, fmt)
                txn_date = parsed.strftime('%Y-%m-%d')
                break
            except ValueError:
                continue

    # Extract merchant (text after 'at', 'to', 'from', 'by', 'VPA')
    merchant = ''
    merch_patterns = [
        r'(?:at|to)\s+([A-Za-z][A-Za-z0-9@.\-_ ]+?)(?:\s*(?:\bon\b|\bref\b|\bupi\b|\btxn\b|\bavl\b|\bbal\b|\bIMPS\b|\.|$))',
        r'(?:VPA|payee)[:\s]+([A-Za-z0-9@.\-_]+)',
        r'(?:from)\s+([A-Za-z][A-Za-z0-9@.\-_ ]+?)(?:\s*(?:\bon\b|\bref\b|\bupi\b|\btxn\b|\bavl\b|\bbal\b|\bIMPS\b|\.|$))',
    ]
    for mp in merch_patterns:
        merch_match = re.search(mp, sms, re.IGNORECASE)
        if merch_match:
            merchant = merch_match.group(1).strip()[:100]
            break

    # Categorize
    category = 'Miscellaneous'
    income_type = 'Other'
    if txn_type == 'debit':
        search_text = (merchant + ' ' + sms).lower()
        for cat, keywords in _SMS_CATEGORY_MAP.items():
            for kw in keywords:
                if kw in search_text:
                    category = cat
                    break
            if category != 'Miscellaneous':
                break
    else:
        for itype, keywords in _INCOME_TYPE_MAP.items():
            for kw in keywords:
                if kw in sms_lower:
                    income_type = itype
                    break
            if income_type != 'Other':
                break

    return {
        'type': txn_type,
        'amount': amount,
        'merchant': merchant,
        'category': category,
        'income_type': income_type,
        'account': account,
        'date': txn_date,
        'upi_ref': upi_ref,
        'description': merchant or (f'{"Debit" if txn_type == "debit" else "Credit"} transaction'),
        'balance': balance,
        'original_sms': sms.strip(),
    }


def _regex_parse_sms(sms_text):
    """Parse multiple SMS messages using regex. Returns list of dicts."""
    # Split by common SMS separators (double newline, or SMS-like boundaries)
    messages = re.split(r'\n\s*\n|\n(?=[A-Z]{2,}[\-\s])', sms_text.strip())
    if len(messages) == 1:
        # Try splitting by single newlines if each line looks like a separate SMS
        lines = sms_text.strip().split('\n')
        if all(len(l.strip()) > 20 for l in lines if l.strip()):
            messages = lines

    results = []
    for msg in messages:
        msg = msg.strip()
        if not msg or len(msg) < 15:
            continue
        parsed = _regex_parse_single_sms(msg)
        if parsed:
            results.append(parsed)

    return results


# ── Main Parse Function ───────────────────────────────────────────────

def parse_sms_transactions(sms_text):
    """Parse SMS text into structured transactions.

    Tries Gemini AI first, falls back to regex parsing.
    Returns list of transaction dicts.
    """
    if not sms_text or not sms_text.strip():
        return []

    # Try AI first
    result = _ai_parse_sms(sms_text)
    if result:
        # Mark as AI-parsed and validate
        validated = []
        for txn in result:
            if not isinstance(txn, dict):
                continue
            if not txn.get('amount') or not txn.get('type'):
                continue
            try:
                txn['amount'] = float(str(txn['amount']).replace(',', ''))
            except (ValueError, TypeError):
                continue
            if txn['amount'] <= 0:
                continue
            txn['ai_parsed'] = True
            txn.setdefault('category', 'Miscellaneous')
            txn.setdefault('income_type', 'Other')
            txn.setdefault('merchant', '')
            txn.setdefault('account', '')
            txn.setdefault('date', '')
            txn.setdefault('upi_ref', '')
            txn.setdefault('description', txn.get('merchant', 'Transaction'))
            txn.setdefault('balance', None)
            txn.setdefault('original_sms', '')
            validated.append(txn)
        if validated:
            return validated

    # Fallback to regex
    result = _regex_parse_sms(sms_text)
    for txn in result:
        txn['ai_parsed'] = False
    return result
