"""One-time migration script for new features.
Run this BEFORE starting the app if you have an existing database.
"""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance', 'Vnit.db')

if not os.path.exists(DB_PATH):
    print(f'Database not found at {DB_PATH}. Run the app first to create it.')
    exit(0)

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Get existing columns for each table
def get_columns(table):
    cursor.execute(f"PRAGMA table_info({table})")
    return {row[1] for row in cursor.fetchall()}

# Add member columns to existing tables
for tbl in ['investment', 'insurance_policy', 'scheme']:
    try:
        cols = get_columns(tbl)
        if 'member' not in cols:
            cursor.execute(f"ALTER TABLE {tbl} ADD COLUMN member VARCHAR(100) DEFAULT 'Self'")
            print(f'Added {tbl}.member')
        else:
            print(f'{tbl}.member: already exists')
    except Exception as e:
        print(f'{tbl}.member: {e}')

# Add session/security columns to user table
user_cols = get_columns('user')
for col, coltype, default in [
    ('failed_login_count', 'INTEGER', '0'),
    ('locked_until', 'DATETIME', 'NULL'),
    ('last_activity', 'DATETIME', 'NULL'),
]:
    try:
        if col not in user_cols:
            cursor.execute(f"ALTER TABLE user ADD COLUMN {col} {coltype} DEFAULT {default}")
            print(f'Added user.{col}')
        else:
            print(f'user.{col}: already exists')
    except Exception as e:
        print(f'user.{col}: {e}')

conn.commit()
conn.close()
print('Migration complete.')
