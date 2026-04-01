"""
Database schema updater for production deployment.

How to run on server:
1. Pull latest code to the server.
2. Activate virtual environment:
   source venv/bin/activate
3. Run:
   python update_schema.py
4. Restart the Flask app/Gunicorn service.
"""

from app import app, db
from sqlalchemy import inspect, text


def update_database():
    with app.app_context():
        inspector = inspect(db.engine)

        # Check if 'portfolios' table exists
        if 'portfolios' in inspector.get_table_names():
            columns = [col['name'] for col in inspector.get_columns('portfolios')]

            # Check if 'trust_badges' column is missing
            if 'trust_badges' not in columns:
                print("Adding 'trust_badges' column to 'portfolios' table...")
                try:
                    # Execute raw SQL to add the column safely
                    db.session.execute(text('ALTER TABLE portfolios ADD COLUMN trust_badges TEXT'))
                    db.session.commit()
                    print("SUCCESS: Added 'trust_badges' column.")
                except Exception as e:
                    db.session.rollback()
                    print(f"ERROR updating database: {e}")
            else:
                print("SKIP: 'trust_badges' column already exists. No changes made.")
        else:
            print("ERROR: 'portfolios' table not found in the database.")


if __name__ == '__main__':
    update_database()
