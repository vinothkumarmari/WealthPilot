"""
WealthPilot - AI-Powered Financial Management Application
Flask Application Package
"""
import os
import json
from flask import Flask
from flask_login import LoginManager
from flask_mail import Mail
from werkzeug.security import generate_password_hash
from .models import db
from .config import Config

login_manager = LoginManager()
login_manager.login_view = 'main.login'
login_manager.login_message_category = 'info'

mail = Mail()


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

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
