import os
import secrets
from datetime import timedelta


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or secrets.token_hex(32)
    WTF_CSRF_ENABLED = True
    
    # Session Configuration
    SESSION_PERMANENT = True
    PERMANENT_SESSION_LIFETIME = timedelta(hours=2)
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SECURE = os.environ.get('FLASK_ENV') == 'production'
    SESSION_COOKIE_SAMESITE = 'Lax'
    SESSION_REFRESH_EACH_REQUEST = True
    
    # Idle timeout (in seconds) — logged out after 30 min inactivity
    SESSION_IDLE_TIMEOUT = int(os.environ.get('SESSION_IDLE_TIMEOUT', 1800))
    
    # Account lockout
    MAX_FAILED_LOGINS = 5
    ACCOUNT_LOCKOUT_MINUTES = 15
    
    # Database Configuration
    DB_NAME = 'Vnit'
    DB_PASSWORD = os.environ.get('DB_PASSWORD', '')
    _db_url = os.environ.get('DATABASE_URL', f'sqlite:///{DB_NAME}.db')
    # Render.com provides postgres:// — convert to postgresql+psycopg:// for SQLAlchemy + psycopg3
    if _db_url.startswith('postgres://'):
        _db_url = _db_url.replace('postgres://', 'postgresql+psycopg://', 1)
    elif _db_url.startswith('postgresql://'):
        _db_url = _db_url.replace('postgresql://', 'postgresql+psycopg://', 1)
    SQLALCHEMY_DATABASE_URI = _db_url
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 180,
    }
    
    # App Port
    APP_PORT = int(os.environ.get('PORT', 7777))

    # File Upload
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB max
    ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'bmp', 'tiff', 'webp'}
    
    # Admin Configuration (MUST be set via env vars in production)
    ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME', 'admin')
    ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', secrets.token_urlsafe(24))
    ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL', 'admin@wealthpilot.com')
    ADMIN_FULL_NAME = os.environ.get('ADMIN_FULL_NAME', 'Vinoth - Founder & CEO')
    
    # Email / SMTP Configuration for OTP
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME', '')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD', '')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER', 'noreply@wealthpilot.com')

    # Payments (Razorpay)
    RAZORPAY_KEY_ID = os.environ.get('RAZORPAY_KEY_ID', '')
    RAZORPAY_KEY_SECRET = os.environ.get('RAZORPAY_KEY_SECRET', '')
    RAZORPAY_WEBHOOK_SECRET = os.environ.get('RAZORPAY_WEBHOOK_SECRET', '')
    RAZORPAY_CURRENCY = 'INR'
    
    # App Version (for cache busting static assets)
    APP_VERSION = os.environ.get('APP_VERSION', '7')

    # OTP Settings
    OTP_EXPIRY_MINUTES = 3
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
