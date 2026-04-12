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
from flask_limiter.util import get_remote_address
from flask_migrate import Migrate
from werkzeug.security import generate_password_hash
from sqlalchemy import text
from .models import db
from .config import Config

login_manager = LoginManager()
login_manager.login_view = 'main.login'
login_manager.login_message_category = 'info'

mail = Mail()
csrf = CSRFProtect()
limiter = Limiter(key_func=get_remote_address, default_limits=["200 per minute"])
migrate = Migrate()


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

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
        if _cu and _cu.is_authenticated:
            lang = getattr(_cu, 'language', 'en') or 'en'
        return {'t': get_translator(lang), 'current_lang': lang, 'LANGUAGES': LANGUAGES}

    # User loader
    from .models import User

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

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
            "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net; "
            "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com https://fonts.googleapis.com; "
            "img-src 'self' data: blob:; "
            "connect-src 'self';"
        )
        if not app.debug:
            response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        return response

    # Session idle timeout
    @app.before_request
    def check_session_timeout():
        try:
            if current_user.is_authenticated:
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
                conn.commit()
    except Exception as e:
        app.logger.warning(f'Could not auto-patch user reminder columns: {e}')
