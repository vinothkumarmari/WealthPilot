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
from werkzeug.security import generate_password_hash
from .models import db
from .config import Config

login_manager = LoginManager()
login_manager.login_view = 'main.login'
login_manager.login_message_category = 'info'

mail = Mail()
csrf = CSRFProtect()
limiter = Limiter(key_func=get_remote_address, default_limits=["200 per minute"])


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
    mail_config_path = os.path.join(app.instance_path, 'mail_config.json')
    if os.path.exists(mail_config_path):
        with open(mail_config_path, 'r') as f:
            cfg = json.load(f)
        if cfg.get('mail_username'):
            app.config['MAIL_SERVER'] = cfg.get('mail_server', 'smtp.gmail.com')
            app.config['MAIL_PORT'] = int(cfg.get('mail_port', 587))
            app.config['MAIL_USE_TLS'] = cfg.get('mail_use_tls', True)
            app.config['MAIL_USE_SSL'] = False
            app.config['MAIL_USERNAME'] = cfg['mail_username']
            app.config['MAIL_PASSWORD'] = cfg.get('mail_password', '')
            app.config['MAIL_DEFAULT_SENDER'] = cfg.get('mail_default_sender', cfg['mail_username'])

    # Initialize extensions
    db.init_app(app)
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
        _seed_admin(app)

    return app


def _seed_admin(app):
    """Create default admin account if not exists."""
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
        db.session.commit()
