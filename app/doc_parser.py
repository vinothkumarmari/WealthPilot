"""
Document Parser - Extract policy/scheme information from uploaded documents.
Supports PDF and image files. Uses text extraction + pattern matching.
"""
import re
import os
from datetime import datetime


def _fix_doubled_text(text):
    """Fix text where characters are doubled (common PDF extraction issue).
    Works per-line to handle documents where only some lines are affected.
    E.g., 'FFoorrttuunnee PPrroo' -> 'Fortune Pro'
    """
    if not text or len(text) < 10:
        return text

    def _is_line_doubled(line):
        """Check if a single line has doubled characters."""
        stripped = line.replace(' ', '')
        if len(stripped) < 6:
            return False
        doubled = 0
        total = 0
        for i in range(0, len(stripped) - 1, 2):
            total += 1
            if stripped[i] == stripped[i + 1]:
                doubled += 1
        return total > 2 and (doubled / total) > 0.65

    def _undouble_line(line):
        """Remove doubled characters from a line."""
        cleaned = []
        i = 0
        while i < len(line):
            cleaned.append(line[i])
            if i + 1 < len(line) and line[i] == line[i + 1] and line[i] != ' ':
                i += 2
            else:
                i += 1
        return ''.join(cleaned)

    result_lines = []
    for line in text.split('\n'):
        if _is_line_doubled(line):
            result_lines.append(_undouble_line(line))
        else:
            result_lines.append(line)
    return '\n'.join(result_lines)


def _fix_reversed_text(text):
    """Fix text where lines are character-reversed (PDF extraction artifact).
    Detects blocks of reversed text by finding lines with known reversed words,
    then reverses all lines within those blocks (including data-only lines nearby).
    """
    if not text:
        return text
    reversed_indicators = [
        'muimerP', 'derussA', 'desilaunnA', 'yciloP', 'mreT', 'efiL',
        'htaeD', 'ytirutaM', 'tifeneB', 'egarevoC', 'tnemecnemmoC',
        'ladoM', 'tnemyaP', 'gnitirwrednU', 'ecnarusnI',
    ]
    lines = text.split('\n')
    # Mark lines that contain reversed indicator words
    is_reversed = [False] * len(lines)
    for i, line in enumerate(lines):
        if any(rw in line for rw in reversed_indicators):
            is_reversed[i] = True
    # Expand reversed marks to cover nearby lines (within 3 lines of a reversed line)
    # This catches data-only lines like amounts/numbers within reversed blocks
    expanded = list(is_reversed)
    for i in range(len(lines)):
        if is_reversed[i]:
            for j in range(max(0, i - 3), min(len(lines), i + 4)):
                # Only expand to short lines (data values) — don't expand to long normal text
                if not expanded[j] and len(lines[j].strip()) <= 20:
                    expanded[j] = True
    result_lines = []
    for i, line in enumerate(lines):
        if expanded[i] and len(line.strip()) > 0:
            result_lines.append(line[::-1])
        else:
            result_lines.append(line)
    return '\n'.join(result_lines)


def extract_text_from_pdf(file_path):
    """Extract text content from a PDF file."""
    try:
        import pdfplumber
        text = ''
        with pdfplumber.open(file_path) as pdf:
            # Limit to first 10 pages for speed (policy details are in first few pages)
            pages_to_scan = pdf.pages[:10]
            for page in pages_to_scan:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + '\n'
                # Also try extracting from tables
                tables = page.extract_tables()
                for table in tables:
                    for row in table:
                        if row:
                            text += ' '.join(str(cell) for cell in row if cell) + '\n'
        text = text.strip()
        # Fix doubled-character extraction issue
        text = _fix_doubled_text(text)
        # Fix reversed-character extraction issue
        text = _fix_reversed_text(text)
        return text
    except Exception as e:
        return ''


def extract_text_from_image(file_path):
    """Extract text from image using pytesseract OCR if available."""
    try:
        from PIL import Image
        import pytesseract
        img = Image.open(file_path)
        # Try to enhance for better OCR
        img = img.convert('L')  # grayscale
        return pytesseract.image_to_string(img, lang='eng')
    except ImportError:
        return '__NO_TESSERACT__'
    except Exception:
        return ''


def extract_text(file_path):
    """Extract text from any supported file type."""
    ext = os.path.splitext(file_path)[1].lower()
    if ext == '.pdf':
        return extract_text_from_pdf(file_path)
    elif ext in ('.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.webp'):
        result = extract_text_from_image(file_path)
        return result
    return ''


def _find_amount(text, patterns):
    """Find monetary amount using multiple regex patterns."""
    for pattern in patterns:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            amount_str = match.group(1).replace(',', '').replace(' ', '')
            if not amount_str or not any(c.isdigit() for c in amount_str):
                continue
            try:
                val = float(amount_str)
                if val >= 100:  # Skip tiny numbers (footnotes, multipliers)
                    return val
            except ValueError:
                continue
    return 0


def _find_date(text, patterns):
    """Find date using multiple regex patterns."""
    date_formats = [
        '%d/%m/%Y', '%d-%m-%Y', '%d-%b-%Y', '%d %b %Y', '%d %B %Y',
        '%Y-%m-%d', '%d.%m.%Y', '%b %d, %Y', '%B %d, %Y',
        '%d/%m/%y', '%d-%m-%y'
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            date_str = match.group(1).strip()
            for fmt in date_formats:
                try:
                    return datetime.strptime(date_str, fmt).strftime('%Y-%m-%d')
                except ValueError:
                    continue
    return ''


def _parse_date_str(date_str):
    """Parse a date string in common formats and return YYYY-MM-DD."""
    date_formats = [
        '%d/%m/%Y', '%d-%m-%Y', '%d-%b-%Y', '%d %b %Y', '%d %B %Y',
        '%Y-%m-%d', '%d.%m.%Y', '%d/%m/%y', '%d-%m-%y'
    ]
    for fmt in date_formats:
        try:
            return datetime.strptime(date_str.strip(), fmt).strftime('%Y-%m-%d')
        except ValueError:
            continue
    return ''


def _find_text(text, patterns):
    """Find text value using multiple regex patterns."""
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1).strip()
    return ''


def _detect_provider(text, providers):
    """Detect insurance/scheme provider from text."""
    text_upper = text.upper()
    provider_keywords = {
        'TATA AIA': ['TATA AIA', 'TATA-AIA'],
        'AXIS Max Life': ['MAX LIFE', 'AXIS MAX'],
        'Bajaj Allianz': ['BAJAJ ALLIANZ', 'BAJAJ'],
        'LIC': ['LIFE INSURANCE CORPORATION', 'LIC OF INDIA', r'\bLIC\b'],
        'HDFC Life': ['HDFC LIFE', 'HDFC STANDARD'],
        'SBI Life': ['SBI LIFE'],
        'ICICI Prudential': ['ICICI PRUDENTIAL', 'ICICI PRU'],
        'Kotak Life': ['KOTAK LIFE', 'KOTAK MAHINDRA LIFE'],
        'Star Health': ['STAR HEALTH'],
        'Niva Bupa': ['NIVA BUPA', 'MAX BUPA'],
        'PNB MetLife': ['PNB METLIFE', 'METLIFE'],
        'Aditya Birla Health': ['ADITYA BIRLA'],
    }
    for provider, keywords in provider_keywords.items():
        for kw in keywords:
            if re.search(kw, text_upper):
                return provider

    for prov in providers:
        if prov.upper() in text_upper:
            return prov
    return ''


def _detect_policy_type(text):
    """Detect policy type from document text."""
    text_upper = text.upper()
    type_map = {
        'Term Life': ['TERM PLAN', 'TERM LIFE', 'TERM INSURANCE', 'TERM ASSURANCE', 'PROTECTION PLAN',
                       'ISMART', 'I-SMART', 'SMART SAMPOORNA', 'RAKSHA SUPREME', 'TECH TERM',
                       'CLICK 2 PROTECT', 'EPROTECT', 'E-PROTECT', 'IPROTECT', 'SARAL JEEVAN BIMA'],
        'ULIP': ['ULIP', 'UNIT LINKED', 'UNIT-LINKED', 'FLEXI CAP', 'WEALTH PLUS', 'INVEST 4G',
                  'ACE INVESTMENT', 'WEALTH PRO', 'LIFE LONG WEALTH', 'ONLINE SAVINGS PLAN',
                  'FORTUNE PRO'],
        'Endowment': ['ENDOWMENT', 'JEEVAN ANAND', 'JEEVAN LAKSHYA', 'JEEVAN UMANG', 'FORTUNE GUARANTEE',
                       'GUARANTEED RETURN', 'GUARANTEED INCOME', 'ASSURED INCOME',
                       'SMART VALUE', 'GUARANTEED SAVINGS', 'SMART SAMPOORNA',
                       'ASSURED WEALTH', 'WEALTH PLAN', 'NON-LINKED NON-PARTICIPATING'],
        'Money Back': ['MONEY BACK', 'MONEYBACK', 'CASH BACK'],
        'Whole Life': ['WHOLE LIFE', 'WHOLE OF LIFE', 'LIFETIME', 'LIFE LONG'],
        'Health Insurance': ['HEALTH INSURANCE', 'HEALTH POLICY', 'MEDICLAIM', 'HEALTH GUARD',
                              'HEALTH COMPANION', 'HEALTH GAIN', 'OPTIMA', 'ACTIVE HEALTH',
                              'FAMILY HEALTH', 'HEALTH PROTECT', 'CARE SUPREME', 'VITAL HEALTH'],
        'Critical Illness': ['CRITICAL ILLNESS', 'CRITICAL CARE', 'CRISIS COVER'],
        'Accident Cover': ['PERSONAL ACCIDENT', 'ACCIDENT COVER', 'ACCIDENT INSURANCE'],
        'Child Plan': ['CHILD PLAN', 'CHILD EDUCATION', "CHILDREN'S", 'CHILD FUTURE',
                        'YOUNG SCHOLAR', 'BACHAT PLAN'],
        'Pension Plan': ['PENSION', 'RETIREMENT', 'ANNUITY', 'SARAL PENSION'],
    }
    for ptype, keywords in type_map.items():
        for kw in keywords:
            if kw in text_upper:
                return ptype
    # Fallback: if "life insurance" or "life" is mentioned, likely a life policy
    if 'LIFE INSURANCE' in text_upper or 'LIFE ASSURANCE' in text_upper:
        return 'Term Life'
    if 'INSURANCE' in text_upper:
        return 'Health Insurance'
    return ''


def _detect_scheme_type(text):
    """Detect scheme type from document text."""
    text_upper = text.upper()
    type_map = {
        'Gold Scheme': ['GOLD SCHEME', 'GOLD SAVING', 'GOLD PLAN', 'GOLD DEPOSIT'],
        'Silver Scheme': ['SILVER SCHEME', 'SILVER SAVING'],
        'Chit Fund': ['CHIT FUND', 'CHIT SCHEME', 'CHITTY'],
        'Recurring Deposit': ['RECURRING DEPOSIT', 'RD ACCOUNT', r'\bRD\b'],
        'Government Bonds': ['GOVT BOND', 'GOVERNMENT BOND', 'G-SEC', 'GSEC'],
        'Corporate Bonds': ['CORPORATE BOND', 'NCD', 'DEBENTURE'],
        'Sovereign Gold Bond': ['SOVEREIGN GOLD', 'SGB'],
        'Bonds': ['BOND', 'FIXED INCOME'],
        'Post Office Scheme': ['POST OFFICE', 'INDIA POST'],
        'Kisan Vikas Patra': ['KISAN VIKAS', 'KVP'],
        'NSC': ['NATIONAL SAVINGS CERTIFICATE', r'\bNSC\b'],
        'Sukanya Samriddhi': ['SUKANYA', 'SSY'],
        'Senior Citizen Scheme': ['SENIOR CITIZEN', 'SCSS'],
    }
    for stype, keywords in type_map.items():
        for kw in keywords:
            if re.search(kw, text_upper):
                return stype
    return ''


def _detect_frequency(text):
    """Detect payment frequency from text."""
    # Most specific: "Premium Payment Frequency Monthly" or "Frequency of Payment : Monthly"
    freq_direct = re.search(
        r'(?:premium\s*payment\s*frequency|frequency\s*of\s*payment|(?:payment|premium)\s*frequency\s*:)\s*[:\-]?\s*(monthly|half[- ]?yearly|quarterly|yearly|annual)\b',
        text, re.IGNORECASE
    )
    if freq_direct:
        freq = freq_direct.group(1).upper()
        if 'MONTH' in freq:
            return 'monthly'
        if 'HALF' in freq:
            return 'half-yearly'
        if 'QUARTER' in freq:
            return 'quarterly'
        return 'yearly'
    # Check "Mode of Premium Payment" on the SAME line (no DOTALL to avoid cross-line noise)
    mode_match = re.search(
        r'(?:mode\s*of\s*(?:premium\s*)?payment|premium\s*(?:payment\s*)?mode)[:\s]+'
        r'(monthly|half[- ]?yearly|quarterly|yearly|annual)',
        text, re.IGNORECASE
    )
    if mode_match:
        freq = mode_match.group(1).upper()
        if 'MONTH' in freq:
            return 'monthly'
        if 'HALF' in freq:
            return 'half-yearly'
        if 'QUARTER' in freq:
            return 'quarterly'
        return 'yearly'
    # Check TATA AIA table row ending with "Annual" or "Monthly" (after numbers and dates)
    table_mode = re.search(
        r'[\d,]+\.\d{2}\s+(?:NA\s+)?\d+\s+\d+\s+(Annual|Monthly|Quarterly|Half[- ]?Yearly)\s*$',
        text, re.IGNORECASE | re.MULTILINE
    )
    if table_mode:
        freq = table_mode.group(1).upper()
        if 'MONTH' in freq:
            return 'monthly'
        if 'HALF' in freq:
            return 'half-yearly'
        if 'QUARTER' in freq:
            return 'quarterly'
        return 'yearly'
    # Check table rows for frequency word (e.g., "Fortune Pro Monthly 10")
    table_freq = re.search(
        r'(?:Monthly|Yearly|Annual|Quarterly|Half[- ]?Yearly)\s+\d+\s+\d{4}/',
        text
    )
    if table_freq:
        freq = table_freq.group(0).split()[0].upper()
        if 'MONTH' in freq:
            return 'monthly'
        if 'HALF' in freq:
            return 'half-yearly'
        if 'QUARTER' in freq:
            return 'quarterly'
        return 'yearly'
    # Fallback: keyword scan (skip 'ANNUALISED' which is a label, not a frequency)
    text_upper = text.upper()
    if any(w in text_upper for w in ['HALF-YEARLY', 'HALF YEARLY', 'SEMI-ANNUAL']):
        return 'half-yearly'
    if any(w in text_upper for w in ['QUARTERLY', 'QUARTER']):
        return 'quarterly'
    if any(w in text_upper for w in ['MONTHLY', 'PER MONTH', 'P.M.']):
        return 'monthly'
    if re.search(r'\bYEARLY\b|\bANNUAL\b(?!ISED|IZED)|\bPER ANNUM\b|\bP\.A\.', text_upper):
        return 'yearly'
    return 'yearly'


def parse_policy_document(file_path, providers):
    """Parse an insurance policy document and extract key information."""
    text = extract_text(file_path)

    ext = os.path.splitext(file_path)[1].lower()
    is_image = ext in ('.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.webp')

    if text == '__NO_TESSERACT__':
        return {
            'success': False,
            'message': 'Image scanning requires Tesseract OCR which is not installed on this server. '
                       'Please upload a PDF document instead, or use "Paste Text" to manually enter the document text.',
            'data': {},
            'needs_text_input': True
        }

    if not text:
        msg = 'Could not extract text from the uploaded file. '
        if is_image:
            msg += 'Image may be too blurry or not a text document. Try uploading a clear PDF instead, or use "Paste Text".'
        else:
            msg += 'The PDF may be scanned/image-based. Try using "Paste Text" to enter details manually.'
        return {'success': False, 'message': msg, 'data': {}, 'needs_text_input': True}

    return _parse_policy_text(text, providers)


def parse_policy_from_text(text, providers):
    """Parse policy details from user-pasted text."""
    if not text or len(text.strip()) < 10:
        return {'success': False, 'message': 'Text is too short. Please paste the full policy document text.', 'data': {}}
    text = _fix_doubled_text(text)
    return _parse_policy_text(text, providers)


def _parse_policy_text(text, providers):

    # Cross-detection: check if this is actually a scheme document
    scheme_sc = _scheme_score(text)
    policy_sc = _policy_score(text)
    if scheme_sc >= 3 and scheme_sc > policy_sc:
        return {
            'success': False,
            'message': 'This appears to be a scheme/bond document. Please use the "Schemes & Bonds" page to scan it instead.',
            'data': {},
            'is_wrong_type': True
        }

    data = {}

    # Provider
    data['provider'] = _detect_provider(text, providers)

    # Policy type
    data['policy_type'] = _detect_policy_type(text)

    # Policy name - try multiple patterns, most specific first
    data['policy_name'] = _find_text(text, [
        r'opting\s+for\s+(?:Max Life\s+|Tata AIA\s+|HDFC\s+|SBI\s+|ICICI\s+|Bajaj\s+|LIC\s+|Kotak\s+)?(.+(?:Plan|Policy|Pro|Shield|Guard|Cover|Raksha|Sampoorna|Protect))(?:\s*[\(\.,]|\s+\()',
        r'Insurance\s+(.+?)\s*\(?UIN',
        r'(?:plan\s*name|policy\s*name|product\s*name)\s*[:\-]\s*\n?\s*(.+?)(?:\n|$)',
        r'(?:name\s*of\s*(?:the\s*)?(?:plan|policy\b|product))\s*[:\-]?\s*(.+?)(?:\n|$)',
        r'(?:product|plan)\s*[:\-]\s*(.+?)(?:\n|$)',
    ])
    # Clean up plan name if it contains noise like "(UIN:" or "Policy Owner"
    if data['policy_name']:
        name = re.sub(r'\s*\(UIN.*', '', data['policy_name']).strip()
        name = re.sub(r'\s*Policy\s*(?:Owner|Number).*', '', name, flags=re.IGNORECASE).strip()
        data['policy_name'] = name if len(name) > 3 else ''

    # Policy number
    data['policy_number'] = _find_text(text, [
        r'(?:policy\s*(?:no|number|#|num)\.?)\s*[:\-]?\s*([A-Za-z0-9\-/]+)',
        r'(?:certificate\s*(?:no|number|#)\.?)\s*[:\-]?\s*([A-Za-z0-9\-/]+)',
        r'(?:contract\s*(?:no|number)\.?)\s*[:\-]?\s*([A-Za-z0-9\-/]+)',
        r'(?:application\s*(?:no|number|#|id)\.?)\s*[:\-]?\s*([A-Za-z0-9\-/]+)',
        r'(?:ref(?:erence)?\s*(?:no|number|#|id)\.?)\s*[:\-]?\s*([A-Za-z0-9\-/]+)',
    ])

    # Sum assured - handle "Sum Assured on Maturity 378000.00" and table formats
    data['sum_assured'] = _find_amount(text, [
        r'sum\s*assured\s*(?:on\s*(?:maturity|death))?\s*[:\-]?\s*(?:Rs\.?|₹|INR)?\s*([\d,]+(?:\.\d+)?)',
        r'(?:life\s*cover|cover\s*amount|death\s*benefit|risk\s*cover|total\s*cover)\s*[:\-]?\s*(?:Rs\.?|₹|INR)?\s*([\d,]+(?:\.\d+)?)',
        r'(?:Rs\.?|₹|INR)\s*([\d,]+(?:\.\d+)?)\s*(?:sum\s*assured|life\s*cover)',
        r'(?:SA|S\.A\.)\s*[:\-]?\s*(?:Rs\.?|₹|INR)?\s*([\d,]+(?:\.\d+)?)',
    ])

    # Fallback: extract sum_assured from table row (sum_assured dates premium)
    if not data['sum_assured']:
        table_sa = re.search(
            r'([\d,]+\.\d{2})\s+\d{1,2}/\d{1,2}/\d{4}\s+\d{1,2}/\d{1,2}/\d{4}\s+\d{1,2}/\d{1,2}/\d{4}\s+[\d,]+\.\d{2}',
            text
        )
        if table_sa:
            try:
                val = float(table_sa.group(1).replace(',', ''))
                if val >= 100:
                    data['sum_assured'] = val
            except ValueError:
                pass

    # Fallback: extract sum_assured from MaxLife-style table (SA term payterm freq code premium)
    if not data['sum_assured']:
        table_sa2 = re.search(
            r'([\d,]+\.\d{2})\s+(\d+)\s+(\d+)\s+(?:Monthly|Yearly|Annual|Quarterly|Half[- ]?Yearly)\s+\d+\s+([\d,]+\.\d{2})',
            text, re.IGNORECASE
        )
        if table_sa2:
            try:
                val = float(table_sa2.group(1).replace(',', ''))
                if val >= 100:
                    data['sum_assured'] = val
            except ValueError:
                pass

    # Premium - try per-installment/modal premium first, then annualised (will convert later)
    _premium_is_annualised = False
    data['premium_amount'] = 0

    # Try table row format: "PlanName Monthly/Yearly term dates premium" (TATA AIA style)
    table_modal = re.search(
        r'(?:Monthly|Yearly|Annual|Quarterly|Half[- ]?Yearly)\s+\d+\s+\d{4}/\d{2}/\d{2}\s+\d{1,2}/\d{1,2}/\d{4}\s+([\d,]+(?:\.\d+)?)',
        text, re.IGNORECASE
    )
    if table_modal:
        try:
            val = float(table_modal.group(1).replace(',', ''))
            if val >= 100:
                data['premium_amount'] = val
        except ValueError:
            pass

    # Try MaxLife table: "SA term payterm Monthly PremiumPerMode AnnualisedPremium"
    # Capture the number immediately after frequency keyword (premium per mode, may lack decimals)
    if not data['premium_amount']:
        table_maxlife = re.search(
            r'[\d,]+(?:\.\d{2})?\s+\d+\s+\d+\s+(?:Monthly|Yearly|Annual|Quarterly|Half[- ]?Yearly)\s+(\d[\d,]*(?:\.\d+)?)\s+[\d,]+(?:\.\d+)?',
            text, re.IGNORECASE
        )
        if table_maxlife:
            try:
                val = float(table_maxlife.group(1).replace(',', ''))
                if val >= 100:
                    data['premium_amount'] = val
            except ValueError:
                pass

    # Try modal/installment premium patterns
    if not data['premium_amount']:
        data['premium_amount'] = _find_amount(text, [
            r'(?:modal\s*premium)\s*[:\-]?\s*(?:\([^)]*\)\s*)?(?:Rs\.?|₹|INR)?\s*([\d,]+(?:\.\d+)?)',
            r'(?:installment|instalment)\s*(?:premium|amount)?\s*[:\-]?\s*(?:Rs\.?|₹|INR)?\s*([\d,]+(?:\.\d+)?)',
            r'(?:premium\s*(?:per\s*(?:month|installment|instalment)))\s*[:\-]?\s*(?:Rs\.?|₹|INR)?\s*([\d,]+(?:\.\d+)?)',
            r'(?:Rs\.?|₹|INR)\s*([\d,]+(?:\.\d+)?)\s*(?:per\s*(?:month|year|annum|quarter)|premium)',
        ])
    # If not found, try general premium patterns
    if not data['premium_amount']:
        data['premium_amount'] = _find_amount(text, [
            r'(?:premium\s*(?:amount|payable)?)\s*[:\-#]?\s*(?:Rs\.?|₹|INR)?\s*([\d,]+(?:\.\d+)?)',
        ])
    # If still not found, try annualised premium (mark it so we can convert after freq detection)
    if not data['premium_amount']:
        data['premium_amount'] = _find_amount(text, [
            r'(?:annual(?:ised|ized)?\s*premium)\s*[:\-]?\s*(?:\([^)]*\)\s*)?(?:Rs\.?|₹|INR)?\s*([\d,]+(?:\.\d+)?)',
            r'(?:total\s*premium|gross\s*premium|net\s*premium)\s*[:\-]?\s*(?:Rs\.?|₹|INR)?\s*([\d,]+(?:\.\d+)?)',
        ])
        if data['premium_amount']:
            _premium_is_annualised = True
    # Check if the first-match premium was actually from an annualised label
    if data['premium_amount'] and not _premium_is_annualised:
        ann_match = re.search(
            r'(?:annual(?:ised|ized)?\s*premium)\s*[:\-]?\s*(?:\([^)]*\)\s*)?(?:Rs\.?|₹|INR)?\s*([\d,]+(?:\.\d+)?)',
            text, re.IGNORECASE
        )
        if ann_match and ann_match.group(1):
            try:
                ann_val = float(ann_match.group(1).replace(',', ''))
                if abs(ann_val - data['premium_amount']) < 1:
                    _premium_is_annualised = True
            except ValueError:
                pass

    # Fallback: extract premium from table row (sum_assured dates premium term)
    if not data['premium_amount']:
        table_prem = re.search(
            r'[\d,]+\.\d{2}\s+\d{1,2}/\d{1,2}/\d{4}\s+\d{1,2}/\d{1,2}/\d{4}\s+\d{1,2}/\d{1,2}/\d{4}\s+([\d,]+\.\d{2})',
            text
        )
        if table_prem:
            try:
                val = float(table_prem.group(1).replace(',', ''))
                if val >= 100:
                    data['premium_amount'] = val
            except ValueError:
                pass

    # Fallback: extract premium from MaxLife-style table (SA term payterm freq code premium)
    if not data['premium_amount']:
        table_prem2 = re.search(
            r'[\d,]+\.\d{2}\s+\d+\s+\d+\s+(?:Monthly|Yearly|Annual|Quarterly|Half[- ]?Yearly)\s+\d+\s+([\d,]+\.\d{2})',
            text, re.IGNORECASE
        )
        if table_prem2:
            try:
                val = float(table_prem2.group(1).replace(',', ''))
                if val >= 100:
                    data['premium_amount'] = val
            except ValueError:
                pass

    # Premium frequency
    data['premium_frequency'] = _detect_frequency(text)

    # Convert annualised premium to per-period amount based on detected frequency
    if _premium_is_annualised and data['premium_amount'] and data['premium_frequency'] != 'yearly':
        divisor = {'monthly': 12, 'quarterly': 4, 'half-yearly': 2}.get(data['premium_frequency'], 1)
        data['premium_amount'] = round(data['premium_amount'] / divisor, 2)

    # Maturity value
    data['maturity_value'] = _find_amount(text, [
        r'(?:sum\s*assured\s*on\s*maturity)\s*[:\-]?\s*(?:Rs\.?|₹|INR)?\s*([\d,]+(?:\.\d+)?)',
        r'(?:maturity\s*(?:value|benefit|amount|sum))\s*[:\-]?\s*(?:Rs\.?|₹|INR)?\s*([\d,]+(?:\.\d+)?)',
        r'(?:guaranteed\s*(?:maturity|payout|return))\s*[:\-]?\s*(?:Rs\.?|₹|INR)?\s*([\d,]+(?:\.\d+)?)',
        r'(?:survival\s*benefit|money\s*back\s*amount)\s*[:\-]?\s*(?:Rs\.?|₹|INR)?\s*([\d,]+(?:\.\d+)?)',
    ])

    # Nominee - handle table format and Mr./Mrs. prefix
    data['nominee'] = _find_text(text, [
        r'Nominee[\s\S]{1,300}?(?:Mr\.?|Mrs\.?|Ms\.?)\s+([A-Z][a-zA-Z\s]{2,25}?)(?:\s+(?:Other|Father|Mother|Brother|Sister|Spouse|Wife|Husband|Son|Daughter|Self))',
        r'(?:name\s*of\s*(?:the\s*)?nominee\s*\(?s?\)?\s*.*?\n)\s*([A-Z][A-Za-z\s]{2,25}?)(?:\s+(?:Father|Mother|Brother|Sister|Spouse|Wife|Husband|Son|Daughter|Self|Other|Male|Female))',
        r'Nominee\n([A-Z][A-Za-z\s]{2,25}?)(?:\s+(?:Male|Female))',
        r'(?:nominee\s*(?:name)?)\s*[:\-]\s*(?:Mr\.?|Mrs\.?|Ms\.?|Smt\.?|Shri\.?)?\s*([A-Za-z][A-Za-z\s\.]{2,30})(?:\n|,|\d|$)',
        r'(?:beneficiary)\s*[:\-]?\s*([A-Za-z][A-Za-z\s\.]{2,30})(?:\n|,|\(|$)',
    ])

    # Dates - handle dd/mm/yyyy and dd-Mon-yyyy formats in various contexts
    data['start_date'] = _find_date(text, [
        r'(?:commencement\s*(?:date|of\s*(?:policy|risk))|policy\s*(?:start\s*)?date|inception\s*(?:date|of\s*policy)|risk\s*commencement|date\s*of\s*(?:commencement|issue)|issue\s*date)\s*[^:]*?[:\-]\s*(\d{1,2}[\s/\-\.]\w{2,9}[\s/\-\.]\d{2,4})',
        r'(?:effective\s*(?:from|date)|w\.?e\.?f\.?|from\s*date)\s*[:\-]?\s*(\d{1,2}[\s/\-\.]\w{2,9}[\s/\-\.]\d{2,4})',
    ])
    data['maturity_date'] = _find_date(text, [
        r'(?:maturity\s*date|date\s*of\s*maturity|expiry\s*date|valid\s*(?:till|until|upto))\s*[:\-]?\s*(\d{1,2}[\s/\-\.]\w{2,9}[\s/\-\.]\d{2,4})',
        r'(?:policy\s*(?:end|term)\s*date)\s*[:\-]?\s*(\d{1,2}[\s/\-\.]\w{2,9}[\s/\-\.]\d{2,4})',
    ])

    # Fallback: extract dates from table rows (amount followed by dates)
    if not data['start_date'] or not data['maturity_date']:
        # Pattern: sum_assured date date maturity_date premium (table row format)
        table_date_match = re.search(
            r'[\d,]+\.\d{2}\s+(\d{1,2}/\d{1,2}/\d{4})\s+\d{1,2}/\d{1,2}/\d{4}\s+(\d{1,2}/\d{1,2}/\d{4})',
            text
        )
        if table_date_match:
            if not data['start_date']:
                data['start_date'] = _parse_date_str(table_date_match.group(1))
            if not data['maturity_date']:
                data['maturity_date'] = _parse_date_str(table_date_match.group(2))

    # Check if we got useful data
    fields_found = sum(1 for v in data.values() if v)
    if fields_found == 0:
        return {'success': False, 'message': 'Could not detect policy information. Please use "Paste Text" or fill in details manually.', 'data': {}, 'needs_text_input': True}

    if fields_found <= 2:
        return {
            'success': True,
            'message': f'Only detected {fields_found} field(s). The document may not have been read properly. Please verify the data or use "Paste Text" for better results.',
            'data': data,
            'raw_text_preview': text[:500],
            'low_confidence': True
        }

    return {
        'success': True,
        'message': f'Detected {fields_found} fields from document. Please verify and complete the form.',
        'data': data,
        'raw_text_preview': text[:500]
    }


def parse_scheme_document(file_path, scheme_types):
    """Parse a scheme/bond document and extract key information."""
    text = extract_text(file_path)

    ext = os.path.splitext(file_path)[1].lower()
    is_image = ext in ('.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.webp')

    if text == '__NO_TESSERACT__':
        return {
            'success': False,
            'message': 'Image scanning requires Tesseract OCR which is not installed on this server. '
                       'Please upload a PDF document instead, or use "Paste Text" to manually enter the document text.',
            'data': {},
            'needs_text_input': True
        }

    if not text:
        msg = 'Could not extract text from the uploaded file. '
        if is_image:
            msg += 'Image may be too blurry or not a text document. Try uploading a clear PDF instead, or use "Paste Text".'
        else:
            msg += 'The PDF may be scanned/image-based. Try using "Paste Text" to enter details manually.'
        return {'success': False, 'message': msg, 'data': {}, 'needs_text_input': True}

    return _parse_scheme_text(text)


def parse_scheme_from_text(text):
    """Parse scheme details from user-pasted text."""
    if not text or len(text.strip()) < 10:
        return {'success': False, 'message': 'Text is too short. Please paste the full scheme document text.', 'data': {}}
    text = _fix_doubled_text(text)
    return _parse_scheme_text(text)


def _policy_score(text):
    """Score how likely the text is an insurance policy document."""
    text_upper = text.upper()
    policy_keywords = ['PREMIUM PAYMENT', 'PREMIUM RECEIPT', 'SUM ASSURED', 'POLICY NUMBER',
                        'POLICY NO', 'LIFE INSURANCE', 'LIFE ASSURED', 'NOMINEE',
                        'POLICYHOLDER', 'INSURANCE COMPANY', 'DEATH BENEFIT',
                        'MATURITY BENEFIT', 'TATA AIA LIFE', 'HDFC LIFE', 'SBI LIFE',
                        'LIC OF INDIA', 'ICICI PRUDENTIAL', 'BAJAJ ALLIANZ',
                        'POLICYBAZAAR', 'PREMIUM', 'POLICY']
    return sum(1 for kw in policy_keywords if kw in text_upper)


def _scheme_score(text):
    """Score how likely the text is a scheme/bond document."""
    text_upper = text.upper()
    scheme_keywords = ['GOLD SCHEME', 'CHIT FUND', 'RECURRING DEPOSIT', 'BOND',
                        'INSTALLMENT', 'JEWELLER', 'POST OFFICE', 'KVP', 'NSC',
                        'SUKANYA', 'SOVEREIGN GOLD', 'NCD', 'DEBENTURE',
                        'GOLD SAVING', 'CHITTY', 'SILVER SCHEME']
    return sum(1 for kw in scheme_keywords if kw in text_upper)


def _is_policy_document(text):
    """Check if text looks like an insurance policy document."""
    return _policy_score(text) >= 2


def _is_scheme_document(text):
    """Check if text looks like a scheme/bond document."""
    return _scheme_score(text) >= 2


def _parse_scheme_text(text):
    """Internal: parse scheme info from extracted text."""

    # Cross-detection: check if this is actually a policy document
    policy_score = _policy_score(text)
    scheme_score = _scheme_score(text)
    if policy_score >= 3 and policy_score > scheme_score:
        return {
            'success': False,
            'message': 'This appears to be an insurance policy document. Please use the "Policies" page to scan it instead.',
            'data': {},
            'is_wrong_type': True
        }

    data = {}

    # Scheme type
    data['scheme_type'] = _detect_scheme_type(text)

    # Provider / issuer
    data['provider'] = _find_text(text, [
        r'(?:issued\s*by|issuer|company|provider|bank|jeweller|jeweler)\s*[:\-]?\s*(.+?)(?:\n|$)',
        r'(?:branch|bank\s*name)\s*[:\-]?\s*(.+?)(?:\n|$)',
    ])

    # Scheme name
    data['scheme_name'] = _find_text(text, [
        r'(?:scheme\s*name|plan\s*name|bond\s*name|product\s*name)\s*[:\-]?\s*(.+?)(?:\n|$)',
        r'(?:name\s*of\s*(?:the\s*)?(?:scheme|plan|bond))\s*[:\-]?\s*(.+?)(?:\n|$)',
        r'(?:product|scheme|plan)\s*[:\-]\s*(.+?)(?:\n|$)',
    ])

    # Installment amount
    data['installment_amount'] = _find_amount(text, [
        r'(?:installment|instalment|monthly\s*(?:amount|payment)|contribution|deposit\s*amount)\s*[:\-]?\s*(?:Rs\.?|₹|INR)?\s*([\d,]+(?:\.\d+)?)',
        r'(?:Rs\.?|₹|INR)\s*([\d,]+(?:\.\d+)?)\s*(?:per\s*month|monthly|per\s*installment)',
        r'(?:amount|payment)\s*[:\-]?\s*(?:Rs\.?|₹|INR)?\s*([\d,]+(?:\.\d+)?)',
    ])

    # Frequency
    data['installment_frequency'] = _detect_frequency(text)

    # Total installments / tenure
    tenure_match = re.search(r'(?:tenure|term|duration|period|total\s*installments?|no\.?\s*of\s*installments?)\s*[:\-]?\s*(\d+)\s*(?:months?|installments?|years?)?', text, re.IGNORECASE)
    if tenure_match:
        data['total_installments'] = int(tenure_match.group(1))
    else:
        data['total_installments'] = 0

    # Maturity value
    data['maturity_value'] = _find_amount(text, [
        r'(?:maturity\s*(?:value|amount|benefit))\s*[:\-]?\s*(?:Rs\.?|₹|INR)?\s*([\d,]+(?:\.\d+)?)',
        r'(?:face\s*value|bond\s*value|redemption\s*value)\s*[:\-]?\s*(?:Rs\.?|₹|INR)?\s*([\d,]+(?:\.\d+)?)',
    ])

    # Bonus
    data['bonus_benefit'] = _find_text(text, [
        r'(?:bonus|benefit|reward|free\s*(?:month|gold|silver)|interest\s*rate)\s*[:\-]?\s*(.+?)(?:\n|$)',
    ])

    # Dates
    data['start_date'] = _find_date(text, [
        r'(?:start\s*date|commencement|date\s*of\s*issue|investment\s*date|opening\s*date)\s*[:\-]?\s*(\d{1,2}[\s/\-\.]\w{2,9}[\s/\-\.]\d{2,4})',
    ])
    data['maturity_date'] = _find_date(text, [
        r'(?:maturity\s*date|end\s*date|expiry\s*date|closing\s*date)\s*[:\-]?\s*(\d{1,2}[\s/\-\.]\w{2,9}[\s/\-\.]\d{2,4})',
    ])

    fields_found = sum(1 for v in data.values() if v)
    if fields_found == 0:
        return {'success': False, 'message': 'Could not detect scheme information. Please use "Paste Text" or fill in details manually.', 'data': {}, 'needs_text_input': True}

    if fields_found <= 2:
        return {
            'success': True,
            'message': f'Only detected {fields_found} field(s). The document may not have been read properly. Please verify the data or use "Paste Text" for better results.',
            'data': data,
            'raw_text_preview': text[:500],
            'low_confidence': True
        }

    return {
        'success': True,
        'message': f'Detected {fields_found} fields from document. Please verify and complete the form.',
        'data': data,
        'raw_text_preview': text[:500]
    }
