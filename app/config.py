import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'VnIT-M0n3y-MaNaG3r-S3cR3t-K3y-2026')
    
    # Database Configuration
    DB_NAME = 'Vnit'
    DB_PASSWORD = os.environ.get('DB_PASSWORD', 'Vinith@45')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', f'sqlite:///{DB_NAME}.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # App Port
    APP_PORT = 7777

    # File Upload
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB max
    ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'bmp', 'tiff', 'webp'}
    
    # Admin Configuration
    ADMIN_USERNAME = 'vinoth'
    ADMIN_PASSWORD = 'Auto@360'
    ADMIN_EMAIL = 'admin@wealthpilot.com'
    ADMIN_FULL_NAME = 'Vinoth - Founder & CEO'
    
    # Email / SMTP Configuration for OTP
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME', '')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD', '')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER', 'noreply@wealthpilot.com')
    
    # OTP Settings
    OTP_EXPIRY_MINUTES = 5
    OTP_LENGTH = 6
    
    # Investment rates (default Indian market rates - configurable)
    FD_RATE = 7.0
    RD_RATE = 6.5
    PPF_RATE = 7.1
    EPF_RATE = 8.25
    NPS_RATE = 10.0
    GOLD_ANNUAL_RETURN = 8.0
    SILVER_ANNUAL_RETURN = 6.0
    MUTUAL_FUND_RETURN = 12.0
    STOCK_MARKET_RETURN = 14.0
    REAL_ESTATE_RETURN = 9.0
    
    # Inflation rate
    INFLATION_RATE = 6.0
    
    # Asset categories
    ASSET_CATEGORIES = [
        'Car', 'Bike', 'House', 'Flat', 'Land', 
        'Farming Land', 'Gold Jewelry', 'Electronics', 'Other'
    ]
    
    EXPENSE_CATEGORIES = [
        'Housing', 'Food & Groceries', 'Transportation', 'Utilities',
        'Healthcare', 'Insurance', 'Education', 'Entertainment',
        'Shopping', 'Personal Care', 'Debt Payments', 'Savings',
        'Investments', 'Charity', 'Miscellaneous'
    ]
    
    INCOME_TYPES = [
        'Salary', 'Freelance', 'Business', 'Rental Income',
        'Investment Returns', 'Dividends', 'Interest', 'Other'
    ]

    INSURANCE_PROVIDERS = [
        'TATA AIA', 'AXIS Max Life', 'Bajaj Allianz', 'LIC', 'HDFC Life',
        'SBI Life', 'ICICI Prudential', 'Kotak Life', 'Max Bupa',
        'Star Health', 'Niva Bupa', 'Aditya Birla Health', 'PNB MetLife',
        'Canara HSBC', 'Edelweiss Tokio', 'Aegon Life', 'Aviva',
        'Policy Bazaar', 'Other'
    ]

    POLICY_TYPES = [
        'Term Life', 'Whole Life', 'Endowment', 'ULIP', 'Money Back',
        'Health Insurance', 'Critical Illness', 'Accident Cover',
        'Child Plan', 'Pension Plan', 'Group Insurance', 'Other'
    ]

    SCHEME_TYPES = [
        'Gold Scheme', 'Silver Scheme', 'Chit Fund', 'Recurring Deposit',
        'Bonds', 'Government Bonds', 'Corporate Bonds', 'Post Office Scheme',
        'Sovereign Gold Bond', 'Kisan Vikas Patra', 'NSC',
        'Sukanya Samriddhi', 'Senior Citizen Scheme', 'Other'
    ]
