"""
MoneyManager Pro - Entry Point
Run this file to start the application.
"""
from app import create_app
from app.config import Config

application = create_app()

if __name__ == '__main__':
    application.run(debug=True, port=Config.APP_PORT)
