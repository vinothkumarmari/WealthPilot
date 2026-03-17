"""Quick test for doc_parser"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.doc_parser import (
    _detect_provider, _detect_policy_type, _find_amount, 
    _detect_frequency, _find_text, _find_date,
    parse_policy_document, extract_text_from_pdf
)

# Check libraries
try:
    import pytesseract
    print('pytesseract: AVAILABLE')
except ImportError:
    print('pytesseract: NOT INSTALLED (image OCR disabled)')

try:
    import pdfplumber
    print('pdfplumber: AVAILABLE')
except ImportError:
    print('pdfplumber: NOT INSTALLED')

# Test regex parsing on sample policy text
test_text = """
TATA AIA Life Insurance Company Limited
Policy Document

Policy Number: U172839201
Plan Name: TATA AIA Fortune Guarantee Plus
Policy Holder: Vinoth Kumar
Sum Assured: Rs. 50,00,000
Premium Amount: Rs. 25,000
Premium Frequency: Yearly
Commencement Date: 15/03/2024
Maturity Date: 15/03/2044
Nominee: Priya Kumar
"""

print('\n--- Testing Policy Parser ---')
print(f'Provider: "{_detect_provider(test_text, ["TATA AIA", "Bajaj Allianz"])}"')
print(f'Policy Type: "{_detect_policy_type(test_text)}"')

# Test amount patterns from parse_policy_document
premium_patterns = [
    r'(?:premium\s*(?:amount)?|installment)\s*[:\-]?\s*(?:Rs\.?|₹|INR)?\s*([\d,]+(?:\.\d+)?)',
]
print(f'Premium: {_find_amount(test_text, premium_patterns)}')

sum_patterns = [
    r'(?:sum\s*assured|life\s*cover|cover\s*amount|death\s*benefit)\s*[:\-]?\s*(?:Rs\.?|₹|INR)?\s*([\d,]+(?:\.\d+)?)',
]
print(f'Sum Assured: {_find_amount(test_text, sum_patterns)}')

name_patterns = [
    r'(?:plan\s*name|policy\s*name|product\s*name|scheme\s*name)\s*[:\-]?\s*(.+?)(?:\n|$)',
]
print(f'Policy Name: "{_find_text(test_text, name_patterns)}"')

num_patterns = [
    r'(?:policy\s*(?:no|number|#)\.?)\s*[:\-]?\s*([A-Z0-9\-/]+)',
]
print(f'Policy Number: "{_find_text(test_text, num_patterns)}"')

date_patterns = [
    r'(?:commencement\s*date|policy\s*(?:start\s*)?date|date\s*of\s*commencement|inception\s*date|risk\s*commencement)\s*[:\-]?\s*(\d{1,2}[\s/\-\.]\w{2,9}[\s/\-\.]\d{2,4})',
]
print(f'Start Date: "{_find_date(test_text, date_patterns)}"')

print(f'Frequency: "{_detect_frequency(test_text)}"')

nominee_patterns = [
    r'(?:nominee\s*(?:name)?)\s*[:\-]?\s*([A-Za-z\s\.]+?)(?:\n|,|$)',
]
print(f'Nominee: "{_find_text(test_text, nominee_patterns)}"')

# Test Indian amount format (with extra comma like 50,00,000)
test_amt = "Sum Assured: Rs. 50,00,000"
print(f'\nIndian format "50,00,000": {_find_amount(test_amt, sum_patterns)}')

# Test ₹ symbol
test_amt2 = "Premium Amount: ₹25,000 per month"
print(f'₹ symbol: {_find_amount(test_amt2, premium_patterns)}')

print('\n--- DONE ---')
