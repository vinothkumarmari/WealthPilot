from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime, timezone

db = SQLAlchemy()


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    full_name = db.Column(db.String(150))
    mobile = db.Column(db.String(15))
    age = db.Column(db.Integer)
    monthly_salary = db.Column(db.Float, default=0)
    annual_salary = db.Column(db.Float, default=0)
    risk_appetite = db.Column(db.String(20), default='moderate')  # low, moderate, high
    budget_needs_pct = db.Column(db.Float, default=50)
    budget_wants_pct = db.Column(db.Float, default=30)
    budget_savings_pct = db.Column(db.Float, default=20)
    enable_grocery_offers = db.Column(db.Boolean, default=False)
    enable_future_monthly_reminders = db.Column(db.Boolean, default=True)
    enable_future_quarterly_reminders = db.Column(db.Boolean, default=True)
    enable_only_critical_notifications = db.Column(db.Boolean, default=False)
    profession = db.Column(db.String(100))  # IT, Doctor, Teacher, Farmer, etc.
    state = db.Column(db.String(50))  # Indian state for state-specific schemes
    language = db.Column(db.String(5), default='en')  # en, ta, hi, te
    is_admin = db.Column(db.Boolean, default=False)
    is_verified = db.Column(db.Boolean, default=False)
    otp_code = db.Column(db.String(10))
    otp_expiry = db.Column(db.DateTime)
    failed_login_count = db.Column(db.Integer, default=0)
    locked_until = db.Column(db.DateTime)
    last_activity = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    
    # Relationships
    incomes = db.relationship('Income', backref='user', lazy=True, cascade='all, delete-orphan')
    expenses = db.relationship('Expense', backref='user', lazy=True, cascade='all, delete-orphan')
    investments = db.relationship('Investment', backref='user', lazy=True, cascade='all, delete-orphan')
    assets = db.relationship('Asset', backref='user', lazy=True, cascade='all, delete-orphan')
    policies = db.relationship('InsurancePolicy', backref='user', lazy=True, cascade='all, delete-orphan')
    schemes = db.relationship('Scheme', backref='user', lazy=True, cascade='all, delete-orphan')
    goals = db.relationship('FinancialGoal', backref='user', lazy=True, cascade='all, delete-orphan')
    sips = db.relationship('SIP', backref='user', lazy=True, cascade='all, delete-orphan')
    budgets = db.relationship('Budget', backref='user', lazy=True, cascade='all, delete-orphan')
    loans = db.relationship('Loan', backref='user', lazy=True, cascade='all, delete-orphan')
    bank_accounts = db.relationship('BankAccount', backref='user', lazy=True, cascade='all, delete-orphan')
    provident_funds = db.relationship('ProvidentFund', backref='user', lazy=True, cascade='all, delete-orphan')
    feedbacks = db.relationship('Feedback', backref='user', lazy=True, cascade='all, delete-orphan')
    notifications = db.relationship('Notification', backref='user', lazy=True, cascade='all, delete-orphan')


class Income(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    source = db.Column(db.String(100), nullable=False)
    income_type = db.Column(db.String(50), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    frequency = db.Column(db.String(20), default='monthly')  # monthly, annual, one-time
    date = db.Column(db.Date, default=lambda: datetime.now(timezone.utc).date())
    description = db.Column(db.String(300))
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))


class Expense(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    date = db.Column(db.Date, default=lambda: datetime.now(timezone.utc).date())
    description = db.Column(db.String(300))
    is_recurring = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))


class Investment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    investment_type = db.Column(db.String(50), nullable=False)  # FD, RD, MF, Stocks, Gold, Silver, PPF, NPS, etc.
    platform = db.Column(db.String(100))  # Groww, Zerodha, SBI, etc.
    name = db.Column(db.String(150), nullable=False)
    amount_invested = db.Column(db.Float, nullable=False)
    current_value = db.Column(db.Float, default=0)
    expected_return_rate = db.Column(db.Float, default=0)
    start_date = db.Column(db.Date)
    maturity_date = db.Column(db.Date)
    is_active = db.Column(db.Boolean, default=True)
    member = db.Column(db.String(100), default='Self')  # family member
    notes = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))


class Asset(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    asset_type = db.Column(db.String(50), nullable=False)
    name = db.Column(db.String(150), nullable=False)
    purchase_price = db.Column(db.Float, nullable=False)
    current_value = db.Column(db.Float, default=0)
    purchase_date = db.Column(db.Date)
    emi_amount = db.Column(db.Float, default=0)
    emi_remaining_months = db.Column(db.Integer, default=0)
    loan_amount = db.Column(db.Float, default=0)
    notes = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))


class InsurancePolicy(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    policy_type = db.Column(db.String(50), nullable=False)  # Life, Term, Health, ULIP, Endowment, etc.
    provider = db.Column(db.String(100), nullable=False)  # TATA AIA, AXIS Max Life, Bajaj Allianz, LIC, etc.
    policy_name = db.Column(db.String(200), nullable=False)
    policy_number = db.Column(db.String(100))
    sum_assured = db.Column(db.Float, default=0)
    premium_amount = db.Column(db.Float, nullable=False)
    premium_frequency = db.Column(db.String(20), default='monthly')  # monthly, quarterly, half-yearly, yearly
    premium_due_day = db.Column(db.Integer, default=0)  # day of month the premium is due (1-31)
    start_date = db.Column(db.Date)
    maturity_date = db.Column(db.Date)
    nominee = db.Column(db.String(150))
    member = db.Column(db.String(100), default='Self')  # family member
    status = db.Column(db.String(20), default='active')  # active, matured, surrendered, lapsed
    total_paid = db.Column(db.Float, default=0)
    maturity_value = db.Column(db.Float, default=0)
    notes = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    payments = db.relationship('PremiumPayment', backref='policy', lazy=True, cascade='all, delete-orphan')


class PremiumPayment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    policy_id = db.Column(db.Integer, db.ForeignKey('insurance_policy.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    payment_date = db.Column(db.Date, nullable=False)
    note = db.Column(db.String(200))
    expense_id = db.Column(db.Integer, db.ForeignKey('expense.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))


class Scheme(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    scheme_type = db.Column(db.String(50), nullable=False)  # Gold Scheme, Chit Fund, RD, Bonds, etc.
    provider = db.Column(db.String(100), nullable=False)  # Jeweler name, Bank, NBFC, etc.
    scheme_name = db.Column(db.String(200), nullable=False)
    installment_amount = db.Column(db.Float, nullable=False)
    installment_frequency = db.Column(db.String(20), default='monthly')
    total_installments = db.Column(db.Integer, default=0)
    paid_installments = db.Column(db.Integer, default=0)
    total_paid = db.Column(db.Float, default=0)
    maturity_value = db.Column(db.Float, default=0)
    bonus_benefit = db.Column(db.String(200))  # e.g. "1 month free gold", "5% bonus"
    start_date = db.Column(db.Date)
    maturity_date = db.Column(db.Date)
    member = db.Column(db.String(100), default='Self')  # family member
    status = db.Column(db.String(20), default='active')  # active, completed, cancelled
    notes = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))


class FinancialGoal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    goal_name = db.Column(db.String(150), nullable=False)
    target_amount = db.Column(db.Float, nullable=False)
    current_saved = db.Column(db.Float, default=0)
    target_date = db.Column(db.Date)
    priority = db.Column(db.String(20), default='medium')  # low, medium, high
    category = db.Column(db.String(50))  # house, car, education, retirement, etc.
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))


class SIP(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    fund_name = db.Column(db.String(200), nullable=False)
    platform = db.Column(db.String(100))  # Groww, Zerodha, etc.
    sip_amount = db.Column(db.Float, nullable=False)
    frequency = db.Column(db.String(20), default='monthly')
    sip_date = db.Column(db.Integer, default=1)  # day of month
    start_date = db.Column(db.Date)
    expected_return = db.Column(db.Float, default=12.0)
    total_invested = db.Column(db.Float, default=0)
    current_value = db.Column(db.Float, default=0)
    member = db.Column(db.String(100), default='Self')
    is_active = db.Column(db.Boolean, default=True)
    notes = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))


class Budget(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    month = db.Column(db.String(7), nullable=False)  # YYYY-MM format
    category = db.Column(db.String(50), nullable=False)
    planned_amount = db.Column(db.Float, default=0)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))


class Loan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    loan_type = db.Column(db.String(50), nullable=False)  # Home, Car, Personal, Education, Credit Card, Gold, Two Wheeler
    lender = db.Column(db.String(150), nullable=False)  # Bank/NBFC name
    loan_name = db.Column(db.String(150), nullable=False)
    principal_amount = db.Column(db.Float, nullable=False)
    interest_rate = db.Column(db.Float, nullable=False)  # Annual %
    tenure_months = db.Column(db.Integer, nullable=False)
    emi_amount = db.Column(db.Float, nullable=False)
    paid_months = db.Column(db.Integer, default=0)
    total_paid = db.Column(db.Float, default=0)
    outstanding_balance = db.Column(db.Float, default=0)
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)
    emi_day = db.Column(db.Integer, default=5)  # Day of month EMI is deducted
    is_active = db.Column(db.Boolean, default=True)
    notes = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))


class BankAccount(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    bank_name = db.Column(db.String(150), nullable=False)
    account_type = db.Column(db.String(50), nullable=False)  # Savings, Current, Salary, FD, RD
    account_number_last4 = db.Column(db.String(4))  # last 4 digits only for security
    balance = db.Column(db.Float, default=0)
    interest_rate = db.Column(db.Float, default=0)  # annual %
    notes = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))


class ProvidentFund(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    pf_type = db.Column(db.String(20), nullable=False)  # EPF, VPF, GPF
    uan_number = db.Column(db.String(20))
    employer = db.Column(db.String(150))
    employee_contribution = db.Column(db.Float, default=0)  # monthly
    employer_contribution = db.Column(db.Float, default=0)  # monthly
    total_balance = db.Column(db.Float, default=0)
    interest_rate = db.Column(db.Float, default=8.25)  # current EPF rate
    start_date = db.Column(db.Date)
    notes = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))


class Feedback(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)  # 1-5 stars
    category = db.Column(db.String(50), default='General')  # General, UI, Features, Bug, Suggestion
    message = db.Column(db.String(1000), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))


class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.String(500), nullable=False)
    category = db.Column(db.String(50), default='info')  # info, warning, success, danger
    icon = db.Column(db.String(50), default='notifications')
    is_read = db.Column(db.Boolean, default=False)
    link = db.Column(db.String(200))  # optional URL to navigate to
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))


class PaymentTransaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    plan_code = db.Column(db.String(20), nullable=False)  # pro_monthly, family_monthly
    amount = db.Column(db.Integer, nullable=False)  # paise
    currency = db.Column(db.String(10), default='INR')
    status = db.Column(db.String(20), default='created')  # created, paid, failed
    razorpay_order_id = db.Column(db.String(80), unique=True)
    razorpay_payment_id = db.Column(db.String(80), unique=True)
    razorpay_signature = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    paid_at = db.Column(db.DateTime)
