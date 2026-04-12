"""
WealthPilot - All Routes (Blueprint)
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session, send_from_directory
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timezone, date, timedelta
from dateutil.relativedelta import relativedelta
from functools import wraps
from .models import db, User, Income, Expense, Investment, Asset, FinancialGoal, InsurancePolicy, Scheme, PremiumPayment, SIP, Budget, Loan, BankAccount, ProvidentFund, Feedback, Notification
from .ml_engine import FinancialAdvisor
from .config import Config
from . import limiter, csrf
from sqlalchemy import or_
from sqlalchemy.exc import OperationalError
import json
import re
import os
import io
import csv
import secrets
import hmac
import hashlib
import requests
from werkzeug.utils import secure_filename

main = Blueprint('main', __name__)
advisor = FinancialAdvisor()


# ======================== PWA SERVICE WORKER ========================

@main.route('/sw.js')
def service_worker():
    return send_from_directory(main.static_folder or 'static', 'sw.js', mimetype='application/javascript')


# ======================== MAIL CONFIG HELPERS ========================

MAIL_CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'instance', 'mail_config.json')

def load_mail_config():
    """Load SMTP settings: JSON file first, then env vars, then empty."""
    # Try JSON file first
    if os.path.exists(MAIL_CONFIG_PATH):
        with open(MAIL_CONFIG_PATH, 'r') as f:
            cfg = json.load(f)
        if cfg.get('mail_username'):
            return cfg
    # Fall back to environment variables (Render / production)
    env_username = os.environ.get('MAIL_USERNAME', '')
    if env_username:
        return {
            'mail_server': os.environ.get('MAIL_SERVER', 'smtp.gmail.com'),
            'mail_port': int(os.environ.get('MAIL_PORT', 587)),
            'mail_use_tls': True,
            'mail_username': env_username,
            'mail_password': os.environ.get('MAIL_PASSWORD', ''),
            'mail_default_sender': os.environ.get('MAIL_DEFAULT_SENDER', env_username),
        }
    return {}

def save_mail_config(config_dict):
    """Save SMTP settings to JSON file."""
    os.makedirs(os.path.dirname(MAIL_CONFIG_PATH), exist_ok=True)
    with open(MAIL_CONFIG_PATH, 'w') as f:
        json.dump(config_dict, f, indent=2)

def apply_mail_config(app):
    """Apply saved mail config to Flask app and reinitialize Flask-Mail."""
    from app import mail
    cfg = load_mail_config()
    if cfg.get('mail_username'):
        app.config['MAIL_SERVER'] = cfg.get('mail_server', 'smtp.gmail.com')
        app.config['MAIL_PORT'] = int(cfg.get('mail_port', 587))
        app.config['MAIL_USE_TLS'] = cfg.get('mail_use_tls', True)
        app.config['MAIL_USERNAME'] = cfg['mail_username']
        app.config['MAIL_PASSWORD'] = cfg.get('mail_password', '')
        app.config['MAIL_USE_SSL'] = False
        app.config['MAIL_DEFAULT_SENDER'] = cfg.get('mail_default_sender', cfg['mail_username'])
        mail.init_app(app)


# ======================== HELPERS ========================

def validate_email(email):
    """Validate email format."""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def validate_mobile(mobile):
    """Validate mobile number (Indian 10-digit or international with country code)."""
    pattern = r'^(\+?\d{1,3}[-.\s]?)?\d{10}$'
    return re.match(pattern, mobile) is not None


def generate_otp():
    """Generate a secure numeric OTP."""
    return ''.join([str(secrets.randbelow(10)) for _ in range(Config.OTP_LENGTH)])


def send_otp_email(user_email, otp_code):
    """Send OTP via email. Falls back to flash message if SMTP not configured."""
    from flask import current_app
    from app import mail
    from flask_mail import Message
    try:
        # Apply saved mail config if not already loaded
        cfg = load_mail_config()
        if cfg.get('mail_username'):
            apply_mail_config(current_app._get_current_object())

        username = current_app.config.get('MAIL_USERNAME', '')
        if not username:
            current_app.logger.warning('SMTP not configured: MAIL_USERNAME is empty')
            return False

        # Use the authenticated username as sender (Gmail requires this)
        sender = current_app.config.get('MAIL_DEFAULT_SENDER', username)
        msg = Message(
            subject='WealthPilot - Email Verification OTP',
            sender=sender,
            recipients=[user_email],
            body=f'Your OTP for WealthPilot registration is: {otp_code}\n'
                 f'This code expires in {Config.OTP_EXPIRY_MINUTES} minutes.\n'
                 f'Do not share this code with anyone.'
        )
        current_app.logger.info(f'Sending OTP email to {user_email} via {current_app.config.get("MAIL_SERVER")}:{current_app.config.get("MAIL_PORT")} as {sender}')
        mail.send(msg)
        current_app.logger.info(f'OTP email sent successfully to {user_email}')
        return True
    except Exception as e:
        current_app.logger.error(f'Failed to send OTP email to {user_email}: {e}')
        print(f'[MAIL ERROR] Failed to send email to {user_email}: {e}')
    return False


def admin_required(f):
    """Decorator to restrict routes to admin users only."""
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if not current_user.is_admin:
            flash('Admin access required.', 'danger')
            return redirect(url_for('main.dashboard'))
        return f(*args, **kwargs)
    return decorated_function


def _sync_user_salary(user):
    """Auto-update user's monthly/annual salary from Salary-type income records."""
    salary_total = db.session.query(db.func.sum(Income.amount)).filter_by(
        user_id=user.id, income_type='Salary'
    ).scalar() or 0
    salary_count = Income.query.filter_by(user_id=user.id, income_type='Salary').count()
    if salary_count > 0:
        user.monthly_salary = salary_total / salary_count
        user.annual_salary = user.monthly_salary * 12
    else:
        user.monthly_salary = 0
        user.annual_salary = 0


# ======================== AUTH ROUTES ========================

@main.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    return render_template('landing.html')


@main.route('/pricing')
def pricing():
    return render_template('pricing.html')


@main.route('/register', methods=['GET', 'POST'])
@limiter.limit('10 per minute')
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip().lower()
        mobile = request.form.get('mobile', '').strip()
        password = request.form.get('password', '')
        full_name = request.form.get('full_name', '').strip()
        age = request.form.get('age', type=int)
        monthly_salary = request.form.get('monthly_salary', 0, type=float)

        if not username or not email or not password:
            flash('Username, email, and password are required.', 'danger')
            return render_template('register.html')

        # Validate email format
        if not validate_email(email):
            flash('Please enter a valid email address.', 'danger')
            return render_template('register.html')

        # Validate mobile number
        if mobile and not validate_mobile(mobile):
            flash('Please enter a valid mobile number (10 digits).', 'danger')
            return render_template('register.html')

        # Password strength check
        if len(password) < 8:
            flash('Password must be at least 8 characters.', 'danger')
            return render_template('register.html')
        if not re.search(r'[A-Z]', password):
            flash('Password must contain at least one uppercase letter.', 'danger')
            return render_template('register.html')
        if not re.search(r'[0-9]', password):
            flash('Password must contain at least one number.', 'danger')
            return render_template('register.html')

        lookup_username = username.lower()
        existing = User.query.filter(
            (db.func.lower(User.username) == lookup_username) | (db.func.lower(User.email) == email)
        ).first()
        if existing:
            if not existing.is_verified:
                # Unverified user — update credentials and resend OTP
                existing.username = username
                existing.email = email
                existing.password_hash = generate_password_hash(password)
                existing.full_name = full_name
                existing.mobile = mobile
                existing.age = age
                existing.monthly_salary = monthly_salary
                existing.annual_salary = monthly_salary * 12
                existing.risk_appetite = request.form.get('risk_appetite', 'moderate')
                otp = generate_otp()
                existing.otp_code = otp
                existing.otp_expiry = datetime.now(timezone.utc) + timedelta(minutes=Config.OTP_EXPIRY_MINUTES)
                db.session.commit()
                session['pending_user_id'] = existing.id
                email_sent = send_otp_email(email, otp)
                if email_sent:
                    flash('Account already registered but not verified. New OTP sent to your email.', 'info')
                else:
                    flash('OTP generated but email could not be sent. Please ask admin to configure SMTP settings.', 'danger')
                return redirect(url_for('main.verify_otp'))
            else:
                flash('Username or email already registered. Please login with your credentials.', 'danger')
                return render_template('register.html')

        # Generate OTP and create new unverified user
        otp = generate_otp()
        user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password),
            full_name=full_name,
            mobile=mobile,
            age=age,
            monthly_salary=monthly_salary,
            annual_salary=monthly_salary * 12,
            risk_appetite=request.form.get('risk_appetite', 'moderate'),
            is_verified=False,
            otp_code=otp,
            otp_expiry=datetime.now(timezone.utc) + timedelta(minutes=Config.OTP_EXPIRY_MINUTES)
        )
        db.session.add(user)
        db.session.commit()

        # Send OTP email
        email_sent = send_otp_email(email, otp)
        session['pending_user_id'] = user.id

        if email_sent:
            flash(f'OTP sent to {email}. Please verify your email.', 'info')
        else:
            flash('OTP generated but email could not be sent. Please ask admin to configure SMTP settings.', 'danger')

        return redirect(url_for('main.verify_otp'))
    return render_template('register.html')


@main.route('/verify-otp', methods=['GET', 'POST'])
def verify_otp():
    user_id = session.get('pending_user_id')
    if not user_id:
        flash('No pending verification. Please register first.', 'danger')
        return redirect(url_for('main.register'))

    user = db.session.get(User, user_id)
    if not user:
        session.pop('pending_user_id', None)
        flash('User not found. Please register again.', 'danger')
        return redirect(url_for('main.register'))

    if request.method == 'POST':
        entered_otp = request.form.get('otp', '').strip()

        if not entered_otp:
            flash('Please enter the OTP.', 'danger')
            return render_template('verify_otp.html', email=user.email)

        # Check OTP validity
        if user.otp_code != entered_otp:
            flash('Invalid OTP. Please try again.', 'danger')
            return render_template('verify_otp.html', email=user.email)

        if user.otp_expiry and user.otp_expiry.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
            flash('OTP has expired. Please request a new one.', 'danger')
            return render_template('verify_otp.html', email=user.email)

        # Verify user
        user.is_verified = True
        user.otp_code = None
        user.otp_expiry = None
        db.session.commit()

        session.pop('pending_user_id', None)
        login_user(user)
        flash('Email verified! Account created successfully!', 'success')
        return redirect(url_for('main.dashboard'))

    return render_template('verify_otp.html', email=user.email)


@main.route('/resend-otp')
@limiter.limit('3 per minute')
def resend_otp():
    user_id = session.get('pending_user_id')
    if not user_id:
        flash('No pending verification.', 'danger')
        return redirect(url_for('main.register'))

    user = db.session.get(User, user_id)
    if not user:
        session.pop('pending_user_id', None)
        return redirect(url_for('main.register'))

    otp = generate_otp()
    user.otp_code = otp
    user.otp_expiry = datetime.now(timezone.utc) + timedelta(minutes=Config.OTP_EXPIRY_MINUTES)
    db.session.commit()

    email_sent = send_otp_email(user.email, otp)
    if email_sent:
        flash(f'New OTP sent to {user.email}.', 'info')
    else:
        flash('OTP generated but email could not be sent. Please ask admin to configure SMTP settings.', 'danger')

    return redirect(url_for('main.verify_otp'))


@main.route('/login', methods=['GET', 'POST'])
@limiter.limit('10 per minute')
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        lookup = username.lower()
        user = User.query.filter(
            or_(db.func.lower(User.username) == lookup, db.func.lower(User.email) == lookup)
        ).first()
        
        if user:
            # Check account lockout
            now_utc = datetime.now(timezone.utc)
            locked_until = user.locked_until
            if locked_until and locked_until.tzinfo is None:
                locked_until = locked_until.replace(tzinfo=timezone.utc)
            if locked_until and locked_until > now_utc:
                remaining = int((locked_until - now_utc).total_seconds() / 60) + 1
                flash(f'Account locked due to too many failed attempts. Try again in {remaining} minute(s).', 'danger')
                return render_template('login.html')
            
            if check_password_hash(user.password_hash, password):
                # Reset failed attempts on success
                user.failed_login_count = 0
                user.locked_until = None
                db.session.commit()
                
                if not user.is_verified:
                    otp = generate_otp()
                    user.otp_code = otp
                    user.otp_expiry = datetime.now(timezone.utc) + timedelta(minutes=Config.OTP_EXPIRY_MINUTES)
                    db.session.commit()
                    session['pending_user_id'] = user.id
                    email_sent = send_otp_email(user.email, otp)
                    if email_sent:
                        flash('Email not verified. New OTP sent to your email.', 'warning')
                    else:
                        flash('Email not verified. OTP generated but email could not be sent. Please ask admin to configure SMTP settings.', 'danger')
                    return redirect(url_for('main.verify_otp'))
                login_user(user, remember=request.form.get('remember'))
                session['_last_activity'] = datetime.now(timezone.utc).isoformat()
                flash('Login successful!', 'success')
                return redirect(url_for('main.dashboard'))
            else:
                # Increment failed login count
                user.failed_login_count = (user.failed_login_count or 0) + 1
                if user.failed_login_count >= Config.MAX_FAILED_LOGINS:
                    user.locked_until = datetime.now(timezone.utc) + timedelta(minutes=Config.ACCOUNT_LOCKOUT_MINUTES)
                    db.session.commit()
                    flash(f'Account locked for {Config.ACCOUNT_LOCKOUT_MINUTES} minutes due to {Config.MAX_FAILED_LOGINS} failed attempts.', 'danger')
                    return render_template('login.html')
                db.session.commit()
        flash('Invalid credentials.', 'danger')
    return render_template('login.html')


# ======================== BILLING & PAYMENTS ========================

PLAN_PRICING = {
    'pro_monthly': {'amount_paise': 9900, 'name': 'WealthPilot Pro (Monthly)'},
    'family_monthly': {'amount_paise': 19900, 'name': 'WealthPilot Family (Monthly)'},
}


@main.route('/billing/create-order', methods=['POST'])
@login_required
def create_billing_order():
    if not Config.RAZORPAY_KEY_ID or not Config.RAZORPAY_KEY_SECRET:
        return jsonify({'success': False, 'message': 'Payment gateway is not configured.'}), 503

    plan_code = request.form.get('plan_code', '').strip()
    plan = PLAN_PRICING.get(plan_code)
    if not plan:
        return jsonify({'success': False, 'message': 'Invalid plan selected.'}), 400

    payload = {
        'amount': plan['amount_paise'],
        'currency': Config.RAZORPAY_CURRENCY,
        'receipt': f'wp_{current_user.id}_{secrets.token_hex(6)}',
        'notes': {
            'user_id': str(current_user.id),
            'plan_code': plan_code,
            'email': current_user.email,
        }
    }
    try:
        resp = requests.post(
            'https://api.razorpay.com/v1/orders',
            auth=(Config.RAZORPAY_KEY_ID, Config.RAZORPAY_KEY_SECRET),
            json=payload,
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()

        from .models import PaymentTransaction
        txn = PaymentTransaction(
            user_id=current_user.id,
            plan_code=plan_code,
            amount=plan['amount_paise'],
            currency=Config.RAZORPAY_CURRENCY,
            status='created',
            razorpay_order_id=data.get('id')
        )
        db.session.add(txn)
        db.session.commit()

        return jsonify({
            'success': True,
            'key': Config.RAZORPAY_KEY_ID,
            'order_id': data.get('id'),
            'amount': plan['amount_paise'],
            'currency': Config.RAZORPAY_CURRENCY,
            'plan_name': plan['name'],
            'user_name': current_user.full_name or current_user.username,
            'user_email': current_user.email,
        })
    except Exception as e:
        return jsonify({'success': False, 'message': f'Unable to create payment order: {e}'}), 502


@main.route('/billing/verify', methods=['POST'])
@login_required
def verify_billing_payment():
    if not Config.RAZORPAY_KEY_SECRET:
        return jsonify({'success': False, 'message': 'Payment verification is not configured.'}), 503

    order_id = request.form.get('razorpay_order_id', '').strip()
    payment_id = request.form.get('razorpay_payment_id', '').strip()
    signature = request.form.get('razorpay_signature', '').strip()
    if not order_id or not payment_id or not signature:
        return jsonify({'success': False, 'message': 'Missing payment verification fields.'}), 400

    payload = f'{order_id}|{payment_id}'.encode('utf-8')
    expected = hmac.new(
        Config.RAZORPAY_KEY_SECRET.encode('utf-8'), payload, hashlib.sha256
    ).hexdigest()
    if not hmac.compare_digest(expected, signature):
        return jsonify({'success': False, 'message': 'Invalid payment signature.'}), 400

    from .models import PaymentTransaction
    txn = PaymentTransaction.query.filter_by(
        user_id=current_user.id, razorpay_order_id=order_id
    ).first()
    if not txn:
        return jsonify({'success': False, 'message': 'Payment record not found.'}), 404

    txn.razorpay_payment_id = payment_id
    txn.razorpay_signature = signature
    txn.status = 'paid'
    txn.paid_at = datetime.now(timezone.utc)
    db.session.commit()
    return jsonify({'success': True, 'message': 'Payment verified successfully.'})


@main.route('/billing/webhook/razorpay', methods=['POST'])
@csrf.exempt
def razorpay_webhook():
    if not Config.RAZORPAY_WEBHOOK_SECRET:
        return jsonify({'success': False, 'message': 'Webhook secret missing.'}), 503

    body = request.get_data() or b''
    signature = request.headers.get('X-Razorpay-Signature', '')
    expected = hmac.new(
        Config.RAZORPAY_WEBHOOK_SECRET.encode('utf-8'), body, hashlib.sha256
    ).hexdigest()
    if not hmac.compare_digest(expected, signature):
        return jsonify({'success': False, 'message': 'Invalid webhook signature.'}), 400

    event = request.get_json(silent=True) or {}
    if event.get('event') == 'payment.captured':
        payment = (event.get('payload', {}).get('payment', {}) or {}).get('entity', {})
        order_id = payment.get('order_id')
        payment_id = payment.get('id')
        if order_id and payment_id:
            from .models import PaymentTransaction
            txn = PaymentTransaction.query.filter_by(razorpay_order_id=order_id).first()
            if txn and txn.status != 'paid':
                txn.razorpay_payment_id = payment_id
                txn.status = 'paid'
                txn.paid_at = datetime.now(timezone.utc)
                db.session.commit()

    return jsonify({'success': True})


@main.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    # Auto-fill email from username query param
    prefill_email = ''
    uname = request.args.get('username', '').strip()
    if uname:
        lookup = User.query.filter_by(username=uname, is_verified=True).first()
        if lookup:
            prefill_email = lookup.email

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        if not email or not validate_email(email):
            flash('Please enter a valid email address.', 'danger')
            return render_template('forgot_password.html', prefill_email=email)

        user = User.query.filter_by(email=email, is_verified=True).first()
        if not user:
            flash('No verified account found with that email.', 'danger')
            return render_template('forgot_password.html', prefill_email=email)

        otp = generate_otp()
        user.otp_code = otp
        user.otp_expiry = datetime.now(timezone.utc) + timedelta(minutes=Config.OTP_EXPIRY_MINUTES)
        db.session.commit()
        session['reset_user_id'] = user.id

        from flask import current_app
        from flask_mail import Message as MailMessage
        email_sent = False
        try:
            cfg = load_mail_config()
            if cfg.get('mail_username'):
                apply_mail_config(current_app._get_current_object())
            username = current_app.config.get('MAIL_USERNAME', '')
            if username:
                msg = MailMessage(
                    subject='WealthPilot - Password Reset OTP',
                    recipients=[email],
                    body=f'Your OTP for password reset is: {otp}\n'
                         f'This code expires in {Config.OTP_EXPIRY_MINUTES} minutes.\n'
                         f'If you did not request this, ignore this email.'
                )
                mail.send(msg)
                email_sent = True
        except Exception as e:
            current_app.logger.error(f'Failed to send password reset email to {email}: {e}')
            print(f'[MAIL ERROR] Failed to send password reset email to {email}: {e}')

        if email_sent:
            flash(f'OTP sent to {email}. Please check your inbox.', 'info')
        else:
            flash('OTP generated but email could not be sent. Please ask admin to configure SMTP settings.', 'danger')
        return redirect(url_for('main.reset_password'))
    return render_template('forgot_password.html', prefill_email=prefill_email)


@main.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    user_id = session.get('reset_user_id')
    if not user_id:
        flash('Please request a password reset first.', 'danger')
        return redirect(url_for('main.forgot_password'))

    user = db.session.get(User, user_id)
    if not user:
        session.pop('reset_user_id', None)
        flash('User not found.', 'danger')
        return redirect(url_for('main.forgot_password'))

    if request.method == 'POST':
        password = request.form.get('password', '')
        confirm = request.form.get('confirm_password', '')

        # OTP must have been verified via AJAX before submitting
        if not session.get('reset_otp_verified'):
            flash('Please verify the OTP first.', 'danger')
            return render_template('reset_password.html', email=user.email)

        # Validate password
        if len(password) < 8:
            flash('Password must be at least 8 characters.', 'danger')
            return render_template('reset_password.html', email=user.email, otp_verified=True)
        if not re.search(r'[A-Z]', password):
            flash('Password must contain at least one uppercase letter.', 'danger')
            return render_template('reset_password.html', email=user.email, otp_verified=True)
        if not re.search(r'[0-9]', password):
            flash('Password must contain at least one number.', 'danger')
            return render_template('reset_password.html', email=user.email, otp_verified=True)
        if password != confirm:
            flash('Passwords do not match.', 'danger')
            return render_template('reset_password.html', email=user.email, otp_verified=True)

        # All valid — reset password
        user.password_hash = generate_password_hash(password)
        user.otp_code = None
        user.otp_expiry = None
        db.session.commit()
        session.pop('reset_user_id', None)
        session.pop('reset_otp_verified', None)
        flash('Password reset successful! Please login with your new password.', 'success')
        return redirect(url_for('main.login'))

    return render_template('reset_password.html', email=user.email)


@main.route('/verify-reset-otp-ajax', methods=['POST'])
def verify_reset_otp_ajax():
    user_id = session.get('reset_user_id')
    if not user_id:
        return jsonify({'success': False, 'message': 'No reset in progress.'})

    user = db.session.get(User, user_id)
    if not user:
        return jsonify({'success': False, 'message': 'User not found.'})

    data = request.get_json()
    entered_otp = (data.get('otp', '') if data else '').strip()

    if not entered_otp:
        return jsonify({'success': False, 'message': 'Please enter the OTP.'})

    if user.otp_code != entered_otp:
        return jsonify({'success': False, 'message': 'Invalid OTP. Please try again.'})

    if user.otp_expiry and user.otp_expiry.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
        return jsonify({'success': False, 'message': 'OTP has expired. Please request a new one.'})

    # OTP valid — mark verified in session
    session['reset_otp_verified'] = True
    user.otp_code = None
    user.otp_expiry = None
    db.session.commit()
    return jsonify({'success': True, 'message': 'OTP verified! Set your new password.'})


@main.route('/resend-reset-otp')
def resend_reset_otp():
    user_id = session.get('reset_user_id')
    if not user_id:
        flash('No password reset in progress.', 'danger')
        return redirect(url_for('main.forgot_password'))

    user = db.session.get(User, user_id)
    if not user:
        session.pop('reset_user_id', None)
        return redirect(url_for('main.forgot_password'))

    otp = generate_otp()
    user.otp_code = otp
    user.otp_expiry = datetime.now(timezone.utc) + timedelta(minutes=Config.OTP_EXPIRY_MINUTES)
    db.session.commit()

    email_sent = send_otp_email(user.email, otp)
    if email_sent:
        flash(f'New OTP sent to {user.email}.', 'info')
    else:
        flash('OTP generated but email could not be sent. Please ask admin to configure SMTP settings.', 'danger')

    session.pop('reset_otp_verified', None)
    return redirect(url_for('main.reset_password'))


@main.route('/logout')
@login_required
def logout():
    logout_user()
    session.clear()
    flash('Logged out successfully.', 'info')
    return redirect(url_for('main.index'))


# ======================== CHANGE PASSWORD ========================

@main.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    if request.method == 'POST':
        current_pw = request.form.get('current_password', '')
        new_pw = request.form.get('new_password', '')
        confirm_pw = request.form.get('confirm_password', '')
        
        if not check_password_hash(current_user.password_hash, current_pw):
            flash('Current password is incorrect.', 'danger')
            return render_template('change_password.html')
        
        if len(new_pw) < 8:
            flash('New password must be at least 8 characters.', 'danger')
            return render_template('change_password.html')
        if not re.search(r'[A-Z]', new_pw):
            flash('New password must contain at least one uppercase letter.', 'danger')
            return render_template('change_password.html')
        if not re.search(r'[0-9]', new_pw):
            flash('New password must contain at least one number.', 'danger')
            return render_template('change_password.html')
        if new_pw != confirm_pw:
            flash('New passwords do not match.', 'danger')
            return render_template('change_password.html')
        if check_password_hash(current_user.password_hash, new_pw):
            flash('New password must be different from current password.', 'danger')
            return render_template('change_password.html')
        
        current_user.password_hash = generate_password_hash(new_pw)
        db.session.commit()
        flash('Password changed successfully!', 'success')
        return redirect(url_for('main.profile'))
    return render_template('change_password.html')


# ======================== HEALTH CHECK ========================

@main.route('/health')
def health_check():
    try:
        db.session.execute(db.text('SELECT 1'))
        return jsonify({'status': 'healthy', 'database': 'connected'}), 200
    except Exception as e:
        return jsonify({'status': 'unhealthy', 'database': str(e)}), 503


# ======================== DATA EXPORT (CSV) ========================

EXPORT_CONFIG = {
    'income': {
        'model': 'Income',
        'fields': ['source', 'income_type', 'amount', 'frequency', 'date', 'description'],
        'headers': ['Source', 'Type', 'Amount', 'Frequency', 'Date', 'Description'],
    },
    'expenses': {
        'model': 'Expense',
        'fields': ['category', 'amount', 'date', 'description', 'is_recurring'],
        'headers': ['Category', 'Amount', 'Date', 'Description', 'Recurring'],
    },
    'investments': {
        'model': 'Investment',
        'fields': ['investment_type', 'platform', 'name', 'amount_invested', 'current_value', 'expected_return_rate', 'start_date', 'maturity_date', 'is_active', 'member', 'notes'],
        'headers': ['Type', 'Platform', 'Name', 'Invested', 'Current Value', 'Return Rate %', 'Start Date', 'Maturity Date', 'Active', 'Member', 'Notes'],
    },
    'assets': {
        'model': 'Asset',
        'fields': ['asset_type', 'name', 'purchase_price', 'current_value', 'purchase_date', 'emi_amount', 'emi_remaining_months', 'loan_amount', 'notes'],
        'headers': ['Type', 'Name', 'Purchase Price', 'Current Value', 'Purchase Date', 'EMI', 'EMI Months Left', 'Loan Amount', 'Notes'],
    },
    'goals': {
        'model': 'FinancialGoal',
        'fields': ['goal_name', 'target_amount', 'current_saved', 'target_date', 'priority', 'category'],
        'headers': ['Goal', 'Target Amount', 'Current Saved', 'Target Date', 'Priority', 'Category'],
    },
    'policies': {
        'model': 'InsurancePolicy',
        'fields': ['policy_type', 'provider', 'policy_name', 'policy_number', 'sum_assured', 'premium_amount', 'premium_frequency', 'start_date', 'maturity_date', 'nominee', 'member', 'status', 'notes'],
        'headers': ['Type', 'Provider', 'Policy Name', 'Policy No.', 'Sum Assured', 'Premium', 'Frequency', 'Start Date', 'Maturity Date', 'Nominee', 'Member', 'Status', 'Notes'],
    },
    'schemes': {
        'model': 'Scheme',
        'fields': ['scheme_type', 'provider', 'scheme_name', 'installment_amount', 'installment_frequency', 'total_installments', 'paid_installments', 'total_paid', 'maturity_value', 'start_date', 'maturity_date', 'member', 'status', 'notes'],
        'headers': ['Type', 'Provider', 'Scheme Name', 'Installment', 'Frequency', 'Total Installments', 'Paid', 'Total Paid', 'Maturity Value', 'Start Date', 'Maturity Date', 'Member', 'Status', 'Notes'],
    },
    'sips': {
        'model': 'SIP',
        'fields': ['fund_name', 'platform', 'sip_amount', 'frequency', 'sip_date', 'start_date', 'expected_return', 'total_invested', 'current_value', 'member', 'is_active', 'notes'],
        'headers': ['Fund Name', 'Platform', 'SIP Amount', 'Frequency', 'SIP Date', 'Start Date', 'Expected Return %', 'Total Invested', 'Current Value', 'Member', 'Active', 'Notes'],
    },
    'loans': {
        'model': 'Loan',
        'fields': ['loan_type', 'lender', 'loan_name', 'principal_amount', 'interest_rate', 'tenure_months', 'emi_amount', 'paid_months', 'total_paid', 'outstanding_balance', 'start_date', 'end_date', 'is_active', 'notes'],
        'headers': ['Type', 'Lender', 'Loan Name', 'Principal', 'Interest Rate %', 'Tenure (Months)', 'EMI', 'Paid Months', 'Total Paid', 'Outstanding', 'Start Date', 'End Date', 'Active', 'Notes'],
    },
}

@main.route('/export/<data_type>')
@login_required
def export_csv(data_type):
    if data_type not in EXPORT_CONFIG:
        flash('Invalid export type.', 'danger')
        return redirect(url_for('main.dashboard'))

    config = EXPORT_CONFIG[data_type]
    model_class = globals().get(config['model']) or locals().get(config['model'])
    if not model_class:
        # Resolve from models module
        import app.models as m
        model_class = getattr(m, config['model'])

    records = model_class.query.filter_by(user_id=current_user.id).all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(config['headers'])
    for record in records:
        row = []
        for field in config['fields']:
            val = getattr(record, field, '')
            if isinstance(val, (date, datetime)):
                val = val.strftime('%Y-%m-%d')
            elif isinstance(val, bool):
                val = 'Yes' if val else 'No'
            elif val is None:
                val = ''
            row.append(val)
        writer.writerow(row)

    output.seek(0)
    from flask import Response
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={
            'Content-Disposition': f'attachment; filename=wealthpilot_{data_type}_{date.today().isoformat()}.csv'
        }
    )


# ======================== ACCOUNT DELETION ========================

@main.route('/delete-account', methods=['GET', 'POST'])
@login_required
def delete_account():
    flash('Delete account permission has been removed for users. Please contact support for account closure requests.', 'warning')
    return redirect(url_for('main.profile'))


# ======================== DASHBOARD ========================

@main.route('/dashboard')
@login_required
def dashboard():
    # Sync salary from actual income records
    _sync_user_salary(current_user)
    db.session.commit()

    total_income = db.session.query(db.func.sum(Income.amount)).filter_by(user_id=current_user.id).scalar() or 0
    total_expenses = db.session.query(db.func.sum(Expense.amount)).filter_by(user_id=current_user.id).scalar() or 0
    total_investments = db.session.query(db.func.sum(Investment.amount_invested)).filter_by(user_id=current_user.id, is_active=True).scalar() or 0
    total_assets_value = db.session.query(db.func.sum(Asset.current_value)).filter_by(user_id=current_user.id).scalar() or 0
    total_debts = db.session.query(db.func.sum(Asset.loan_amount)).filter_by(user_id=current_user.id).scalar() or 0

    # ---- Policy & Scheme data for sync across tabs ----
    all_policies = InsurancePolicy.query.filter_by(user_id=current_user.id).all()
    active_policies = [p for p in all_policies if p.status == 'active']
    total_policy_paid = sum(p.total_paid or 0 for p in all_policies)
    total_sum_assured = sum(p.sum_assured or 0 for p in active_policies)

    monthly_premiums = 0
    freq_div_map = {'monthly': 1, 'quarterly': 3, 'half-yearly': 6, 'yearly': 12}
    for p in active_policies:
        monthly_premiums += p.premium_amount / freq_div_map.get((p.premium_frequency or '').lower(), 12)

    all_schemes = Scheme.query.filter_by(user_id=current_user.id).all()
    active_schemes = [s for s in all_schemes if s.status == 'active']
    total_scheme_paid = sum(s.total_paid or 0 for s in all_schemes)

    monthly_scheme = 0
    for s in active_schemes:
        monthly_scheme += s.installment_amount / freq_div_map.get((s.installment_frequency or '').lower(), 12)

    # EMI commitments from assets
    all_assets = Asset.query.filter_by(user_id=current_user.id).all()
    total_emi = sum(a.emi_amount or 0 for a in all_assets if (a.emi_remaining_months or 0) > 0)

    monthly_commitments = monthly_premiums + monthly_scheme + total_emi

    # Investments include policies (ULIP/Endowment) + schemes
    total_investments_all = total_investments + total_policy_paid + total_scheme_paid

    # Investment allocation breakdown
    inv_by_type = db.session.query(
        Investment.investment_type, db.func.sum(Investment.amount_invested)
    ).filter_by(user_id=current_user.id, is_active=True).group_by(Investment.investment_type).all()
    allocation = [{'type': t, 'amount': float(a)} for t, a in inv_by_type]
    if total_policy_paid > 0:
        allocation.append({'type': 'Insurance', 'amount': float(total_policy_paid)})
    if total_scheme_paid > 0:
        allocation.append({'type': 'Schemes & Bonds', 'amount': float(total_scheme_paid)})

    # Upcoming dues (next payment due for each active policy/scheme)
    upcoming_dues = []
    today = date.today()
    for p in active_policies:
        if not p.start_date:
            continue
        fm = freq_div_map.get((p.premium_frequency or '').lower(), 12)
        d = p.start_date
        while d < today:
            d = d + relativedelta(months=fm)
        upcoming_dues.append({
            'name': p.policy_name, 'provider': p.provider,
            'amount': p.premium_amount, 'due_date': d, 'type': 'Premium',
            'days_left': (d - today).days
        })
    for s in active_schemes:
        if not s.start_date:
            continue
        fm = freq_div_map.get((s.installment_frequency or '').lower(), 12)
        d = s.start_date
        while d < today:
            d = d + relativedelta(months=fm)
        upcoming_dues.append({
            'name': s.scheme_name, 'provider': s.provider,
            'amount': s.installment_amount, 'due_date': d, 'type': 'Installment',
            'days_left': (d - today).days
        })
    upcoming_dues.sort(key=lambda x: x['due_date'])
    upcoming_dues = upcoming_dues[:6]

    # SIPs
    active_sips = SIP.query.filter_by(user_id=current_user.id, is_active=True).all()
    monthly_sip = sum(s.sip_amount for s in active_sips)
    total_sip_invested = sum(s.total_invested or 0 for s in active_sips)
    total_sip_value = sum(s.current_value or 0 for s in active_sips)
    monthly_commitments += monthly_sip
    total_investments_all += total_sip_invested

    if total_sip_invested > 0:
        allocation.append({'type': 'SIP (Mutual Funds)', 'amount': float(total_sip_invested)})

    # Add SIP dues to upcoming
    for s in active_sips:
        if not s.start_date:
            continue
        d = s.start_date
        while d < today:
            d = d + relativedelta(months=1)
        upcoming_dues.append({
            'name': s.fund_name, 'provider': s.platform or 'SIP',
            'amount': s.sip_amount, 'due_date': d, 'type': 'SIP',
            'days_left': (d - today).days
        })
    upcoming_dues.sort(key=lambda x: x['due_date'])
    upcoming_dues = upcoming_dues[:8]

    # Maturity tracker — items maturing within 365 days
    maturing_soon = []
    one_year = today + timedelta(days=365)
    for p in active_policies:
        if p.maturity_date and today <= p.maturity_date <= one_year:
            maturing_soon.append({
                'name': p.policy_name, 'type': 'Policy',
                'maturity_date': p.maturity_date, 'value': p.maturity_value or 0,
                'days_left': (p.maturity_date - today).days
            })
    for s in all_schemes:
        if s.maturity_date and s.status == 'active' and today <= s.maturity_date <= one_year:
            maturing_soon.append({
                'name': s.scheme_name, 'type': 'Scheme',
                'maturity_date': s.maturity_date, 'value': s.maturity_value or 0,
                'days_left': (s.maturity_date - today).days
            })
    for i in Investment.query.filter_by(user_id=current_user.id, is_active=True).all():
        if i.maturity_date and today <= i.maturity_date <= one_year:
            maturing_soon.append({
                'name': i.name, 'type': i.investment_type,
                'maturity_date': i.maturity_date, 'value': i.current_value or i.amount_invested,
                'days_left': (i.maturity_date - today).days
            })
    maturing_soon.sort(key=lambda x: x['maturity_date'])

    # Use tracked salary income for health score
    effective_salary = current_user.monthly_salary
    if effective_salary <= 0 and total_income > 0:
        # Estimate monthly salary from tracked salary income
        salary_income = db.session.query(db.func.sum(Income.amount)).filter_by(
            user_id=current_user.id, income_type='Salary'
        ).scalar() or 0
        if salary_income > 0:
            salary_count = Income.query.filter_by(user_id=current_user.id, income_type='Salary').count()
            effective_salary = salary_income / max(salary_count, 1)
        else:
            effective_salary = total_income

    health = advisor.analyze_financial_health(
        effective_salary, total_expenses, total_investments, total_debts
    )

    recent_expenses = Expense.query.filter_by(user_id=current_user.id).order_by(Expense.date.desc()).limit(5).all()
    recent_incomes = Income.query.filter_by(user_id=current_user.id).order_by(Income.date.desc()).limit(5).all()

    expense_by_cat = db.session.query(
        Expense.category, db.func.sum(Expense.amount)
    ).filter_by(user_id=current_user.id).group_by(Expense.category).all()

    monthly_trend = []
    for i in range(5, -1, -1):
        month_date = date.today() - relativedelta(months=i)
        month_exp = db.session.query(db.func.sum(Expense.amount)).filter(
            Expense.user_id == current_user.id,
            db.extract('month', Expense.date) == month_date.month,
            db.extract('year', Expense.date) == month_date.year
        ).scalar() or 0
        month_inc = db.session.query(db.func.sum(Income.amount)).filter(
            Income.user_id == current_user.id,
            db.extract('month', Income.date) == month_date.month,
            db.extract('year', Income.date) == month_date.year
        ).scalar() or 0
        monthly_trend.append({
            'month': month_date.strftime('%b %Y'),
            'expense': float(month_exp),
            'income': float(month_inc)
        })

    goals = FinancialGoal.query.filter_by(user_id=current_user.id).all()

    # Loan summary for dashboard
    active_loans = Loan.query.filter_by(user_id=current_user.id, is_active=True).all()
    total_loan_emi = sum(l.emi_amount for l in active_loans)
    total_loan_outstanding = sum(l.outstanding_balance or 0 for l in active_loans)
    monthly_commitments += total_loan_emi
    total_debts += total_loan_outstanding

    # Bank balance and PF for net worth
    total_bank_balance = db.session.query(db.func.sum(BankAccount.balance)).filter_by(user_id=current_user.id).scalar() or 0
    total_pf_balance = db.session.query(db.func.sum(ProvidentFund.total_balance)).filter_by(user_id=current_user.id).scalar() or 0
    total_investments_all += float(total_pf_balance)

    net_worth = total_assets_value + total_investments_all + float(total_bank_balance) - total_debts

    # Future readiness quick summary (target-year planner preview for dashboard)
    future_target_year = current_user.future_target_year or 2040
    future_data = advisor.get_future_readiness_plan(
        monthly_salary=current_user.monthly_salary or effective_salary or 0,
        age=current_user.age or 30,
        risk_appetite=current_user.risk_appetite or 'moderate',
        target_year=future_target_year,
    )
    future_target = float(future_data['plan']['monthly_investment_target'])
    current_investing = float(monthly_sip + monthly_premiums + monthly_scheme)
    investment_progress = min(100, int((current_investing / future_target) * 100)) if future_target > 0 else 0
    emergency_target = float(future_data['plan']['emergency_fund_target'])
    emergency_progress = min(100, int((float(total_bank_balance) / emergency_target) * 100)) if emergency_target > 0 else 0
    future_score = int(round((investment_progress * 0.55) + (emergency_progress * 0.30) + (max(0.0, min(100.0, health.savings_rate)) * 0.15)))

    future_checklist = [
        {
            'title': 'Emergency fund is 6 months ready',
            'done': float(total_bank_balance) >= emergency_target,
        },
        {
            'title': f'Monthly investing is on {future_target_year} target',
            'done': current_investing >= future_target,
        },
        {
            'title': 'Savings rate is healthy (20%+)',
            'done': health.savings_rate >= 20,
        },
    ]

    return render_template('dashboard.html',
        total_income=total_income,
        total_expenses=total_expenses,
        total_investments=total_investments_all,
        total_assets=total_assets_value,
        total_debts=total_debts,
        net_worth=net_worth,
        health=health,
        recent_expenses=recent_expenses,
        recent_incomes=recent_incomes,
        expense_by_cat=json.dumps([{'category': c, 'amount': float(a)} for c, a in expense_by_cat]),
        monthly_trend=json.dumps(monthly_trend),
        goals=goals,
        savings=total_income - total_expenses,
        monthly_commitments=monthly_commitments,
        total_sum_assured=total_sum_assured,
        allocation=json.dumps(allocation),
        upcoming_dues=upcoming_dues,
        maturing_soon=maturing_soon,
        active_loans=active_loans,
        total_loan_emi=total_loan_emi,
        total_loan_outstanding=total_loan_outstanding,
        total_bank_balance=float(total_bank_balance),
        total_pf_balance=float(total_pf_balance),
        future_data=future_data,
        future_score=future_score,
        future_checklist=future_checklist,
        future_investment_progress=investment_progress,
        future_emergency_progress=emergency_progress,
        future_current_investing=current_investing,
        future_monthly_target=future_target,
        future_emergency_target=emergency_target,
        future_target_year=future_target_year,
    )


# ======================== INCOME / SALARY ========================

@main.route('/income')
@login_required
def income():
    incomes = Income.query.filter_by(user_id=current_user.id).order_by(Income.date.desc()).all()
    total = sum(i.amount for i in incomes)
    income_types = Config.INCOME_TYPES

    # Keep salary in sync with actual records on every page load
    _sync_user_salary(current_user)
    db.session.commit()

    income_by_type = db.session.query(
        Income.income_type, db.func.sum(Income.amount)
    ).filter_by(user_id=current_user.id).group_by(Income.income_type).all()

    return render_template('income.html',
        incomes=incomes,
        total=total,
        income_types=income_types,
        income_by_type=json.dumps([{'type': t, 'amount': float(a)} for t, a in income_by_type])
    )


@main.route('/income/add', methods=['POST'])
@login_required
def add_income():
    inc = Income(
        user_id=current_user.id,
        source=request.form['source'],
        income_type=request.form['income_type'],
        amount=float(request.form['amount']),
        frequency=request.form.get('frequency', 'monthly'),
        date=datetime.strptime(request.form['date'], '%Y-%m-%d').date() if request.form.get('date') else date.today(),
        description=request.form.get('description', '')
    )
    db.session.add(inc)

    # Auto-update user salary from salary-type income records
    _sync_user_salary(current_user)

    db.session.commit()
    flash('Income added successfully!', 'success')
    return redirect(url_for('main.income'))


@main.route('/income/delete/<int:id>', methods=['POST'])
@login_required
def delete_income(id):
    inc = Income.query.get_or_404(id)
    if inc.user_id != current_user.id:
        flash('Unauthorized.', 'danger')
        return redirect(url_for('main.income'))
    db.session.delete(inc)

    # Re-sync salary after deletion
    _sync_user_salary(current_user)

    db.session.commit()
    flash('Income deleted.', 'info')
    return redirect(url_for('main.income'))


@main.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        current_user.full_name = request.form.get('full_name', '').strip()
        current_user.age = request.form.get('age', type=int)
        current_user.monthly_salary = request.form.get('monthly_salary', 0, type=float)
        current_user.annual_salary = current_user.monthly_salary * 12
        current_user.risk_appetite = request.form.get('risk_appetite', 'moderate')
        current_user.profession = request.form.get('profession', '').strip()
        current_user.state = request.form.get('state', '').strip()
        current_year = datetime.now().year
        requested_target_year = request.form.get('future_target_year', type=int)
        current_user.future_target_year = min(2100, max(current_year + 1, requested_target_year or (current_user.future_target_year or 2040)))
        current_user.enable_grocery_offers = request.form.get('enable_grocery_offers') == 'on'
        current_user.enable_future_monthly_reminders = request.form.get('enable_future_monthly_reminders') == 'on'
        current_user.enable_future_quarterly_reminders = request.form.get('enable_future_quarterly_reminders') == 'on'
        current_user.enable_only_critical_notifications = request.form.get('enable_only_critical_notifications') == 'on'
        lang = request.form.get('language', 'en')
        if lang in ('en', 'ta', 'hi', 'te'):
            current_user.language = lang
        db.session.commit()
        flash('Profile updated!', 'success')
        return redirect(url_for('main.profile'))
    return render_template('profile.html')


# ======================== EXPENSES ========================

@main.route('/expenses')
@login_required
def expenses():
    all_expenses = Expense.query.filter_by(user_id=current_user.id).order_by(Expense.date.desc()).all()
    total = sum(e.amount for e in all_expenses)
    categories = Config.EXPENSE_CATEGORIES

    expense_by_cat = db.session.query(
        Expense.category, db.func.sum(Expense.amount)
    ).filter_by(user_id=current_user.id).group_by(Expense.category).all()

    expenses_dict = {cat: float(amt) for cat, amt in expense_by_cat}

    # Auto-calculate actual percentages from salary
    salary = current_user.monthly_salary or 0
    needs_cats = ['Housing', 'Food & Groceries', 'Transportation', 'Utilities', 'Healthcare', 'Insurance']
    wants_cats = ['Entertainment', 'Shopping', 'Personal Care', 'Miscellaneous']
    savings_cats = ['Savings', 'Investments', 'Debt Payments']

    needs_total = sum(expenses_dict.get(c, 0) for c in needs_cats)
    wants_total = sum(expenses_dict.get(c, 0) for c in wants_cats)
    savings_total = sum(expenses_dict.get(c, 0) for c in savings_cats)

    # Include investment commitments in savings calculation
    freq_div_map = {'monthly': 1, 'quarterly': 3, 'half-yearly': 6, 'yearly': 12}
    active_policies = InsurancePolicy.query.filter_by(user_id=current_user.id, status='active').all()
    monthly_insurance = sum(
        p.premium_amount / freq_div_map.get((p.premium_frequency or '').lower(), 12)
        for p in active_policies
    )
    active_schemes = Scheme.query.filter_by(user_id=current_user.id, status='active').all()
    monthly_schemes = sum(
        s.installment_amount / freq_div_map.get((s.installment_frequency or '').lower(), 12)
        for s in active_schemes
    )
    active_sips = SIP.query.filter_by(user_id=current_user.id, is_active=True).all()
    monthly_sips = sum(s.sip_amount for s in active_sips)
    all_assets = Asset.query.filter_by(user_id=current_user.id).all()
    total_emi = sum(a.emi_amount or 0 for a in all_assets if (a.emi_remaining_months or 0) > 0)

    commitments = {
        'insurance': round(monthly_insurance),
        'schemes': round(monthly_schemes),
        'sips': round(monthly_sips),
        'emi': round(total_emi),
        'total': round(monthly_insurance + monthly_schemes + monthly_sips + total_emi)
    }

    # Actual savings = investment commitments + explicit savings expenses
    actual_savings = savings_total + commitments['total']
    total_spent = needs_total + wants_total
    unallocated = salary - total_spent - actual_savings

    # Auto-calculate actual percentages
    actual_pct = {
        'needs': round(needs_total / salary * 100, 1) if salary > 0 else 0,
        'wants': round(wants_total / salary * 100, 1) if salary > 0 else 0,
        'savings': round(actual_savings / salary * 100, 1) if salary > 0 else 0,
        'unallocated': round(unallocated / salary * 100, 1) if salary > 0 else 0,
    }

    # Warnings based on 50/30/20 benchmark
    warnings = []
    if actual_pct['needs'] > 50:
        warnings.append({'type': 'danger', 'icon': 'warning', 'msg': f"Needs at {actual_pct['needs']}% — exceeds 50% benchmark! Reduce essential spending."})
    if actual_pct['wants'] > 30:
        warnings.append({'type': 'danger', 'icon': 'warning', 'msg': f"Wants at {actual_pct['wants']}% — exceeds 30% benchmark! Cut discretionary spending."})
    if actual_pct['savings'] < 20 and salary > 0:
        warnings.append({'type': 'danger', 'icon': 'trending_down', 'msg': f"Savings at {actual_pct['savings']}% — below 20% benchmark! Increase investments."})
    if actual_pct['savings'] >= 20 and actual_pct['needs'] <= 50 and actual_pct['wants'] <= 30:
        warnings.append({'type': 'success', 'icon': 'check_circle', 'msg': "Your budget follows the 50/30/20 rule. Keep it up!"})

    # Monthly budget history (last 6 months)
    monthly_history = []
    for i in range(5, -1, -1):
        m_date = date.today() - relativedelta(months=i)
        m_exp = db.session.query(Expense.category, db.func.sum(Expense.amount)).filter(
            Expense.user_id == current_user.id,
            db.extract('month', Expense.date) == m_date.month,
            db.extract('year', Expense.date) == m_date.year
        ).group_by(Expense.category).all()
        m_dict = {c: float(a) for c, a in m_exp}
        m_needs = sum(m_dict.get(c, 0) for c in needs_cats)
        m_wants = sum(m_dict.get(c, 0) for c in wants_cats)
        m_sav = salary - m_needs - m_wants  # remaining goes to savings
        monthly_history.append({
            'month': m_date.strftime('%b %Y'),
            'needs_pct': round(m_needs / salary * 100, 1) if salary > 0 else 0,
            'wants_pct': round(m_wants / salary * 100, 1) if salary > 0 else 0,
            'savings_pct': round(m_sav / salary * 100, 1) if salary > 0 else 0,
            'needs': m_needs, 'wants': m_wants, 'savings': m_sav
        })

    remaining_after = salary - commitments['total'] - total

    expense_history = [{'amount': float(e.amount), 'date': str(e.date)} for e in all_expenses[:12]]
    trend = advisor.predict_expense_trend(expense_history)

    return render_template('expenses.html',
        expenses=all_expenses,
        total=total,
        categories=categories,
        expense_by_cat=json.dumps([{'category': c, 'amount': float(a)} for c, a in expense_by_cat]),
        actual_pct=actual_pct,
        needs_total=needs_total,
        wants_total=wants_total,
        actual_savings=actual_savings,
        unallocated=unallocated,
        warnings=warnings,
        monthly_history=json.dumps(monthly_history),
        commitments=commitments,
        remaining_after=remaining_after,
        trend=trend
    )


@main.route('/expenses/update-ratios', methods=['POST'])
@login_required
def update_budget_ratios():
    needs = float(request.form.get('needs_pct', 50))
    wants = float(request.form.get('wants_pct', 30))
    savings = float(request.form.get('savings_pct', 20))
    # Normalize to 100%
    total_pct = needs + wants + savings
    if total_pct > 0:
        needs = round(needs / total_pct * 100, 1)
        wants = round(wants / total_pct * 100, 1)
        savings = round(100 - needs - wants, 1)
    current_user.budget_needs_pct = needs
    current_user.budget_wants_pct = wants
    current_user.budget_savings_pct = savings
    db.session.commit()
    flash(f'Budget rule updated to {needs:.0f}/{wants:.0f}/{savings:.0f}!', 'success')
    return redirect(url_for('main.expenses'))


@main.route('/expenses/add', methods=['POST'])
@login_required
def add_expense():
    expense = Expense(
        user_id=current_user.id,
        category=request.form['category'],
        amount=float(request.form['amount']),
        date=datetime.strptime(request.form['date'], '%Y-%m-%d').date() if request.form.get('date') else date.today(),
        description=request.form.get('description', ''),
        is_recurring=bool(request.form.get('is_recurring'))
    )
    db.session.add(expense)
    db.session.commit()
    flash('Expense added!', 'success')
    return redirect(url_for('main.expenses'))


@main.route('/expenses/delete/<int:id>', methods=['POST'])
@login_required
def delete_expense(id):
    exp = Expense.query.get_or_404(id)
    if exp.user_id != current_user.id:
        flash('Unauthorized.', 'danger')
        return redirect(url_for('main.expenses'))
    db.session.delete(exp)
    db.session.commit()
    flash('Expense deleted.', 'info')
    return redirect(url_for('main.expenses'))


# ======================== INVESTMENTS ========================

@main.route('/investments')
@login_required
def investments():
    all_investments = Investment.query.filter_by(user_id=current_user.id).order_by(Investment.created_at.desc()).all()
    total_invested = sum(i.amount_invested for i in all_investments if i.is_active)
    total_current = sum(i.current_value for i in all_investments if i.is_active)

    inv_by_type = db.session.query(
        Investment.investment_type, db.func.sum(Investment.amount_invested)
    ).filter_by(user_id=current_user.id, is_active=True).group_by(Investment.investment_type).all()
    allocation = [{'type': t, 'amount': float(a)} for t, a in inv_by_type]

    # Include policies as investments
    all_policies = InsurancePolicy.query.filter_by(user_id=current_user.id).all()
    policy_invested = sum(p.total_paid or 0 for p in all_policies)
    policy_current = sum((p.maturity_value or p.total_paid or 0) for p in all_policies if p.status == 'active')
    total_invested += policy_invested
    total_current += policy_current
    if policy_invested > 0:
        allocation.append({'type': 'Insurance', 'amount': float(policy_invested)})

    # Include schemes as investments
    all_schemes = Scheme.query.filter_by(user_id=current_user.id).all()
    scheme_invested = sum(s.total_paid or 0 for s in all_schemes)
    scheme_current = sum((s.maturity_value or s.total_paid or 0) for s in all_schemes if s.status == 'active')
    total_invested += scheme_invested
    total_current += scheme_current
    if scheme_invested > 0:
        allocation.append({'type': 'Schemes & Bonds', 'amount': float(scheme_invested)})

    # Include SIPs as investments
    all_sips = SIP.query.filter_by(user_id=current_user.id).all()
    sip_invested = sum(s.total_invested or 0 for s in all_sips)
    sip_current = sum(s.current_value or 0 for s in all_sips)
    total_invested += sip_invested
    total_current += sip_current
    if sip_invested > 0:
        allocation.append({'type': 'SIP (Mutual Funds)', 'amount': float(sip_invested)})

    # Include Provident Fund as investments
    all_pf = ProvidentFund.query.filter_by(user_id=current_user.id).all()
    pf_balance = sum(p.total_balance or 0 for p in all_pf)
    total_invested += pf_balance
    total_current += pf_balance
    if pf_balance > 0:
        allocation.append({'type': 'Provident Fund', 'amount': float(pf_balance)})

    # Bank accounts
    all_banks = BankAccount.query.filter_by(user_id=current_user.id).all()
    total_bank_balance = sum(b.balance or 0 for b in all_banks)

    total_returns = total_current - total_invested

    return render_template('investments.html',
        investments=all_investments,
        policies=all_policies,
        schemes=all_schemes,
        sips=all_sips,
        pf_accounts=all_pf,
        bank_accounts=all_banks,
        total_bank_balance=total_bank_balance,
        total_invested=total_invested,
        total_current=total_current,
        total_returns=total_returns,
        inv_by_type=json.dumps(allocation)
    )


@main.route('/investments/add', methods=['POST'])
@login_required
def add_investment():
    inv = Investment(
        user_id=current_user.id,
        investment_type=request.form['investment_type'],
        platform=request.form.get('platform', ''),
        name=request.form['name'],
        amount_invested=float(request.form['amount_invested']),
        current_value=float(request.form.get('current_value', 0)),
        expected_return_rate=float(request.form.get('expected_return_rate', 0)),
        start_date=datetime.strptime(request.form['start_date'], '%Y-%m-%d').date() if request.form.get('start_date') else date.today(),
        maturity_date=datetime.strptime(request.form['maturity_date'], '%Y-%m-%d').date() if request.form.get('maturity_date') else None,
        member=request.form.get('member', 'Self'),
        notes=request.form.get('notes', '')
    )
    db.session.add(inv)
    db.session.commit()
    flash('Investment added!', 'success')
    return redirect(url_for('main.investments'))


@main.route('/investments/delete/<int:id>', methods=['POST'])
@login_required
def delete_investment(id):
    inv = Investment.query.get_or_404(id)
    if inv.user_id != current_user.id:
        flash('Unauthorized.', 'danger')
        return redirect(url_for('main.investments'))
    db.session.delete(inv)
    db.session.commit()
    flash('Investment deleted.', 'info')
    return redirect(url_for('main.investments'))


# ======================== PROVIDENT FUND ========================

@main.route('/add-pf', methods=['POST'])
@login_required
def add_pf():
    pf = ProvidentFund(
        user_id=current_user.id,
        pf_type=request.form.get('pf_type', 'EPF'),
        uan_number=request.form.get('uan_number', '').strip(),
        employer=request.form.get('employer', '').strip(),
        employee_contribution=float(request.form.get('employee_contribution') or 0),
        employer_contribution=float(request.form.get('employer_contribution') or 0),
        total_balance=float(request.form.get('total_balance') or 0),
        interest_rate=float(request.form.get('interest_rate') or 8.25),
        start_date=datetime.strptime(request.form['start_date'], '%Y-%m-%d').date() if request.form.get('start_date') else None,
        notes=request.form.get('notes', '').strip()
    )
    db.session.add(pf)
    db.session.commit()
    flash('Provident Fund added!', 'success')
    return redirect(url_for('main.investments'))


@main.route('/delete-pf/<int:id>', methods=['POST'])
@login_required
def delete_pf(id):
    pf = ProvidentFund.query.get_or_404(id)
    if pf.user_id != current_user.id:
        flash('Unauthorized.', 'danger')
        return redirect(url_for('main.investments'))
    db.session.delete(pf)
    db.session.commit()
    flash('PF record deleted.', 'info')
    return redirect(url_for('main.investments'))


# ======================== BANK ACCOUNTS ========================

@main.route('/add-bank-account', methods=['POST'])
@login_required
def add_bank_account():
    acct = BankAccount(
        user_id=current_user.id,
        bank_name=request.form.get('bank_name', '').strip(),
        account_type=request.form.get('account_type', 'Savings'),
        account_number_last4=request.form.get('account_number_last4', '').strip()[-4:],
        balance=float(request.form.get('balance') or 0),
        interest_rate=float(request.form.get('interest_rate') or 0),
        notes=request.form.get('notes', '').strip()
    )
    db.session.add(acct)
    db.session.commit()
    flash('Bank account added!', 'success')
    return redirect(url_for('main.investments'))


@main.route('/update-bank-balance/<int:id>', methods=['POST'])
@login_required
def update_bank_balance(id):
    acct = BankAccount.query.get_or_404(id)
    if acct.user_id != current_user.id:
        flash('Unauthorized.', 'danger')
        return redirect(url_for('main.investments'))
    acct.balance = float(request.form.get('balance') or 0)
    db.session.commit()
    flash(f'{acct.bank_name} balance updated!', 'success')
    return redirect(url_for('main.investments'))


@main.route('/delete-bank-account/<int:id>', methods=['POST'])
@login_required
def delete_bank_account(id):
    acct = BankAccount.query.get_or_404(id)
    if acct.user_id != current_user.id:
        flash('Unauthorized.', 'danger')
        return redirect(url_for('main.investments'))
    db.session.delete(acct)
    db.session.commit()
    flash('Bank account removed.', 'info')
    return redirect(url_for('main.investments'))


# ======================== INVESTMENT CALCULATORS ========================

@main.route('/calculators')
@login_required
def calculators():
    return render_template('calculators.html')


@main.route('/api/calculate', methods=['POST'])
@login_required
def calculate():
    data = request.get_json()
    calc_type = data.get('type')

    if calc_type == 'sip':
        result = advisor.calculate_investment_returns(
            principal=0,
            rate=float(data.get('rate', 12)),
            years=int(data.get('years', 10)),
            investment_type='sip',
            monthly_sip=float(data.get('monthly_sip', 5000))
        )
    elif calc_type == 'lumpsum':
        result = advisor.calculate_investment_returns(
            principal=float(data.get('principal', 100000)),
            rate=float(data.get('rate', 10)),
            years=int(data.get('years', 10)),
            investment_type='lumpsum'
        )
    elif calc_type == 'emi':
        principal = float(data.get('principal', 1000000))
        rate = float(data.get('rate', 8.5))
        years = int(data.get('years', 20))
        emi = advisor._calculate_emi(principal, rate, years)
        total_payment = emi * years * 12
        total_interest = total_payment - principal
        result = {
            'emi': emi,
            'total_payment': round(total_payment),
            'total_interest': round(total_interest),
            'principal': principal
        }
    elif calc_type == 'retirement':
        result = advisor.calculate_retirement_corpus(
            current_age=int(data.get('current_age', 30)),
            retirement_age=int(data.get('retirement_age', 60)),
            monthly_expense=float(data.get('monthly_expense', 50000)),
            inflation_rate=float(data.get('inflation_rate', 6)),
            return_rate=float(data.get('return_rate', 10))
        )
    elif calc_type == 'fd':
        principal = float(data.get('principal', 100000))
        rate = float(data.get('rate', 7))
        years = int(data.get('years', 5))
        amount = principal * ((1 + rate / 100 / 4) ** (4 * years))
        result = {
            'invested': principal,
            'maturity_value': round(amount),
            'interest_earned': round(amount - principal),
            'effective_rate': round((amount / principal - 1) * 100, 2)
        }
    else:
        return jsonify({'error': 'Invalid calculator type'}), 400

    return jsonify(result)


# ======================== AI SUGGESTIONS ========================

@main.route('/suggestions')
@login_required
def suggestions():
    age = current_user.age or 30
    salary = current_user.monthly_salary or 0
    risk = current_user.risk_appetite or 'moderate'

    investment_suggestions = advisor.get_investment_suggestions(salary, age, risk)
    commodity_suggestions = advisor.get_commodity_suggestions(salary)
    tax_suggestions = advisor.get_tax_saving_suggestions(salary * 12)

    total_emi = db.session.query(db.func.sum(Asset.emi_amount)).filter_by(user_id=current_user.id).scalar() or 0
    asset_plan = advisor.get_asset_buying_plan(salary, age, float(total_emi))

    total_expenses = db.session.query(db.func.sum(Expense.amount)).filter_by(user_id=current_user.id).scalar() or salary * 0.6
    retirement = advisor.calculate_retirement_corpus(age, 60, float(total_expenses) if total_expenses else salary * 0.6)

    # Bank balance for context in suggestions
    total_bank_balance = db.session.query(db.func.sum(BankAccount.balance)).filter_by(user_id=current_user.id).scalar() or 0

    # Vehicle buy timing suggestions
    buy_timing = []
    user_goals = FinancialGoal.query.filter_by(user_id=current_user.id).all()
    goal_categories_found = set()
    for g in user_goals:
        cat = (g.category or '').lower()
        if cat in ['car', 'automobile', 'vehicle', 'bike', 'two wheeler', 'scooter', 'motorcycle']:
            timing = advisor.get_buy_timing_suggestion(g.category, g.target_amount)
            buy_timing.append({'goal_name': g.goal_name, 'target_amount': g.target_amount, 'suggestions': timing})
            goal_categories_found.add('car' if cat in ['car', 'automobile', 'vehicle'] else 'bike')
    if 'car' not in goal_categories_found:
        timing = advisor.get_buy_timing_suggestion('car', 1000000)
        buy_timing.insert(0, {'goal_name': 'Buy a Car', 'target_amount': 1000000, 'suggestions': timing})
    if 'bike' not in goal_categories_found:
        timing = advisor.get_buy_timing_suggestion('bike', 150000)
        buy_timing.append({'goal_name': 'Buy a Bike', 'target_amount': 150000, 'suggestions': timing})

    # Grocery offers (only if user enabled it in profile)
    grocery_offers = advisor.get_grocery_offers(salary) if current_user.enable_grocery_offers else None

    return render_template('suggestions.html',
        investment_suggestions=investment_suggestions,
        commodity_suggestions=commodity_suggestions,
        tax_suggestions=tax_suggestions,
        asset_plan=asset_plan,
        retirement=retirement,
        bank_balance=float(total_bank_balance),
        buy_timing=buy_timing,
        grocery_offers=grocery_offers
    )


@main.route('/ai-playbooks')
@login_required
def ai_playbooks():
    data = advisor.get_ai_playbooks(
        monthly_salary=current_user.monthly_salary or 0,
        profession=current_user.profession or '',
        state=current_user.state or '',
        risk_appetite=current_user.risk_appetite or 'moderate',
    )
    return render_template('ai_playbooks.html', data=data)


@main.route('/future-planner')
@login_required
def future_planner():
    data = advisor.get_future_readiness_plan(
        monthly_salary=current_user.monthly_salary or 0,
        age=current_user.age or 30,
        risk_appetite=current_user.risk_appetite or 'moderate',
        target_year=current_user.future_target_year or 2040,
    )
    return render_template('future_planner.html', data=data)


# ======================== BUSINESS IDEAS ========================

@main.route('/business-ideas')
@login_required
def business_ideas():
    salary = current_user.monthly_salary or 0
    age = current_user.age or 30
    risk = current_user.risk_appetite or 'moderate'
    profession = current_user.profession or ''
    state = current_user.state or ''

    total_savings = db.session.query(db.func.sum(BankAccount.balance)).filter_by(user_id=current_user.id).scalar() or 0
    total_investments = db.session.query(db.func.sum(Investment.current_value)).filter_by(user_id=current_user.id).scalar() or 0

    ideas = advisor.get_business_ideas(
        profession=profession,
        monthly_salary=salary,
        age=age,
        risk_appetite=risk,
        state=state,
        total_savings=float(total_savings),
        total_investments=float(total_investments)
    )

    return render_template('business_ideas.html', ideas=ideas)


# ======================== ASSETS ========================

@main.route('/assets')
@login_required
def assets():
    all_assets = Asset.query.filter_by(user_id=current_user.id).order_by(Asset.created_at.desc()).all()
    total_value = sum(a.current_value for a in all_assets)
    total_loans = sum(a.loan_amount for a in all_assets)
    total_emi = sum(a.emi_amount for a in all_assets)
    categories = Config.ASSET_CATEGORIES

    asset_by_type = db.session.query(
        Asset.asset_type, db.func.sum(Asset.current_value)
    ).filter_by(user_id=current_user.id).group_by(Asset.asset_type).all()

    return render_template('assets.html',
        assets=all_assets,
        total_value=total_value,
        total_loans=total_loans,
        total_emi=total_emi,
        categories=categories,
        asset_by_type=json.dumps([{'type': t, 'value': float(v)} for t, v in asset_by_type])
    )


@main.route('/assets/add', methods=['POST'])
@login_required
def add_asset():
    asset = Asset(
        user_id=current_user.id,
        asset_type=request.form['asset_type'],
        name=request.form['name'],
        purchase_price=float(request.form.get('purchase_price') or 0),
        current_value=float(request.form.get('current_value') or 0),
        purchase_date=datetime.strptime(request.form['purchase_date'], '%Y-%m-%d').date() if request.form.get('purchase_date') else date.today(),
        emi_amount=float(request.form.get('emi_amount') or 0),
        emi_remaining_months=int(request.form.get('emi_remaining_months') or 0),
        loan_amount=float(request.form.get('loan_amount') or 0),
        notes=request.form.get('notes', '')
    )
    db.session.add(asset)
    db.session.commit()
    flash('Asset added!', 'success')
    return redirect(url_for('main.assets'))


@main.route('/assets/delete/<int:id>', methods=['POST'])
@login_required
def delete_asset(id):
    asset = Asset.query.get_or_404(id)
    if asset.user_id != current_user.id:
        flash('Unauthorized.', 'danger')
        return redirect(url_for('main.assets'))
    db.session.delete(asset)
    db.session.commit()
    flash('Asset deleted.', 'info')
    return redirect(url_for('main.assets'))


# ======================== GOALS ========================

@main.route('/goals')
@login_required
def goals():
    all_goals = FinancialGoal.query.filter_by(user_id=current_user.id).order_by(FinancialGoal.priority.desc()).all()
    return render_template('goals.html', goals=all_goals)


@main.route('/goals/add', methods=['POST'])
@login_required
def add_goal():
    goal = FinancialGoal(
        user_id=current_user.id,
        goal_name=request.form['goal_name'],
        target_amount=float(request.form['target_amount']),
        current_saved=float(request.form.get('current_saved', 0)),
        target_date=datetime.strptime(request.form['target_date'], '%Y-%m-%d').date() if request.form.get('target_date') else None,
        priority=request.form.get('priority', 'medium'),
        category=request.form.get('category', '')
    )
    db.session.add(goal)
    db.session.commit()
    flash('Goal added!', 'success')
    return redirect(url_for('main.goals'))


@main.route('/goals/update/<int:id>', methods=['POST'])
@login_required
def update_goal(id):
    goal = FinancialGoal.query.get_or_404(id)
    if goal.user_id != current_user.id:
        flash('Unauthorized.', 'danger')
        return redirect(url_for('main.goals'))
    goal.current_saved = float(request.form.get('current_saved', goal.current_saved))
    db.session.commit()
    flash('Goal updated!', 'success')
    return redirect(url_for('main.goals'))


@main.route('/goals/delete/<int:id>', methods=['POST'])
@login_required
def delete_goal(id):
    goal = FinancialGoal.query.get_or_404(id)
    if goal.user_id != current_user.id:
        flash('Unauthorized.', 'danger')
        return redirect(url_for('main.goals'))
    db.session.delete(goal)
    db.session.commit()
    flash('Goal deleted.', 'info')
    return redirect(url_for('main.goals'))


# ======================== TURNOVER / REPORTS ========================

@main.route('/reports')
@login_required
def reports():
    months_data = []
    for i in range(11, -1, -1):
        month_date = date.today() - relativedelta(months=i)
        income_total = db.session.query(db.func.sum(Income.amount)).filter(
            Income.user_id == current_user.id,
            db.extract('month', Income.date) == month_date.month,
            db.extract('year', Income.date) == month_date.year
        ).scalar() or 0
        expense_total = db.session.query(db.func.sum(Expense.amount)).filter(
            Expense.user_id == current_user.id,
            db.extract('month', Expense.date) == month_date.month,
            db.extract('year', Expense.date) == month_date.year
        ).scalar() or 0
        months_data.append({
            'month': month_date.strftime('%b %Y'),
            'income': float(income_total),
            'expense': float(expense_total),
            'savings': float(income_total) - float(expense_total)
        })

    total_income = db.session.query(db.func.sum(Income.amount)).filter_by(user_id=current_user.id).scalar() or 0
    total_expense = db.session.query(db.func.sum(Expense.amount)).filter_by(user_id=current_user.id).scalar() or 0

    return render_template('reports.html',
        months_data=json.dumps(months_data),
        total_income=float(total_income),
        total_expense=float(total_expense),
        turnover=float(total_income),
        net_savings=float(total_income) - float(total_expense)
    )


# ======================== ADMIN PANEL ========================

@main.route('/admin')
@admin_required
def admin_panel():
    users = User.query.order_by(User.created_at.desc()).all()
    total_users = len(users)
    verified_users = sum(1 for u in users if u.is_verified)
    unverified_users = total_users - verified_users

    # System stats
    total_income = db.session.query(db.func.sum(Income.amount)).scalar() or 0
    total_expenses = db.session.query(db.func.sum(Expense.amount)).scalar() or 0
    total_investments = db.session.query(db.func.sum(Investment.amount_invested)).scalar() or 0

    # Load current mail settings
    mail_cfg = load_mail_config()

    # Feedback stats
    all_feedbacks = Feedback.query.order_by(Feedback.created_at.desc()).all()
    avg_rating = db.session.query(db.func.avg(Feedback.rating)).scalar() or 0

    return render_template('admin_panel.html',
        users=users,
        total_users=total_users,
        verified_users=verified_users,
        unverified_users=unverified_users,
        total_income=float(total_income),
        total_expenses=float(total_expenses),
        total_investments=float(total_investments),
        mail_cfg=mail_cfg,
        feedbacks=all_feedbacks,
        avg_rating=round(float(avg_rating), 1)
    )


@main.route('/admin/delete-user/<int:id>', methods=['POST'])
@admin_required
def admin_delete_user(id):
    user = db.session.get(User, id)
    if not user:
        flash('User not found.', 'danger')
        return redirect(url_for('main.admin_panel'))
    if user.is_admin:
        flash('Cannot delete admin account.', 'danger')
        return redirect(url_for('main.admin_panel'))
    db.session.delete(user)
    db.session.commit()
    flash(f'User "{user.username}" deleted.', 'info')
    return redirect(url_for('main.admin_panel'))


@main.route('/admin/mail-settings', methods=['POST'])
@admin_required
def admin_mail_settings():
    mail_server = request.form.get('mail_server', 'smtp.gmail.com').strip()
    mail_port = request.form.get('mail_port', '587').strip()
    mail_username = request.form.get('mail_username', '').strip()
    mail_password = request.form.get('mail_password', '').strip()
    mail_default_sender = request.form.get('mail_default_sender', '').strip()

    # Load existing config to preserve password if not changed
    existing = load_mail_config()
    if mail_password == '********' or not mail_password:
        mail_password = existing.get('mail_password', '')

    cfg = {
        'mail_server': mail_server,
        'mail_port': int(mail_port) if mail_port.isdigit() else 587,
        'mail_use_tls': True,
        'mail_username': mail_username,
        'mail_password': mail_password,
        'mail_default_sender': mail_default_sender or mail_username,
    }
    save_mail_config(cfg)

    # Apply to current running app
    from flask import current_app
    apply_mail_config(current_app._get_current_object())

    # Test connection if credentials provided
    if mail_username and mail_password:
        try:
            import smtplib
            with smtplib.SMTP(mail_server, int(cfg['mail_port'])) as smtp:
                smtp.ehlo()
                smtp.starttls()
                smtp.login(mail_username, mail_password)
            flash('Mail settings saved & SMTP connection verified successfully!', 'success')
        except Exception as e:
            flash(f'Settings saved but SMTP test failed: {str(e)}', 'warning')
    else:
        flash('Mail settings saved. Add username & password to enable email delivery.', 'info')

    return redirect(url_for('main.admin_panel'))


@main.route('/admin/test-mail', methods=['POST'])
@admin_required
def admin_test_mail():
    from flask import current_app
    from app import mail
    from flask_mail import Message
    test_email = request.form.get('test_email', '').strip()
    if not test_email or not validate_email(test_email):
        flash('Enter a valid email address to send test mail.', 'danger')
        return redirect(url_for('main.admin_panel'))

    apply_mail_config(current_app._get_current_object())
    try:
        msg = Message(
            subject='WealthPilot - Test Email',
            recipients=[test_email],
            body='This is a test email from WealthPilot.\nYour SMTP settings are working correctly!'
        )
        mail.send(msg)
        flash(f'Test email sent to {test_email} successfully!', 'success')
    except Exception as e:
        flash(f'Failed to send test email: {str(e)}', 'danger')

    return redirect(url_for('main.admin_panel'))


@main.route('/admin/toggle-verify/<int:id>', methods=['POST'])
@admin_required
def admin_toggle_verify(id):
    user = db.session.get(User, id)
    if not user:
        flash('User not found.', 'danger')
        return redirect(url_for('main.admin_panel'))
    user.is_verified = not user.is_verified
    db.session.commit()
    status = 'verified' if user.is_verified else 'unverified'
    flash(f'User "{user.username}" marked as {status}.', 'success')
    return redirect(url_for('main.admin_panel'))


# ======================== INSURANCE POLICIES ========================

@main.route('/policies')
@login_required
def policies():
    all_policies = InsurancePolicy.query.filter_by(user_id=current_user.id).order_by(InsurancePolicy.created_at.desc()).all()
    active_policies = [p for p in all_policies if p.status == 'active']
    total_premium_monthly = 0
    for p in active_policies:
        if p.premium_frequency == 'monthly':
            total_premium_monthly += p.premium_amount
        elif p.premium_frequency == 'quarterly':
            total_premium_monthly += p.premium_amount / 3
        elif p.premium_frequency == 'half-yearly':
            total_premium_monthly += p.premium_amount / 6
        elif p.premium_frequency == 'yearly':
            total_premium_monthly += p.premium_amount / 12

    total_sum_assured = sum(p.sum_assured for p in active_policies)
    total_paid = sum(p.total_paid for p in all_policies)
    providers = Config.INSURANCE_PROVIDERS
    policy_types = Config.POLICY_TYPES

    # Group by provider
    by_provider = {}
    for p in all_policies:
        by_provider.setdefault(p.provider, []).append(p)

    return render_template('policies.html',
        policies=all_policies,
        active_count=len(active_policies),
        total_premium_monthly=total_premium_monthly,
        total_sum_assured=total_sum_assured,
        total_paid=total_paid,
        providers=providers,
        policy_types=policy_types,
        by_provider=by_provider,
        by_provider_json=json.dumps([{'provider': k, 'count': len(v)} for k, v in by_provider.items()])
    )


@main.route('/policies/add', methods=['POST'])
@login_required
def add_policy():
    premium = float(request.form.get('premium_amount') or 0)
    total_installments_paid = int(request.form.get('installments_paid') or 0)
    policy = InsurancePolicy(
        user_id=current_user.id,
        policy_type=request.form['policy_type'],
        provider=request.form['provider'],
        policy_name=request.form['policy_name'],
        policy_number=request.form.get('policy_number', ''),
        sum_assured=float(request.form.get('sum_assured') or 0),
        premium_amount=premium,
        premium_frequency=request.form.get('premium_frequency', 'monthly'),
        start_date=datetime.strptime(request.form['start_date'], '%Y-%m-%d').date() if request.form.get('start_date') else date.today(),
        maturity_date=datetime.strptime(request.form['maturity_date'], '%Y-%m-%d').date() if request.form.get('maturity_date') else None,
        nominee=request.form.get('nominee', ''),
        status=request.form.get('status', 'active'),
        total_paid=premium * total_installments_paid,
        maturity_value=float(request.form.get('maturity_value') or 0),
        member=request.form.get('member', 'Self'),
        notes=request.form.get('notes', '')
    )
    db.session.add(policy)
    db.session.commit()
    flash('Policy added successfully!', 'success')
    return redirect(url_for('main.policies'))


@main.route('/policies/delete/<int:id>', methods=['POST'])
@login_required
def delete_policy(id):
    policy = InsurancePolicy.query.get_or_404(id)
    if policy.user_id != current_user.id:
        flash('Unauthorized.', 'danger')
        return redirect(url_for('main.policies'))
    db.session.delete(policy)
    db.session.commit()
    flash('Policy deleted.', 'info')
    return redirect(url_for('main.policies'))


@main.route('/policies/update/<int:id>', methods=['POST'])
@login_required
def update_policy(id):
    policy = InsurancePolicy.query.get_or_404(id)
    if policy.user_id != current_user.id:
        flash('Unauthorized.', 'danger')
        return redirect(url_for('main.policies'))
    policy.provider = request.form.get('provider', policy.provider)
    policy.policy_type = request.form.get('policy_type', policy.policy_type)
    policy.policy_name = request.form.get('policy_name', policy.policy_name)
    policy.policy_number = request.form.get('policy_number', policy.policy_number)
    policy.premium_amount = float(request.form.get('premium_amount') or policy.premium_amount)
    policy.premium_frequency = request.form.get('premium_frequency', policy.premium_frequency)
    if request.form.get('premium_due_day'):
        policy.premium_due_day = int(request.form.get('premium_due_day') or 0)
    policy.sum_assured = float(request.form.get('sum_assured') or 0)
    policy.maturity_value = float(request.form.get('maturity_value') or 0)
    policy.nominee = request.form.get('nominee', policy.nominee)
    policy.total_paid = float(request.form.get('total_paid') or policy.total_paid)
    policy.status = request.form.get('status', policy.status)
    policy.notes = request.form.get('notes', policy.notes)
    if request.form.get('start_date'):
        policy.start_date = datetime.strptime(request.form['start_date'], '%Y-%m-%d').date()
    if request.form.get('maturity_date'):
        policy.maturity_date = datetime.strptime(request.form['maturity_date'], '%Y-%m-%d').date()
    db.session.commit()
    flash('Policy updated!', 'success')
    return redirect(url_for('main.policies'))


@main.route('/policies/calc-by-due', methods=['POST'])
@login_required
def calc_paid_by_due():
    """Calculate total paid based on due date tracking.
    Counts how many due dates have passed from start_date up to the selected month."""
    policy_id = request.form.get('policy_id', type=int)
    paid_upto = request.form.get('paid_upto', '').strip()  # YYYY-MM format
    if not policy_id or not paid_upto:
        return jsonify(success=False, message='Missing parameters.')

    policy = InsurancePolicy.query.get_or_404(policy_id)
    if policy.user_id != current_user.id:
        return jsonify(success=False, message='Unauthorized.')
    if not policy.start_date or not policy.premium_amount:
        return jsonify(success=False, message='Policy must have start date and premium amount.')

    freq_months = {'monthly': 1, 'quarterly': 3, 'half-yearly': 6,
                   'yearly': 12}.get((policy.premium_frequency or '').lower(), 12)

    # Parse the paid_upto month
    paid_year, paid_month = int(paid_upto.split('-')[0]), int(paid_upto.split('-')[1])
    due_day = policy.premium_due_day or policy.start_date.day

    # Calculate all due dates from start_date with the given frequency
    current_due = policy.start_date
    today = date.today()
    paid_upto_date = date(paid_year, paid_month, min(due_day, 28))

    # Count premiums from start to paid_upto month
    count = 0
    d = policy.start_date
    while d <= paid_upto_date:
        count += 1
        d = d + relativedelta(months=freq_months)

    total = count * policy.premium_amount

    # Find unpaid months (dues between last recorded and selected)
    # Check which months had no payment recorded
    unpaid_months = []
    d = policy.start_date
    while d <= paid_upto_date:
        # Check if there's a payment within ±15 days of this due
        has_payment = PremiumPayment.query.filter(
            PremiumPayment.policy_id == policy_id,
            PremiumPayment.payment_date >= d - timedelta(days=15),
            PremiumPayment.payment_date <= d + timedelta(days=15)
        ).first()
        if not has_payment:
            unpaid_months.append(d.strftime('%B %Y'))
        d = d + relativedelta(months=freq_months)

    return jsonify(
        success=True,
        total=total,
        count=count,
        premium=policy.premium_amount,
        unpaid_months=unpaid_months,
    )


@main.route('/policies/scan-statement', methods=['POST'])
@login_required
def scan_premium_statement():
    """Scan a premium paid statement PDF and extract total paid amount."""
    if 'document' not in request.files:
        return jsonify(success=False, message='No file uploaded.')
    file = request.files['document']
    if not file.filename:
        return jsonify(success=False, message='No file selected.')

    from .doc_parser import extract_text_from_pdf
    import tempfile

    ext = os.path.splitext(file.filename)[1].lower()
    if ext != '.pdf':
        return jsonify(success=False, message='Only PDF files are supported for statements.')

    with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
        file.save(tmp.name)
        text = extract_text_from_pdf(tmp.name)
        os.unlink(tmp.name)

    if not text or len(text.strip()) < 20:
        return jsonify(success=False, message='Could not extract text from the document.')

    # Try to find total premium paid from statement
    total_paid = 0
    # Look for patterns like "Total Premium Paid: 60,000" or "Total.*₹.*60,000"
    patterns = [
        r'(?:Total\s+Premium\s+Paid|Total\s+Amount\s+Paid|Total\s+Paid|Grand\s+Total)[:\s]*(?:Rs\.?|₹|INR)?\s*([\d,]+(?:\.\d{2})?)',
        r'(?:Total\s+Premium|Net\s+Premium\s+Paid)[:\s]*(?:Rs\.?|₹|INR)?\s*([\d,]+(?:\.\d{2})?)',
    ]
    for pat in patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            total_paid = float(m.group(1).replace(',', ''))
            break

    # If no total found, sum all individual premium amounts in the statement
    if total_paid == 0:
        amounts = re.findall(r'(?:Rs\.?|₹|INR)\s*([\d,]+(?:\.\d{2})?)', text)
        if amounts:
            parsed = [float(a.replace(',', '')) for a in amounts]
            # Filter to likely premium amounts (>= 100)
            parsed = [a for a in parsed if a >= 100]
            if parsed:
                total_paid = sum(parsed)

    # Extract individual payment entries: date + amount pairs
    # Common patterns: "25/12/2024  5,000.00" or "2024-12-25  Rs. 5,000"
    payment_entries = []
    date_amt_patterns = [
        r'(\d{2}[/-]\d{2}[/-]\d{4})\s+(?:Rs\.?|₹|INR)?\s*([\d,]+(?:\.\d{2})?)',
        r'(\d{4}[/-]\d{2}[/-]\d{2})\s+(?:Rs\.?|₹|INR)?\s*([\d,]+(?:\.\d{2})?)',
    ]
    for pat in date_amt_patterns:
        for m in re.finditer(pat, text):
            try:
                ds = m.group(1)
                amt = float(m.group(2).replace(',', ''))
                if amt < 100:
                    continue
                for fmt in ('%d/%m/%Y', '%d-%m-%Y', '%Y-%m-%d', '%Y/%m/%d'):
                    try:
                        dt = datetime.strptime(ds, fmt).date()
                        payment_entries.append({'date': dt.isoformat(), 'amount': amt})
                        break
                    except ValueError:
                        continue
            except (ValueError, IndexError):
                continue
        if payment_entries:
            break

    if total_paid == 0 and not payment_entries:
        return jsonify(success=False, message='Could not find premium paid amounts in the document.',
                       raw_text_preview=text[:500])

    return jsonify(success=True, total_paid=total_paid,
                   payments=payment_entries,
                   message=f'Found total paid: ₹{total_paid:,.0f}' + (f' ({len(payment_entries)} individual payments)' if payment_entries else ''))


@main.route('/policies/lookup', methods=['POST'])
@login_required
def lookup_premium():
    policy_number = request.form.get('policy_number', '').strip()
    if not policy_number:
        return jsonify(success=False, message='Please enter a policy number.')
    policy = InsurancePolicy.query.filter_by(
        user_id=current_user.id, policy_number=policy_number
    ).first()
    if not policy:
        return jsonify(success=False, message=f'No policy found with number "{policy_number}".')

    # Get actual payment records
    payments = PremiumPayment.query.filter_by(policy_id=policy.id).order_by(PremiumPayment.payment_date.desc()).all()
    actual_total = sum(p.amount for p in payments)

    # Calculate next due date from last payment or start_date
    next_due = None
    if policy.start_date:
        freq_months = {'monthly': 1, 'quarterly': 3, 'half-yearly': 6,
                       'semi-annually': 6, 'yearly': 12, 'annually': 12}.get(
            (policy.premium_frequency or '').lower(), 12)
        if payments:
            last_paid = max(p.payment_date for p in payments)
            next_due = last_paid + relativedelta(months=freq_months)
        else:
            next_due = policy.start_date + relativedelta(months=freq_months)

    payment_list = [dict(
        id=p.id,
        amount=p.amount,
        date=p.payment_date.strftime('%d-%m-%Y'),
        note=p.note or ''
    ) for p in payments]

    return jsonify(
        success=True,
        data=dict(
            policy_id=policy.id,
            policy_name=policy.policy_name or '',
            policy_number=policy.policy_number,
            provider=policy.provider or '',
            policy_type=policy.policy_type or '',
            premium_amount=policy.premium_amount or 0,
            premium_frequency=policy.premium_frequency or '',
            sum_assured=policy.sum_assured or 0,
            maturity_value=policy.maturity_value or 0,
            start_date=policy.start_date.strftime('%d-%m-%Y') if policy.start_date else '',
            maturity_date=policy.maturity_date.strftime('%d-%m-%Y') if policy.maturity_date else '',
            status=policy.status or '',
            actual_total=actual_total,
            payment_count=len(payments),
            next_due=next_due.strftime('%d-%m-%Y') if next_due else '',
            payments=payment_list,
        )
    )


@main.route('/policies/record-payment', methods=['POST'])
@login_required
def record_premium_payment():
    policy_id = request.form.get('policy_id', type=int)
    amount = float(request.form.get('amount') or 0)
    payment_date_str = request.form.get('payment_date', '').strip()
    note = request.form.get('note', '').strip()

    if not policy_id or amount <= 0 or not payment_date_str:
        return jsonify(success=False, message='Policy, amount and date are required.')

    policy = InsurancePolicy.query.get_or_404(policy_id)
    if policy.user_id != current_user.id:
        return jsonify(success=False, message='Unauthorized.')

    payment_date = datetime.strptime(payment_date_str, '%Y-%m-%d').date()

    # Auto-create an Expense so premium shows in financial tracking
    expense = Expense(
        user_id=current_user.id,
        category='Insurance',
        amount=amount,
        date=payment_date,
        description=f'Premium - {policy.policy_name}',
        is_recurring=False,
    )
    db.session.add(expense)
    db.session.flush()  # get expense.id

    payment = PremiumPayment(policy_id=policy_id, amount=amount,
                             payment_date=payment_date, note=note,
                             expense_id=expense.id)
    db.session.add(payment)

    # Sync total_paid on the policy
    policy.total_paid = (policy.total_paid or 0) + amount
    db.session.commit()
    return jsonify(success=True, message='Payment recorded!')


@main.route('/policies/delete-payment/<int:payment_id>', methods=['POST'])
@login_required
def delete_premium_payment(payment_id):
    payment = PremiumPayment.query.get_or_404(payment_id)
    policy = InsurancePolicy.query.get_or_404(payment.policy_id)
    if policy.user_id != current_user.id:
        return jsonify(success=False, message='Unauthorized.')

    policy.total_paid = max(0, (policy.total_paid or 0) - payment.amount)

    # Remove linked expense
    if payment.expense_id:
        linked_expense = Expense.query.get(payment.expense_id)
        if linked_expense:
            db.session.delete(linked_expense)

    db.session.delete(payment)
    db.session.commit()
    return jsonify(success=True, message='Payment deleted.')


# ======================== SCHEMES & BONDS ========================

@main.route('/schemes')
@login_required
def schemes():
    all_schemes = Scheme.query.filter_by(user_id=current_user.id).order_by(Scheme.created_at.desc()).all()
    active_schemes = [s for s in all_schemes if s.status == 'active']
    total_monthly_commitment = 0
    for s in active_schemes:
        if s.installment_frequency == 'monthly':
            total_monthly_commitment += s.installment_amount
        elif s.installment_frequency == 'quarterly':
            total_monthly_commitment += s.installment_amount / 3
        elif s.installment_frequency == 'half-yearly':
            total_monthly_commitment += s.installment_amount / 6
        elif s.installment_frequency == 'yearly':
            total_monthly_commitment += s.installment_amount / 12

    total_invested = sum(s.total_paid for s in all_schemes)
    total_maturity = sum(s.maturity_value for s in all_schemes)
    scheme_types = Config.SCHEME_TYPES

    # Group by type
    by_type = {}
    for s in all_schemes:
        by_type.setdefault(s.scheme_type, []).append(s)

    return render_template('schemes.html',
        schemes=all_schemes,
        active_count=len(active_schemes),
        total_monthly_commitment=total_monthly_commitment,
        total_invested=total_invested,
        total_maturity=total_maturity,
        scheme_types=scheme_types,
        by_type=by_type,
        by_type_json=json.dumps([{'type': k, 'count': len(v)} for k, v in by_type.items()])
    )


@main.route('/schemes/add', methods=['POST'])
@login_required
def add_scheme():
    installment = float(request.form.get('installment_amount') or 0)
    total_inst = int(request.form.get('total_installments') or 0)
    paid_inst = int(request.form.get('paid_installments') or 0)
    scheme = Scheme(
        user_id=current_user.id,
        scheme_type=request.form['scheme_type'],
        provider=request.form['provider'],
        scheme_name=request.form['scheme_name'],
        installment_amount=installment,
        installment_frequency=request.form.get('installment_frequency', 'monthly'),
        total_installments=total_inst,
        paid_installments=paid_inst,
        total_paid=installment * paid_inst,
        maturity_value=float(request.form.get('maturity_value') or 0),
        bonus_benefit=request.form.get('bonus_benefit', ''),
        start_date=datetime.strptime(request.form['start_date'], '%Y-%m-%d').date() if request.form.get('start_date') else date.today(),
        maturity_date=datetime.strptime(request.form['maturity_date'], '%Y-%m-%d').date() if request.form.get('maturity_date') else None,
        status=request.form.get('status', 'active'),
        member=request.form.get('member', 'Self'),
        notes=request.form.get('notes', '')
    )
    db.session.add(scheme)
    db.session.commit()
    flash('Scheme added successfully!', 'success')
    return redirect(url_for('main.schemes'))


@main.route('/schemes/update/<int:id>', methods=['POST'])
@login_required
def update_scheme(id):
    scheme = Scheme.query.get_or_404(id)
    if scheme.user_id != current_user.id:
        flash('Unauthorized.', 'danger')
        return redirect(url_for('main.schemes'))
    scheme.paid_installments = int(request.form.get('paid_installments', scheme.paid_installments))
    scheme.total_paid = scheme.installment_amount * scheme.paid_installments
    scheme.status = request.form.get('status', scheme.status)
    if scheme.paid_installments >= scheme.total_installments and scheme.total_installments > 0:
        scheme.status = 'completed'
    db.session.commit()
    flash('Scheme updated!', 'success')
    return redirect(url_for('main.schemes'))


@main.route('/schemes/delete/<int:id>', methods=['POST'])
@login_required
def delete_scheme(id):
    scheme = Scheme.query.get_or_404(id)
    if scheme.user_id != current_user.id:
        flash('Unauthorized.', 'danger')
        return redirect(url_for('main.schemes'))
    db.session.delete(scheme)
    db.session.commit()
    flash('Scheme deleted.', 'info')
    return redirect(url_for('main.schemes'))


# ======================== DOCUMENT UPLOAD & SCAN ========================

def _allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS


@main.route('/policies/scan', methods=['POST'])
@login_required
def scan_policy_document():
    """Upload and scan a policy document to auto-detect fields."""
    if 'document' not in request.files:
        return jsonify({'success': False, 'message': 'No file uploaded.'})

    file = request.files['document']
    if file.filename == '':
        return jsonify({'success': False, 'message': 'No file selected.'})

    if not _allowed_file(file.filename):
        return jsonify({'success': False, 'message': 'Unsupported file type. Use PDF, PNG, JPG, or JPEG.'})

    # Save file temporarily
    os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
    filename = secure_filename(f"{current_user.id}_{secrets.token_hex(8)}_{file.filename}")
    filepath = os.path.join(Config.UPLOAD_FOLDER, filename)
    file.save(filepath)

    try:
        from .doc_parser import parse_policy_document
        result = parse_policy_document(filepath, Config.INSURANCE_PROVIDERS)
        return jsonify(result)
    finally:
        # Clean up temp file
        try:
            os.remove(filepath)
        except OSError:
            pass


@main.route('/schemes/scan', methods=['POST'])
@login_required
def scan_scheme_document():
    """Upload and scan a scheme/bond document to auto-detect fields."""
    if 'document' not in request.files:
        return jsonify({'success': False, 'message': 'No file uploaded.'})

    file = request.files['document']
    if file.filename == '':
        return jsonify({'success': False, 'message': 'No file selected.'})

    if not _allowed_file(file.filename):
        return jsonify({'success': False, 'message': 'Unsupported file type. Use PDF, PNG, JPG, or JPEG.'})

    os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
    filename = secure_filename(f"{current_user.id}_{secrets.token_hex(8)}_{file.filename}")
    filepath = os.path.join(Config.UPLOAD_FOLDER, filename)
    file.save(filepath)

    try:
        from .doc_parser import parse_scheme_document
        result = parse_scheme_document(filepath, Config.SCHEME_TYPES)
        return jsonify(result)
    finally:
        try:
            os.remove(filepath)
        except OSError:
            pass


@main.route('/policies/scan-text', methods=['POST'])
@login_required
def scan_policy_text():
    """Parse policy details from user-pasted text."""
    data = request.get_json()
    text = data.get('text', '') if data else ''
    from .doc_parser import parse_policy_from_text
    result = parse_policy_from_text(text, Config.INSURANCE_PROVIDERS)
    return jsonify(result)


@main.route('/schemes/scan-text', methods=['POST'])
@login_required
def scan_scheme_text():
    """Parse scheme details from user-pasted text."""
    data = request.get_json()
    text = data.get('text', '') if data else ''
    from .doc_parser import parse_scheme_from_text
    result = parse_scheme_from_text(text)
    return jsonify(result)


# ======================== SIP TRACKER ========================

@main.route('/sips')
@login_required
def sips():
    all_sips = SIP.query.filter_by(user_id=current_user.id).order_by(SIP.created_at.desc()).all()
    active = [s for s in all_sips if s.is_active]
    total_monthly = sum(s.sip_amount for s in active)
    total_invested = sum(s.total_invested or 0 for s in all_sips)
    total_current = sum(s.current_value or 0 for s in all_sips)

    sip_alloc = [{'fund': s.fund_name[:25], 'amount': float(s.total_invested or 0)} for s in active]

    # Include policy premiums as recurring investments
    freq_div_map = {'monthly': 1, 'quarterly': 3, 'half-yearly': 6, 'yearly': 12}
    all_policies = InsurancePolicy.query.filter_by(user_id=current_user.id).all()
    active_policies = [p for p in all_policies if p.status == 'active']
    for p in active_policies:
        fm = freq_div_map.get((p.premium_frequency or '').lower(), 12)
        monthly_amt = p.premium_amount / fm
        total_monthly += monthly_amt
        total_invested += p.total_paid or 0
        total_current += p.maturity_value or p.total_paid or 0
        sip_alloc.append({'fund': p.policy_name[:25], 'amount': float(p.total_paid or 0)})

    # Include scheme installments as recurring investments
    all_schemes = Scheme.query.filter_by(user_id=current_user.id).all()
    active_schemes = [s for s in all_schemes if s.status == 'active']
    for s in active_schemes:
        fm = freq_div_map.get((s.installment_frequency or '').lower(), 12)
        monthly_amt = s.installment_amount / fm
        total_monthly += monthly_amt
        total_invested += s.total_paid or 0
        total_current += s.maturity_value or s.total_paid or 0
        sip_alloc.append({'fund': s.scheme_name[:25], 'amount': float(s.total_paid or 0)})

    total_returns = total_current - total_invested
    active_count = len(active) + len(active_policies) + len(active_schemes)

    return render_template('sips.html',
        sips=all_sips, policies=active_policies, schemes=active_schemes,
        active_count=active_count,
        total_monthly=total_monthly, total_invested=total_invested,
        total_current=total_current, total_returns=total_returns,
        sip_by_fund=json.dumps(sip_alloc)
    )


@main.route('/sips/add', methods=['POST'])
@login_required
def add_sip():
    months = int(request.form.get('months_invested') or 0)
    sip_amount = float(request.form.get('sip_amount') or 0)
    sip = SIP(
        user_id=current_user.id,
        fund_name=request.form['fund_name'],
        platform=request.form.get('platform', ''),
        sip_amount=sip_amount,
        frequency=request.form.get('frequency', 'monthly'),
        sip_date=int(request.form.get('sip_date') or 1),
        start_date=datetime.strptime(request.form['start_date'], '%Y-%m-%d').date() if request.form.get('start_date') else date.today(),
        expected_return=float(request.form.get('expected_return') or 12.0),
        total_invested=sip_amount * months,
        current_value=float(request.form.get('current_value') or 0),
        member=request.form.get('member', 'Self'),
        notes=request.form.get('notes', '')
    )
    db.session.add(sip)
    db.session.commit()
    flash('SIP added!', 'success')
    return redirect(url_for('main.sips'))


@main.route('/sips/update/<int:id>', methods=['POST'])
@login_required
def update_sip(id):
    sip = SIP.query.get_or_404(id)
    if sip.user_id != current_user.id:
        flash('Unauthorized.', 'danger')
        return redirect(url_for('main.sips'))
    sip.current_value = float(request.form.get('current_value') or sip.current_value)
    sip.total_invested = float(request.form.get('total_invested') or sip.total_invested)
    sip.is_active = request.form.get('is_active') != '0'
    db.session.commit()
    flash('SIP updated!', 'success')
    return redirect(url_for('main.sips'))


@main.route('/sips/delete/<int:id>', methods=['POST'])
@login_required
def delete_sip(id):
    sip = SIP.query.get_or_404(id)
    if sip.user_id != current_user.id:
        flash('Unauthorized.', 'danger')
        return redirect(url_for('main.sips'))
    db.session.delete(sip)
    db.session.commit()
    flash('SIP deleted.', 'info')
    return redirect(url_for('main.sips'))


# ======================== BUDGET PLANNER ========================

@main.route('/budget')
@login_required
def budget():
    current_month = date.today().strftime('%Y-%m')
    month_param = request.args.get('month', current_month)

    # Get budgets for selected month
    budgets = Budget.query.filter_by(user_id=current_user.id, month=month_param).all()
    budget_map = {b.category: b.planned_amount for b in budgets}

    # Auto-init from 50/30/20 if no budget set for this month
    if not budgets and current_user.monthly_salary > 0:
        salary = current_user.monthly_salary
        defaults = {
            'Housing': salary * 0.25, 'Food & Groceries': salary * 0.15,
            'Transportation': salary * 0.05, 'Utilities': salary * 0.05,
            'Healthcare': salary * 0.03, 'Insurance': salary * 0.05,
            'Education': salary * 0.02, 'Entertainment': salary * 0.05,
            'Shopping': salary * 0.05, 'Personal Care': salary * 0.02,
            'Debt Payments': salary * 0.05, 'Savings': salary * 0.10,
            'Investments': salary * 0.10, 'Charity': salary * 0.01,
            'Miscellaneous': salary * 0.02
        }
        budget_map = defaults

    # Actual spending for selected month
    y, m = int(month_param.split('-')[0]), int(month_param.split('-')[1])
    actuals = db.session.query(
        Expense.category, db.func.sum(Expense.amount)
    ).filter(
        Expense.user_id == current_user.id,
        db.extract('month', Expense.date) == m,
        db.extract('year', Expense.date) == y
    ).group_by(Expense.category).all()
    actual_map = {cat: float(amt) for cat, amt in actuals}

    categories = Config.EXPENSE_CATEGORIES
    budget_data = []
    total_planned = 0
    total_actual = 0
    for cat in categories:
        planned = budget_map.get(cat, 0)
        actual = actual_map.get(cat, 0)
        total_planned += planned
        total_actual += actual
        pct = (actual / planned * 100) if planned > 0 else 0
        budget_data.append({
            'category': cat, 'planned': planned, 'actual': actual,
            'pct': min(pct, 100), 'over': actual > planned
        })

    return render_template('budget.html',
        month=month_param, budget_data=budget_data,
        total_planned=total_planned, total_actual=total_actual,
        categories=categories, salary=current_user.monthly_salary
    )


@main.route('/budget/save', methods=['POST'])
@login_required
def save_budget():
    month = request.form.get('month', date.today().strftime('%Y-%m'))
    categories = Config.EXPENSE_CATEGORIES

    # Delete existing budgets for this month
    Budget.query.filter_by(user_id=current_user.id, month=month).delete()

    for cat in categories:
        amt = float(request.form.get(f'budget_{cat}', 0))
        if amt > 0:
            db.session.add(Budget(
                user_id=current_user.id, month=month,
                category=cat, planned_amount=amt
            ))
    db.session.commit()
    flash('Budget saved!', 'success')
    return redirect(url_for('main.budget', month=month))


# ======================== TAX PLANNING ========================

@main.route('/tax')
@login_required
def tax_planning():
    # Section 80C — ₹1,50,000 limit
    # Eligible: PPF, EPF, ELSS MF, NSC, Life Insurance premiums, Sukanya, Tax-saver FD, NPS (extra 50K under 80CCD)
    sec80c_types = {'PPF', 'EPF', 'ELSS', 'NPS', 'NSC', 'Tax-Saver FD'}
    sec80c_inv = db.session.query(db.func.sum(Investment.amount_invested)).filter(
        Investment.user_id == current_user.id,
        Investment.investment_type.in_(sec80c_types)
    ).scalar() or 0

    # Life insurance premiums (annual total)
    active_policies = InsurancePolicy.query.filter_by(user_id=current_user.id, status='active').all()
    freq_map = {'monthly': 12, 'quarterly': 4, 'half-yearly': 2, 'yearly': 1}
    annual_premiums = sum(
        p.premium_amount * freq_map.get((p.premium_frequency or '').lower(), 1)
        for p in active_policies
        if p.policy_type in ('Term Life', 'Whole Life', 'Endowment', 'ULIP', 'Money Back', 'Child Plan')
    )

    # Scheme-based 80C: NSC, Sukanya, KVP
    sec80c_schemes = {'NSC', 'Sukanya Samriddhi', 'Kisan Vikas Patra'}
    scheme_80c = sum(
        s.total_paid or 0 for s in Scheme.query.filter_by(user_id=current_user.id).all()
        if s.scheme_type in sec80c_schemes
    )

    total_80c = sec80c_inv + annual_premiums + scheme_80c
    limit_80c = 150000

    # Section 80D — Health Insurance: ₹25,000 self, ₹50,000 parents (senior)
    health_premiums = sum(
        p.premium_amount * freq_map.get((p.premium_frequency or '').lower(), 1)
        for p in active_policies
        if p.policy_type in ('Health Insurance', 'Critical Illness')
    )
    limit_80d = 25000

    # NPS extra 80CCD(1B): ₹50,000
    nps_inv = db.session.query(db.func.sum(Investment.amount_invested)).filter(
        Investment.user_id == current_user.id,
        Investment.investment_type == 'NPS'
    ).scalar() or 0
    limit_nps = 50000

    # Build 80C breakdown
    breakdown_80c = []
    if sec80c_inv > 0:
        for typ in sec80c_types:
            amt = db.session.query(db.func.sum(Investment.amount_invested)).filter(
                Investment.user_id == current_user.id,
                Investment.investment_type == typ
            ).scalar() or 0
            if amt > 0:
                breakdown_80c.append({'item': typ, 'amount': amt})
    if annual_premiums > 0:
        breakdown_80c.append({'item': 'Life Insurance Premiums', 'amount': annual_premiums})
    if scheme_80c > 0:
        for st in sec80c_schemes:
            amt = sum(s.total_paid or 0 for s in Scheme.query.filter_by(user_id=current_user.id).all() if s.scheme_type == st)
            if amt > 0:
                breakdown_80c.append({'item': st, 'amount': amt})

    annual_income = current_user.annual_salary or (current_user.monthly_salary * 12)

    return render_template('tax.html',
        total_80c=total_80c, limit_80c=limit_80c,
        health_premiums=health_premiums, limit_80d=limit_80d,
        nps_inv=nps_inv, limit_nps=limit_nps,
        breakdown_80c=breakdown_80c,
        annual_income=annual_income,
        tax_saved_80c=min(total_80c, limit_80c) * 0.3,  # Approx 30% slab
        tax_saved_80d=min(health_premiums, limit_80d) * 0.3,
    )


# ======================== GOVERNMENT SCHEMES ========================

@main.route('/govt-schemes')
@login_required
def govt_schemes():
    return render_template('govt_schemes.html')


# ======================== INDIAN BUDGET ========================

@main.route('/indian-budget')
@login_required
def indian_budget():
    return render_template('indian_budget.html')


# ======================== LOANS ========================

@main.route('/loans')
@login_required
def loans():
    all_loans = Loan.query.filter_by(user_id=current_user.id).order_by(Loan.is_active.desc(), Loan.start_date.desc()).all()
    monthly_salary = current_user.monthly_salary or 0
    total_debts = sum(l.outstanding_balance or 0 for l in all_loans if l.is_active)

    # AI analysis for each loan
    loan_data = []
    for loan in all_loans:
        analysis = advisor.analyze_loan(
            loan.loan_type, loan.principal_amount, loan.interest_rate,
            loan.tenure_months, loan.emi_amount, loan.paid_months or 0, monthly_salary
        )
        progress = (loan.paid_months / loan.tenure_months * 100) if loan.tenure_months > 0 else 0
        loan_data.append({
            'loan': loan,
            'analysis': analysis,
            'progress': round(progress, 1)
        })

    # Credit card offers
    cc_offers = advisor.get_credit_card_offers(monthly_salary, total_debts)

    # Summary
    active_loans = [l for l in all_loans if l.is_active]
    total_emi = sum(l.emi_amount for l in active_loans)
    total_outstanding = sum(l.outstanding_balance or 0 for l in active_loans)
    total_principal = sum(l.principal_amount for l in active_loans)
    total_paid_amount = sum(l.total_paid or 0 for l in all_loans)

    return render_template('loans.html',
        loan_data=loan_data,
        cc_offers=cc_offers,
        total_emi=total_emi,
        total_outstanding=total_outstanding,
        total_principal=total_principal,
        total_paid_amount=total_paid_amount,
        active_count=len(active_loans),
        total_count=len(all_loans),
        monthly_salary=monthly_salary,
    )


@main.route('/add-loan', methods=['POST'])
@login_required
def add_loan():
    principal = float(request.form.get('principal_amount') or 0)
    interest_rate = float(request.form.get('interest_rate') or 0)
    tenure_months = int(request.form.get('tenure_months') or 0)
    emi_amount = float(request.form.get('emi_amount') or 0)

    # Auto-calculate EMI if not provided
    if emi_amount == 0 and principal > 0 and interest_rate > 0 and tenure_months > 0:
        r = interest_rate / 12 / 100
        emi_amount = principal * r * (1 + r) ** tenure_months / ((1 + r) ** tenure_months - 1)
        emi_amount = round(emi_amount, 2)

    paid_months = int(request.form.get('paid_months') or 0)
    total_paid = emi_amount * paid_months
    outstanding = (emi_amount * (tenure_months - paid_months)) if tenure_months > paid_months else 0

    start_date_str = request.form.get('start_date')
    start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date() if start_date_str else date.today()

    end_date = start_date + relativedelta(months=tenure_months)

    loan = Loan(
        user_id=current_user.id,
        loan_type=request.form.get('loan_type', 'Personal'),
        lender=request.form.get('lender', '').strip(),
        loan_name=request.form.get('loan_name', '').strip(),
        principal_amount=principal,
        interest_rate=interest_rate,
        tenure_months=tenure_months,
        emi_amount=emi_amount,
        paid_months=paid_months,
        total_paid=total_paid,
        outstanding_balance=outstanding,
        start_date=start_date,
        end_date=end_date,
        emi_day=int(request.form.get('emi_day') or 5),
        notes=request.form.get('notes', '').strip()
    )
    db.session.add(loan)
    db.session.commit()
    flash('Loan added successfully!', 'success')
    return redirect(url_for('main.loans'))


@main.route('/record-loan-payment/<int:id>', methods=['POST'])
@login_required
def record_loan_payment(id):
    loan = Loan.query.get_or_404(id)
    if loan.user_id != current_user.id:
        flash('Unauthorized', 'danger')
        return redirect(url_for('main.loans'))

    loan.paid_months = (loan.paid_months or 0) + 1
    loan.total_paid = loan.emi_amount * loan.paid_months
    remaining = loan.tenure_months - loan.paid_months
    loan.outstanding_balance = loan.emi_amount * remaining if remaining > 0 else 0

    if loan.paid_months >= loan.tenure_months:
        loan.is_active = False
        loan.outstanding_balance = 0
        flash(f'Congratulations! {loan.loan_name} is fully paid off!', 'success')
    else:
        flash(f'Payment recorded for {loan.loan_name}. {remaining} EMIs remaining.', 'success')

    db.session.commit()
    return redirect(url_for('main.loans'))


@main.route('/delete-loan/<int:id>', methods=['POST'])
@login_required
def delete_loan(id):
    loan = Loan.query.get_or_404(id)
    if loan.user_id != current_user.id:
        flash('Unauthorized', 'danger')
        return redirect(url_for('main.loans'))
    db.session.delete(loan)
    db.session.commit()
    flash('Loan deleted.', 'success')
    return redirect(url_for('main.loans'))


# ======================== GOLD & SILVER RATES ========================

@main.route('/gold-silver')
@login_required
def gold_silver():
    from .ibja_rates import fetch_ibja_rates
    live = fetch_ibja_rates()

    if live.get('success'):
        gold_data = {}
        for karat in ['24K', '22K', '18K']:
            g = live['gold'][karat]
            price = g['price_per_gram'] or 0
            history_day = live.get('gold_history', [])
            prev_price = history_day[-2][karat] if len(history_day) >= 2 else price
            change = price - prev_price
            change_pct = (change / prev_price * 100) if prev_price else 0
            avg = sum(h[karat] for h in history_day) / len(history_day) if history_day else price
            trend = 'Bullish' if price >= avg else 'Bearish'

            gold_data[karat] = {
                'current_price': price,
                'price_10g': g['price_per_10g'] or round(price * 10, 2),
                'purity': g['purity'],
                'change': round(change, 2),
                'change_pct': round(change_pct, 2),
                'trend': trend,
                'history_day': [{'date': h['date'], 'price': h[karat]} for h in history_day],
                'history_month': [{'date': h['date'], 'price': h[karat]} for h in live.get('gold_history_month', [])],
                'history_year': [{'date': h['date'], 'price': h[karat]} for h in live.get('gold_history_year', [])],
            }

        # Additional purities
        extra_purities = {}
        for key in ['995', '585']:
            g = live['gold'].get(key, {})
            if g.get('price_per_gram'):
                extra_purities[key] = {
                    'price_per_gram': g['price_per_gram'],
                    'price_per_10g': g['price_per_10g'],
                    'purity': g['purity'],
                }

        # Silver
        s = live['silver']
        s_price = s['price_per_gram'] or 0
        s_history_day = live.get('silver_history', [])
        s_prev = s_history_day[-2]['price'] if len(s_history_day) >= 2 else s_price
        s_change = s_price - s_prev
        s_change_pct = (s_change / s_prev * 100) if s_prev else 0
        s_avg = sum(h['price'] for h in s_history_day) / len(s_history_day) if s_history_day else s_price
        s_trend = 'Bullish' if s_price >= s_avg else 'Bearish'

        # Platinum
        pt = live.get('platinum', {})
        pt_price = pt.get('price_per_gram') or 0

        # Tips
        gold_tips = []
        if gold_data['24K']['trend'] == 'Bullish':
            gold_tips.append('Gold prices trending up — good if already invested, wait for dip to buy more')
            gold_tips.append('Consider Sovereign Gold Bonds for 2.5% extra annual returns')
        else:
            gold_tips.append('Gold prices trending down — good buying opportunity')
            gold_tips.append('Consider SIP-style gold investment via Gold ETF/SGB')
        gold_tips.append('22K gold is best for jewelry, 24K for investment (coins/bars/ETFs)')

        silver_tips = []
        if s_trend == 'Bullish':
            silver_tips.append('Silver showing upward trend — industrial demand driving prices')
        else:
            silver_tips.append('Silver dipping — accumulate for long-term as industrial metal')

        analysis = {
            'gold': gold_data,
            'gold_tips': gold_tips,
            'extra_purities': extra_purities,
            'silver': {
                'current_price': s_price,
                'unit': 'per gram',
                'price_kg': s['price_per_kg'] or round(s_price * 1000, 2),
                'change': round(s_change, 2),
                'change_pct': round(s_change_pct, 2),
                'trend': s_trend,
                'history_day': s_history_day,
                'history_month': live.get('silver_history_month', []),
                'history_year': live.get('silver_history_year', []),
                'tips': silver_tips,
            },
            'platinum': {
                'price_per_gram': pt_price,
                'price_per_10g': pt.get('price_per_10g') or round(pt_price * 10, 2),
            },
            'am_pm_data': live.get('am_pm_data', []),
            'chart_data_points': live.get('chart_data_points', 0),
            'last_updated': live['last_updated'],
            'source': live['source'],
            'live': True,
        }
    else:
        analysis = advisor.get_gold_silver_analysis()
        analysis['source'] = 'Simulated (IBJA unavailable)'
        analysis['live'] = False
        analysis['am_pm_data'] = []
        analysis['extra_purities'] = {}
        analysis['chart_data_points'] = 0

    return render_template('gold_silver.html', analysis=analysis)


@main.route('/api/live-rates')
@login_required
def api_live_rates():
    """API endpoint for AJAX refresh of live rates."""
    from .ibja_rates import fetch_ibja_rates
    live = fetch_ibja_rates()
    return jsonify(live)


# ======================== RATE MONITOR ========================

@main.route('/rate-monitor')
@login_required
def rate_monitor():
    from .rate_monitor import get_rate_summary
    rates = get_rate_summary()
    return render_template('rate_monitor.html', rates=rates)


# ======================== HELP & USER GUIDE ========================

# ======================== FEEDBACK & RATING ========================

@main.route('/feedback', methods=['GET', 'POST'])
@login_required
def feedback():
    if request.method == 'POST':
        rating = request.form.get('rating', type=int)
        category = request.form.get('category', 'General').strip()
        message = request.form.get('message', '').strip()

        if not rating or rating < 1 or rating > 5:
            flash('Please select a rating (1-5 stars).', 'danger')
            return redirect(url_for('main.feedback'))
        if not message:
            flash('Please enter your feedback message.', 'danger')
            return redirect(url_for('main.feedback'))

        fb = Feedback(
            user_id=current_user.id,
            rating=rating,
            category=category,
            message=message[:1000]
        )
        db.session.add(fb)
        db.session.commit()
        flash('Thank you for your feedback!', 'success')
        return redirect(url_for('main.feedback'))

    my_feedbacks = Feedback.query.filter_by(user_id=current_user.id).order_by(Feedback.created_at.desc()).all()
    return render_template('feedback.html', feedbacks=my_feedbacks)


@main.route('/help')
@login_required
def help_guide():
    return render_template('help_guide.html')


@main.route('/privacy-policy')
def privacy_policy():
    return render_template('privacy_policy.html')


@main.route('/terms-of-service')
def terms_of_service():
    return render_template('terms_of_service.html')


# ======================== DUE REMINDERS ========================

@main.route('/send-reminders', methods=['POST'])
@login_required
def send_reminders():
    """Send email reminders for dues coming up in the next 7 days."""
    from flask_mail import Message
    from . import mail

    today = date.today()
    week_ahead = today + timedelta(days=7)
    freq_map = {'monthly': 1, 'quarterly': 3, 'half-yearly': 6, 'yearly': 12}
    dues = []

    for p in InsurancePolicy.query.filter_by(user_id=current_user.id, status='active').all():
        if not p.start_date:
            continue
        fm = freq_map.get((p.premium_frequency or '').lower(), 12)
        d = p.start_date
        while d < today:
            d = d + relativedelta(months=fm)
        if d <= week_ahead:
            dues.append(f"Premium: {p.policy_name} ({p.provider}) — ₹{p.premium_amount:,.0f} due {d.strftime('%d %b %Y')}")

    for s in Scheme.query.filter_by(user_id=current_user.id, status='active').all():
        if not s.start_date:
            continue
        fm = freq_map.get((s.installment_frequency or '').lower(), 12)
        d = s.start_date
        while d < today:
            d = d + relativedelta(months=fm)
        if d <= week_ahead:
            dues.append(f"Installment: {s.scheme_name} ({s.provider}) — ₹{s.installment_amount:,.0f} due {d.strftime('%d %b %Y')}")

    for sip in SIP.query.filter_by(user_id=current_user.id, is_active=True).all():
        if not sip.start_date:
            continue
        d = sip.start_date
        while d < today:
            d = d + relativedelta(months=1)
        if d <= week_ahead:
            dues.append(f"SIP: {sip.fund_name} ({sip.platform or 'N/A'}) — ₹{sip.sip_amount:,.0f} due {d.strftime('%d %b %Y')}")

    if not dues:
        return jsonify(success=True, message='No dues in the next 7 days.')

    body = f"Hi {current_user.full_name or current_user.username},\n\nYou have {len(dues)} upcoming payment(s) in the next 7 days:\n\n"
    body += '\n'.join(f"  • {d}" for d in dues)
    body += '\n\n— WealthPilot'

    try:
        msg = Message(
            subject=f'[WealthPilot] {len(dues)} Payment Reminder(s)',
            recipients=[current_user.email],
            body=body
        )
        mail.send(msg)
        return jsonify(success=True, message=f'Reminder sent to {current_user.email} — {len(dues)} due(s)')
    except Exception as e:
        return jsonify(success=True, message=f'{len(dues)} dues found. Email not sent (mail not configured). Dues: {"; ".join(dues)}')


# ======================== NOTIFICATIONS ========================

def _generate_notifications(user):
    """Auto-generate notifications for the user based on their financial data."""
    today = date.today()
    new_notifs = []

    # Policy premium due in next 7 days
    policies = InsurancePolicy.query.filter_by(user_id=user.id, status='active').all()
    for p in policies:
        if p.premium_due_day:
            # Check if due day is within next 7 days
            try:
                due_date = today.replace(day=p.premium_due_day)
                if due_date < today:
                    due_date = (due_date + relativedelta(months=1))
                days_until = (due_date - today).days
                if 0 <= days_until <= 7:
                    # Check if we already sent this notification this month
                    existing = Notification.query.filter(
                        Notification.user_id == user.id,
                        Notification.title.contains(p.policy_name or 'Policy'),
                        Notification.created_at >= today.replace(day=1)
                    ).first()
                    if not existing:
                        new_notifs.append(Notification(
                            user_id=user.id,
                            title=f'Premium Due: {p.policy_name or p.provider}',
                            message=f'₹{p.premium_amount:,.0f} premium due in {days_until} days (day {p.premium_due_day})',
                            category='warning', icon='shield', link='/policies'
                        ))
            except (ValueError, AttributeError):
                pass

    # Loan EMI due in next 7 days
    loans = Loan.query.filter_by(user_id=user.id).all()
    for loan in loans:
        if loan.emi_day and loan.outstanding_balance and loan.outstanding_balance > 0:
            try:
                due_date = today.replace(day=loan.emi_day)
                if due_date < today:
                    due_date = (due_date + relativedelta(months=1))
                days_until = (due_date - today).days
                if 0 <= days_until <= 7:
                    existing = Notification.query.filter(
                        Notification.user_id == user.id,
                        Notification.title.contains(loan.loan_name or loan.lender or 'Loan'),
                        Notification.created_at >= today.replace(day=1)
                    ).first()
                    if not existing:
                        new_notifs.append(Notification(
                            user_id=user.id,
                            title=f'EMI Due: {loan.loan_name or loan.lender}',
                            message=f'₹{loan.emi_amount:,.0f} EMI due in {days_until} days',
                            category='danger', icon='credit_score', link='/loans'
                        ))
            except (ValueError, AttributeError):
                pass

    # Goal deadline approaching (within 30 days) - optional non-critical alert
    if not getattr(user, 'enable_only_critical_notifications', False):
        goals = FinancialGoal.query.filter_by(user_id=user.id).all()
        for goal in goals:
            if goal.target_date:
                days_left = (goal.target_date - today).days
                if 0 < days_left <= 30 and goal.current_saved < goal.target_amount:
                    remaining = goal.target_amount - goal.current_saved
                    existing = Notification.query.filter(
                        Notification.user_id == user.id,
                        Notification.title.contains(goal.goal_name),
                        Notification.created_at >= today - timedelta(days=7)
                    ).first()
                    if not existing:
                        new_notifs.append(Notification(
                            user_id=user.id,
                            title=f'Goal Deadline: {goal.goal_name}',
                            message=f'₹{remaining:,.0f} remaining with {days_left} days left',
                            category='info', icon='flag', link='/goals'
                        ))

    # SIP reminder (day of month)
    sips = SIP.query.filter_by(user_id=user.id).all()
    for sip in sips:
        if sip.sip_date:
            try:
                due_date = today.replace(day=sip.sip_date)
                if due_date < today:
                    due_date = (due_date + relativedelta(months=1))
                days_until = (due_date - today).days
                if 0 <= days_until <= 3:
                    existing = Notification.query.filter(
                        Notification.user_id == user.id,
                        Notification.title.contains(sip.fund_name),
                        Notification.created_at >= today.replace(day=1)
                    ).first()
                    if not existing:
                        new_notifs.append(Notification(
                            user_id=user.id,
                            title=f'SIP Due: {sip.fund_name}',
                            message=f'₹{sip.sip_amount:,.0f} SIP investment due in {days_until} days',
                            category='info', icon='auto_graph', link='/sips'
                        ))
            except (ValueError, AttributeError):
                pass

    # Future Planner monthly reminder (once per month)
    month_start = today.replace(day=1)
    target_year = user.future_target_year or 2040
    monthly_title = f'Future Planner {target_year}+ Monthly Check'
    future_existing = Notification.query.filter(
        Notification.user_id == user.id,
        Notification.title == monthly_title,
        Notification.created_at >= month_start
    ).first()
    if getattr(user, 'enable_future_monthly_reminders', True) and not future_existing:
        monthly_salary = float(user.monthly_salary or 0)
        future = advisor.get_future_readiness_plan(
            monthly_salary=monthly_salary,
            age=user.age or 30,
            risk_appetite=user.risk_appetite or 'moderate',
            target_year=target_year,
        )
        target = float(future['plan']['monthly_investment_target'])
        bank_balance = db.session.query(db.func.sum(BankAccount.balance)).filter_by(user_id=user.id).scalar() or 0
        suggested_topup = max(0.0, target - (monthly_salary * 0.10)) if monthly_salary > 0 else target

        new_notifs.append(Notification(
            user_id=user.id,
            title=monthly_title,
            message=(
                f"Target year: {target_year}. "
                f"Monthly target: ₹{target:,.0f}. "
                f"Bank reserve: ₹{float(bank_balance):,.0f}. "
                f"Suggested top-up: ₹{float(suggested_topup):,.0f}."
            ),
            category='info',
            icon='rocket_launch',
            link='/future-planner'
        ))

    # Future Planner quarterly review reminder (once per quarter)
    quarter = ((today.month - 1) // 3) + 1
    quarter_start_month = ((quarter - 1) * 3) + 1
    quarter_start = date(today.year, quarter_start_month, 1)
    quarter_title = f'Future Planner {target_year}+ Q{quarter} Review'
    quarter_existing = Notification.query.filter(
        Notification.user_id == user.id,
        Notification.title == quarter_title,
        Notification.created_at >= quarter_start
    ).first()
    if getattr(user, 'enable_future_quarterly_reminders', True) and not quarter_existing:
        quarter_actions = {
            1: 'Rebalance allocation and update annual income growth assumptions.',
            2: 'Increase SIP/top-up by 5-10% and review emergency fund coverage.',
            3: 'Review debt burden and reduce high-interest liabilities aggressively.',
            4: f'Run year-end audit: net worth, corpus progress, and {target_year} target gap.',
        }
        action = quarter_actions.get(quarter, 'Review your 2040 roadmap and adjust monthly contributions.')

        new_notifs.append(Notification(
            user_id=user.id,
            title=quarter_title,
            message=f'Quarterly review due. {action}',
            category='info',
            icon='event_note',
            link='/future-planner'
        ))

    if new_notifs:
        db.session.add_all(new_notifs)
        db.session.commit()


@main.route('/notifications')
@login_required
def notifications():
    _generate_notifications(current_user)
    notifs = Notification.query.filter_by(user_id=current_user.id).order_by(Notification.created_at.desc()).limit(50).all()
    unread = sum(1 for n in notifs if not n.is_read)
    return render_template('notifications.html', notifications=notifs, unread_count=unread)


@main.route('/notifications/read/<int:id>', methods=['POST'])
@login_required
def mark_notification_read(id):
    notif = Notification.query.get_or_404(id)
    if notif.user_id != current_user.id:
        return jsonify(success=False), 403
    notif.is_read = True
    db.session.commit()
    if notif.link:
        return redirect(notif.link)
    return redirect(url_for('main.notifications'))


@main.route('/notifications/read-all', methods=['POST'])
@login_required
def mark_all_notifications_read():
    Notification.query.filter_by(user_id=current_user.id, is_read=False).update({'is_read': True})
    db.session.commit()
    flash('All notifications marked as read.', 'success')
    return redirect(url_for('main.notifications'))


@main.route('/notifications/count')
@login_required
def notification_count():
    try:
        _generate_notifications(current_user)
        count = Notification.query.filter_by(user_id=current_user.id, is_read=False).count()
        return jsonify(count=count)
    except OperationalError:
        db.session.rollback()
        return jsonify(count=0)
