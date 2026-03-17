import sys, os
sys.path.insert(0, r'D:\vinoth\money_manager')
from app.doc_parser import parse_policy_document
from app.config import Config

pdfs = [
    (r'D:\vinoth\Shared_mail_box_testcases\Policy_759285920_3529163331139.pdf', 'Bajaj Smart Wealth'),
    (r'D:\vinoth\Shared_mail_box_testcases\Policy_575832080_3529163331139.pdf', 'MaxLife Online Savings'),
    (r'C:\Users\vinoth-15463\Downloads\Policy_524798632_3529163331139.pdf', 'Fortune Pro'),
    (r'C:\Users\vinoth-15463\Downloads\Policy_Information_Page.pdf', 'Smart Value Income'),
    (r'C:\Users\vinoth-15463\Downloads\Policy_575839855_3529163331139.pdf', 'MaxLife Assured Wealth'),
]
for pdf, label in pdfs:
    if not os.path.exists(pdf):
        print(f'SKIP: {label}')
        continue
    result = parse_policy_document(pdf, Config.INSURANCE_PROVIDERS)
    d = result.get('data', {})
    print(f'{label}: premium={d.get("premium_amount")}/{d.get("premium_frequency")} SA={d.get("sum_assured")}')
