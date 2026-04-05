"""
MoneyManager Pro - Entry Point
Run this file to start the application.
"""
import os
from app import create_app
from app.config import Config

application = create_app()

if __name__ == '__main__':
    debug = os.environ.get('FLASK_DEBUG', 'true').lower() == 'true'
    application.run(debug=debug, port=Config.APP_PORT)
