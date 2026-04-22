"""
WealthPilot - AI-Powered Financial Management Application
Flask Application Package
"""
import os
import json
import logging
from datetime import datetime, timezone
from flask import Flask, render_template, session, request
from flask_login import LoginManager, current_user
from flask_mail import Mail
from flask_wtf.csrf import CSRFProtect
from flask_limiter import Limiter
from flask_migrate import Migrate
from werkzeug.security import generate_password_hash
from sqlalchemy import text
from .models import db
from .config import Config


def _get_real_ip():
    """Return client IP behind reverse proxy (Render / nginx)."""
    forwarded = request.headers.get('X-Forwarded-For', '')
    if forwarded:
        return forwarded.split(',')[0].strip()
    return request.remote_addr or '127.0.0.1'


login_manager = LoginManager()
login_manager.login_view = 'main.login'
login_manager.login_message_category = 'info'

mail = Mail()
csrf = CSRFProtect()
limiter = Limiter(key_func=_get_real_ip, default_limits=["200 per minute"])
migrate = Migrate()


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # ── Session cookie security ──
    app.config.setdefault('SESSION_COOKIE_SECURE', not app.debug)
    app.config.setdefault('SESSION_COOKIE_HTTPONLY', True)
    app.config.setdefault('SESSION_COOKIE_SAMESITE', 'Lax')

    # ── Logging ──
    log_level = logging.DEBUG if app.debug else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
    )
    app.logger.setLevel(log_level)
    app.logger.info('WealthPilot starting up...')

    # Load saved mail config before initializing Flask-Mail
    # Priority: JSON file (with valid username) > environment variables > config.py defaults
    mail_config_path = os.path.join(app.instance_path, 'mail_config.json')
    cfg = None
    if os.path.exists(mail_config_path):
        with open(mail_config_path, 'r') as f:
            loaded = json.load(f)
        if loaded.get('mail_username'):
            cfg = loaded
    if not cfg and os.environ.get('MAIL_USERNAME'):
        cfg = {
            'mail_server': os.environ.get('MAIL_SERVER', 'smtp.gmail.com'),
            'mail_port': int(os.environ.get('MAIL_PORT', 587)),
            'mail_use_tls': True,
            'mail_username': os.environ['MAIL_USERNAME'],
            'mail_password': os.environ.get('MAIL_PASSWORD', ''),
            'mail_default_sender': os.environ.get('MAIL_DEFAULT_SENDER', os.environ['MAIL_USERNAME']),
        }
    if cfg and cfg.get('mail_username'):
        app.config['MAIL_SERVER'] = cfg.get('mail_server', 'smtp.gmail.com')
        app.config['MAIL_PORT'] = int(cfg.get('mail_port', 587))
        app.config['MAIL_USE_TLS'] = cfg.get('mail_use_tls', True)
        app.config['MAIL_USE_SSL'] = False
        app.config['MAIL_USERNAME'] = cfg['mail_username']
        app.config['MAIL_PASSWORD'] = cfg.get('mail_password', '')
        app.config['MAIL_DEFAULT_SENDER'] = cfg.get('mail_default_sender', cfg['mail_username'])

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    mail.init_app(app)
    csrf.init_app(app)
    limiter.init_app(app)

    # Register Jinja2 globals
    app.jinja_env.globals.update(min=min, max=max)

    # Price tracker platform helpers for templates
    from .price_tracker import PLATFORM_COLORS, PLATFORM_ICONS
    app.jinja_env.globals['platform_color'] = lambda p: PLATFORM_COLORS.get(p, '#6c757d')
    app.jinja_env.globals['platform_icon'] = lambda p: PLATFORM_ICONS.get(p, 'link')

    # Indian currency format filter: 462924 → 4,62,924
    def indian_format(value):
        try:
            value = float(value)
        except (ValueError, TypeError):
            return '0'
        is_neg = value < 0
        value = abs(value)
        s = '{:.0f}'.format(value)
        if len(s) <= 3:
            result = s
        else:
            last3 = s[-3:]
            rest = s[:-3]
            # Group rest in 2-digit chunks from right
            groups = []
            while rest:
                groups.insert(0, rest[-2:])
                rest = rest[:-2]
            result = ','.join(groups) + ',' + last3
        return ('-' + result) if is_neg else result

    app.jinja_env.filters['inr'] = indian_format

    # Multi-language context processor
    from .translations import get_translator, LANGUAGES
    from flask_login import current_user as _cu

    @app.context_processor
    def inject_translations():
        lang = 'en'
        subscription_banner = None
        user_plan_code = 'starter'
        try:
            if _cu and _cu.is_authenticated:
                lang = getattr(_cu, 'language', 'en') or 'en'

                # Cache plan lookup in session to avoid DB query on every request
                cached = session.get('_cached_plan')
                if cached and cached.get('uid') == _cu.id:
                    user_plan_code = cached['plan']
                    current_plan = cached['plan_name']
                else:
                    from .models import PaymentTransaction
                    now_utc = datetime.now(timezone.utc)
                    latest_paid = PaymentTransaction.query.filter(
                        PaymentTransaction.user_id == _cu.id,
                        PaymentTransaction.status == 'paid',
                        db.or_(PaymentTransaction.expires_at.is_(None), PaymentTransaction.expires_at > now_utc)
                    ).order_by(PaymentTransaction.paid_at.desc()).first()

                    current_plan = 'Free'
                    if _cu.is_admin:
                        user_plan_code = 'family_monthly'
                        current_plan = 'Admin (Full Access)'
                    elif latest_paid and latest_paid.plan_code == 'pro_monthly':
                        user_plan_code = 'pro_monthly'
                        current_plan = 'WealthPilot Pro'
                    elif latest_paid and latest_paid.plan_code == 'family_monthly':
                        user_plan_code = 'family_monthly'
                        current_plan = 'WealthPilot Family'
                    elif latest_paid:
                        current_plan = latest_paid.plan_code

                    session['_cached_plan'] = {'uid': _cu.id, 'plan': user_plan_code, 'plan_name': current_plan}

                suggestion = None
                if user_plan_code == 'starter':
                    suggestion = {
                        'plan_code': 'pro_monthly',
                        'plan_name': 'WealthPilot Pro',
                        'price': '₹99/month',
                        'reason': 'unlock premium analytics and faster wealth insights',
                    }
                elif user_plan_code == 'pro_monthly':
                    suggestion = {
                        'plan_code': 'family_monthly',
                        'plan_name': 'WealthPilot Family',
                        'price': '₹199/month',
                        'reason': 'add family members and shared financial dashboards',
                    }

                if suggestion:
                    banner_key = f"sub-banner-{_cu.id}-{current_plan}-{suggestion['plan_code']}"
                    subscription_banner = {
                        'current_plan': current_plan,
                        'suggested_plan': suggestion['plan_name'],
                        'price': suggestion['price'],
                        'reason': suggestion['reason'],
                        'pricing_url': '/pricing',
                        'banner_key': banner_key,
                    }
        except Exception as e:
            db.session.rollback()
            app.logger.warning(f'Subscription banner skipped due to transient error: {e}')

        # Plan level helper for sidebar lock icons
        plan_levels = {'starter': 0, 'free': 0, 'pro_monthly': 1, 'family_monthly': 2}
        user_level = plan_levels.get(user_plan_code, 0)

        def has_access(endpoint):
            """Check if current user's plan allows access to endpoint."""
            from .routes import MODULE_PLAN_REQUIREMENTS
            req = MODULE_PLAN_REQUIREMENTS.get(endpoint, 'starter')
            return user_level >= plan_levels.get(req, 0)

        return {
            't': get_translator(lang),
            'current_lang': lang,
            'LANGUAGES': LANGUAGES,
            'subscription_banner': subscription_banner,
            'user_plan': user_plan_code,
            'has_access': has_access,
        }

    # User loader
    from .models import User

    @login_manager.user_loader
    def load_user(user_id):
        try:
            return db.session.get(User, int(user_id))
        except Exception as e:
            db.session.rollback()
            app.logger.warning(f'User loader failed for id={user_id}: {e}')
            return None

    # Register blueprint
    from .routes import main
    app.register_blueprint(main)

    # Security headers
    @app.after_request
    def set_security_headers(response):
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response.headers['Content-Security-Policy'] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net https://*.razorpay.com; "
            "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com https://fonts.googleapis.com; "
            "img-src 'self' data: blob: https://*.razorpay.com; "
            "connect-src 'self' https://*.razorpay.com; "
            "frame-src 'self' https://*.razorpay.com; "
            "form-action 'self' https://*.razorpay.com;"
        )

        # Prevent browser back-button from showing stale authenticated pages.
        try:
            endpoint = request.endpoint or ''
            sensitive_endpoints = {
                'main.login',
                'main.logout',
                'main.dashboard',
                'main.verify_login_otp',
                'main.verify_otp',
                'main.reset_password',
                'main.verify_change_password_otp',
                'main.verify_email_change_otp',
            }
            if current_user.is_authenticated or endpoint in sensitive_endpoints:
                response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0, private'
                response.headers['Pragma'] = 'no-cache'
                response.headers['Expires'] = '0'
        except Exception:
            pass

        if not app.debug:
            response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        return response

    # Session idle timeout
    @app.before_request
    def check_session_timeout():
        try:
            if current_user.is_authenticated:
                # Force-logout users disabled by admin
                if not current_user.is_active:
                    from flask_login import logout_user
                    from flask import flash, redirect, url_for
                    logout_user()
                    session.clear()
                    flash('Your account has been disabled. Contact admin.', 'danger')
                    return redirect(url_for('main.login'))

                session_nonce = session.get('_session_nonce')
                active_nonce = getattr(current_user, 'active_session_nonce', None)
                if active_nonce and session_nonce != active_nonce:
                    from flask_login import logout_user
                    from flask import flash, redirect, url_for
                    logout_user()
                    session.clear()
                    flash('Your account was signed in from another device/session. Please log in again.', 'warning')
                    return redirect(url_for('main.login'))

                now = datetime.now(timezone.utc)
                last = session.get('_last_activity')
                timeout = app.config.get('SESSION_IDLE_TIMEOUT', 1800)
                if last:
                    from datetime import datetime as dt
                    try:
                        last_dt = dt.fromisoformat(last)
                        if (now - last_dt).total_seconds() > timeout:
                            from flask_login import logout_user
                            logout_user()
                            session.clear()
                            from flask import flash
                            flash('Session expired due to inactivity. Please log in again.', 'warning')
                            return
                    except (ValueError, TypeError):
                        pass
                session['_last_activity'] = now.isoformat()
                session.permanent = True
        except Exception as e:
            db.session.rollback()
            app.logger.warning(f'Session timeout check skipped due to transient error: {e}')

    # Error handlers
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('404.html'), 404

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template('500.html'), 500

    # Create database tables and seed admin
    with app.app_context():
        db.create_all()
        _ensure_user_columns(app)
        _seed_admin(app)

    return app


def _seed_admin(app):
    """Create or update default admin account from env vars."""
    from .models import User
    admin = User.query.filter_by(username=Config.ADMIN_USERNAME).first()
    if not admin:
        # Check if email already exists (avoid unique constraint violation)
        existing = User.query.filter_by(email=Config.ADMIN_EMAIL).first()
        if existing:
            existing.is_admin = True
            existing.is_verified = True
            app.logger.info(f'Existing user "{existing.username}" promoted to admin.')
        else:
            admin = User(
                username=Config.ADMIN_USERNAME,
                email=Config.ADMIN_EMAIL,
                password_hash=generate_password_hash(Config.ADMIN_PASSWORD),
                full_name=Config.ADMIN_FULL_NAME,
                is_admin=True,
                is_verified=True
            )
            db.session.add(admin)
            app.logger.info(f'Admin account "{Config.ADMIN_USERNAME}" created.')
    else:
        # Update admin credentials from env vars on each restart
        admin.email = Config.ADMIN_EMAIL
        admin.full_name = Config.ADMIN_FULL_NAME
        admin.password_hash = generate_password_hash(Config.ADMIN_PASSWORD)
        admin.is_admin = True
        admin.is_verified = True
        app.logger.info(f'Admin account "{Config.ADMIN_USERNAME}" credentials updated from env.')
    db.session.commit()


def _ensure_user_columns(app):
    """Best-effort schema patch for newly added User preference columns."""
    try:
        engine = db.engine
        with engine.connect() as conn:
            dialect = engine.dialect.name
            if dialect == 'sqlite':
                rows = conn.execute(text("PRAGMA table_info(user)")).fetchall()
                cols = {r[1] for r in rows}
                if 'enable_future_monthly_reminders' not in cols:
                    conn.execute(text("ALTER TABLE user ADD COLUMN enable_future_monthly_reminders BOOLEAN DEFAULT 1"))
                    app.logger.info('Added column: user.enable_future_monthly_reminders')
                if 'future_target_year' not in cols:
                    conn.execute(text("ALTER TABLE user ADD COLUMN future_target_year INTEGER DEFAULT 2040"))
                    app.logger.info('Added column: user.future_target_year')
                if 'enable_future_quarterly_reminders' not in cols:
                    conn.execute(text("ALTER TABLE user ADD COLUMN enable_future_quarterly_reminders BOOLEAN DEFAULT 1"))
                    app.logger.info('Added column: user.enable_future_quarterly_reminders')
                if 'enable_only_critical_notifications' not in cols:
                    conn.execute(text("ALTER TABLE user ADD COLUMN enable_only_critical_notifications BOOLEAN DEFAULT 0"))
                    app.logger.info('Added column: user.enable_only_critical_notifications')
                if 'pending_email' not in cols:
                    conn.execute(text("ALTER TABLE user ADD COLUMN pending_email VARCHAR(120)"))
                    app.logger.info('Added column: user.pending_email')
                if 'profile_photo' not in cols:
                    conn.execute(text("ALTER TABLE user ADD COLUMN profile_photo VARCHAR(255)"))
                    app.logger.info('Added column: user.profile_photo')
                if 'profile_photo_data' not in cols:
                    conn.execute(text("ALTER TABLE user ADD COLUMN profile_photo_data BLOB"))
                    app.logger.info('Added column: user.profile_photo_data')
                if 'profile_photo_mime' not in cols:
                    conn.execute(text("ALTER TABLE user ADD COLUMN profile_photo_mime VARCHAR(100)"))
                    app.logger.info('Added column: user.profile_photo_mime')
                if 'profile_photo_updated_at' not in cols:
                    conn.execute(text("ALTER TABLE user ADD COLUMN profile_photo_updated_at DATETIME"))
                    app.logger.info('Added column: user.profile_photo_updated_at')
                if 'active_session_nonce' not in cols:
                    conn.execute(text("ALTER TABLE user ADD COLUMN active_session_nonce VARCHAR(64)"))
                    app.logger.info('Added column: user.active_session_nonce')
                if 'active_session_updated_at' not in cols:
                    conn.execute(text("ALTER TABLE user ADD COLUMN active_session_updated_at DATETIME"))
                    app.logger.info('Added column: user.active_session_updated_at')
                if 'otp_attempts' not in cols:
                    conn.execute(text("ALTER TABLE user ADD COLUMN otp_attempts INTEGER DEFAULT 0"))
                    app.logger.info('Added column: user.otp_attempts')
                if 'otp_locked_until' not in cols:
                    conn.execute(text("ALTER TABLE user ADD COLUMN otp_locked_until DATETIME"))
                    app.logger.info('Added column: user.otp_locked_until')
                if 'is_active_user' not in cols:
                    conn.execute(text("ALTER TABLE user ADD COLUMN is_active_user BOOLEAN DEFAULT 1"))
                    app.logger.info('Added column: user.is_active_user')
                if 'enable_price_tracker' not in cols:
                    conn.execute(text("ALTER TABLE user ADD COLUMN enable_price_tracker BOOLEAN DEFAULT 1"))
                    app.logger.info('Added column: user.enable_price_tracker')
                # Add member column to expense and financial_goal tables
                exp_cols = {r[1] for r in conn.execute(text("PRAGMA table_info(expense)")).fetchall()}
                if 'member' not in exp_cols:
                    conn.execute(text("ALTER TABLE expense ADD COLUMN member VARCHAR(100) DEFAULT 'Self'"))
                    app.logger.info('Added column: expense.member')
                goal_cols = {r[1] for r in conn.execute(text("PRAGMA table_info(financial_goal)")).fetchall()}
                if 'member' not in goal_cols:
                    conn.execute(text("ALTER TABLE financial_goal ADD COLUMN member VARCHAR(100) DEFAULT 'Self'"))
                    app.logger.info('Added column: financial_goal.member')
                pt_cols = {r[1] for r in conn.execute(text("PRAGMA table_info(payment_transaction)")).fetchall()}
                if 'expires_at' not in pt_cols:
                    conn.execute(text("ALTER TABLE payment_transaction ADD COLUMN expires_at TIMESTAMP"))
                    app.logger.info('Added column: payment_transaction.expires_at')
                conn.commit()
            else:
                rows = conn.execute(text(
                    "SELECT column_name FROM information_schema.columns WHERE table_name='user'"
                )).fetchall()
                cols = {r[0] for r in rows}
                if 'enable_future_monthly_reminders' not in cols:
                    conn.execute(text("ALTER TABLE \"user\" ADD COLUMN enable_future_monthly_reminders BOOLEAN DEFAULT TRUE"))
                    app.logger.info('Added column: user.enable_future_monthly_reminders')
                if 'future_target_year' not in cols:
                    conn.execute(text("ALTER TABLE \"user\" ADD COLUMN future_target_year INTEGER DEFAULT 2040"))
                    app.logger.info('Added column: user.future_target_year')
                if 'enable_future_quarterly_reminders' not in cols:
                    conn.execute(text("ALTER TABLE \"user\" ADD COLUMN enable_future_quarterly_reminders BOOLEAN DEFAULT TRUE"))
                    app.logger.info('Added column: user.enable_future_quarterly_reminders')
                if 'enable_only_critical_notifications' not in cols:
                    conn.execute(text("ALTER TABLE \"user\" ADD COLUMN enable_only_critical_notifications BOOLEAN DEFAULT FALSE"))
                    app.logger.info('Added column: user.enable_only_critical_notifications')
                if 'pending_email' not in cols:
                    conn.execute(text("ALTER TABLE \"user\" ADD COLUMN pending_email VARCHAR(120)"))
                    app.logger.info('Added column: user.pending_email')
                if 'profile_photo' not in cols:
                    conn.execute(text("ALTER TABLE \"user\" ADD COLUMN profile_photo VARCHAR(255)"))
                    app.logger.info('Added column: user.profile_photo')
                if 'profile_photo_data' not in cols:
                    conn.execute(text("ALTER TABLE \"user\" ADD COLUMN profile_photo_data BYTEA"))
                    app.logger.info('Added column: user.profile_photo_data')
                if 'profile_photo_mime' not in cols:
                    conn.execute(text("ALTER TABLE \"user\" ADD COLUMN profile_photo_mime VARCHAR(100)"))
                    app.logger.info('Added column: user.profile_photo_mime')
                if 'profile_photo_updated_at' not in cols:
                    conn.execute(text("ALTER TABLE \"user\" ADD COLUMN profile_photo_updated_at TIMESTAMP"))
                    app.logger.info('Added column: user.profile_photo_updated_at')
                if 'active_session_nonce' not in cols:
                    conn.execute(text("ALTER TABLE \"user\" ADD COLUMN active_session_nonce VARCHAR(64)"))
                    app.logger.info('Added column: user.active_session_nonce')
                if 'active_session_updated_at' not in cols:
                    conn.execute(text("ALTER TABLE \"user\" ADD COLUMN active_session_updated_at TIMESTAMP"))
                    app.logger.info('Added column: user.active_session_updated_at')
                if 'otp_attempts' not in cols:
                    conn.execute(text("ALTER TABLE \"user\" ADD COLUMN otp_attempts INTEGER DEFAULT 0"))
                    app.logger.info('Added column: user.otp_attempts')
                if 'otp_locked_until' not in cols:
                    conn.execute(text("ALTER TABLE \"user\" ADD COLUMN otp_locked_until TIMESTAMP"))
                    app.logger.info('Added column: user.otp_locked_until')
                if 'is_active_user' not in cols:
                    conn.execute(text("ALTER TABLE \"user\" ADD COLUMN is_active_user BOOLEAN DEFAULT TRUE"))
                    app.logger.info('Added column: user.is_active_user')
                if 'enable_price_tracker' not in cols:
                    conn.execute(text("ALTER TABLE \"user\" ADD COLUMN enable_price_tracker BOOLEAN DEFAULT TRUE"))
                    app.logger.info('Added column: user.enable_price_tracker')
                # Widen otp_code from VARCHAR(10) to VARCHAR(64) for full SHA-256 hash
                try:
                    conn.execute(text("ALTER TABLE \"user\" ALTER COLUMN otp_code TYPE VARCHAR(64)"))
                except Exception:
                    pass
                # Add member column to expense and financial_goal tables
                exp_cols = {r[0] for r in conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name='expense'")).fetchall()}
                if 'member' not in exp_cols:
                    conn.execute(text("ALTER TABLE expense ADD COLUMN member VARCHAR(100) DEFAULT 'Self'"))
                    app.logger.info('Added column: expense.member')
                goal_cols = {r[0] for r in conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name='financial_goal'")).fetchall()}
                if 'member' not in goal_cols:
                    conn.execute(text("ALTER TABLE financial_goal ADD COLUMN member VARCHAR(100) DEFAULT 'Self'"))
                    app.logger.info('Added column: financial_goal.member')
                pt_cols = {r[0] for r in conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name='payment_transaction'")).fetchall()}
                if 'expires_at' not in pt_cols:
                    conn.execute(text("ALTER TABLE payment_transaction ADD COLUMN expires_at TIMESTAMP"))
                    app.logger.info('Added column: payment_transaction.expires_at')
                # Ensure tracked_product and price_history tables exist
                tp_exists = conn.execute(text(
                    "SELECT 1 FROM information_schema.tables WHERE table_name='tracked_product'"
                )).fetchone()
                if not tp_exists:
                    conn.execute(text("""
                        CREATE TABLE tracked_product (
                            id SERIAL PRIMARY KEY,
                            user_id INTEGER NOT NULL REFERENCES "user"(id),
                            url VARCHAR(2048) NOT NULL,
                            platform VARCHAR(50),
                            name VARCHAR(500),
                            image_url VARCHAR(2048),
                            current_price FLOAT,
                            mrp FLOAT,
                            discount_pct FLOAT,
                            min_price FLOAT,
                            max_price FLOAT,
                            target_price FLOAT,
                            is_active BOOLEAN DEFAULT TRUE,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            last_checked TIMESTAMP
                        )
                    """))
                    conn.execute(text("CREATE INDEX ix_tracked_user ON tracked_product(user_id)"))
                    app.logger.info('Created table: tracked_product')
                ph_exists = conn.execute(text(
                    "SELECT 1 FROM information_schema.tables WHERE table_name='price_history'"
                )).fetchone()
                if not ph_exists:
                    conn.execute(text("""
                        CREATE TABLE price_history (
                            id SERIAL PRIMARY KEY,
                            product_id INTEGER NOT NULL REFERENCES tracked_product(id) ON DELETE CASCADE,
                            price FLOAT NOT NULL,
                            recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )
                    """))
                    conn.execute(text("CREATE INDEX ix_pricehist_product ON price_history(product_id)"))
                    app.logger.info('Created table: price_history')
                conn.commit()
    except Exception as e:
        app.logger.warning(f'Could not auto-patch user reminder columns: {e}')
