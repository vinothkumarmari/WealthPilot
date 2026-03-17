"""One-time migration script for new features."""
from app.models import db
from app import create_app
from sqlalchemy import text

app = create_app()
with app.app_context():
    conn = db.engine.connect()
    # Add member columns to existing tables
    for tbl in ['investment', 'insurance_policy', 'scheme']:
        try:
            conn.execute(text(f"ALTER TABLE {tbl} ADD COLUMN member VARCHAR(100) DEFAULT 'Self'"))
            print(f'Added member to {tbl}')
        except Exception as e:
            print(f'{tbl}.member: already exists or {e}')
    conn.commit()
    conn.close()
    # SIP and Budget tables created by db.create_all() in create_app
    print('Migration complete.')
