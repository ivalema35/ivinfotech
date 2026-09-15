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
        tables = inspector.get_table_names()

        # ── 1. Portfolio: add missing columns ──────────────────────────────────
        if 'portfolios' in tables:
            columns = [col['name'] for col in inspector.get_columns('portfolios')]

            if 'trust_badges' not in columns:
                print("Adding 'trust_badges' column to 'portfolios' table...")
                try:
                    db.session.execute(text(
                        'ALTER TABLE portfolios ADD COLUMN trust_badges TEXT'
                    ))
                    db.session.commit()
                    print("SUCCESS: Added 'trust_badges' column.")
                except Exception as e:
                    db.session.rollback()
                    print(f"ERROR updating database: {e}")
            else:
                print("SKIP: 'trust_badges' column already exists.")
        else:
            print("ERROR: 'portfolios' table not found.")

        # ── 2. Service: create table if missing ─────────────────────────────────
        if 'services' not in tables:
            print("Creating 'services' table...")
            try:
                db.session.execute(text("""
                    CREATE TABLE services (
                        id          INTEGER PRIMARY KEY AUTOINCREMENT,
                        slug        VARCHAR(255) NOT NULL UNIQUE,
                        title       VARCHAR(255) NOT NULL,
                        is_active   BOOLEAN      NOT NULL DEFAULT 1,
                        faqs        TEXT,
                        created_at  DATETIME     DEFAULT CURRENT_TIMESTAMP
                    )
                """))
                db.session.commit()
                print("SUCCESS: Created 'services' table.")
            except Exception as e:
                db.session.rollback()
                print(f"ERROR creating 'services' table: {e}")
        else:
            print("SKIP: 'services' table already exists.")

        # ── 3. Service: add industries column ──────────────────────────────────
        if 'services' in tables:
            columns = [col['name'] for col in inspector.get_columns('services')]

            if 'industries' not in columns:
                print("Adding 'industries' column to 'services' table...")
                try:
                    db.session.execute(text(
                        'ALTER TABLE services ADD COLUMN industries TEXT'
                    ))
                    db.session.commit()
                    print("SUCCESS: Added 'industries' column.")
                except Exception as e:
                    db.session.rollback()
                    print(f"ERROR updating database: {e}")
            else:
                print("SKIP: 'industries' column already exists.")
        else:
            print("ERROR: 'services' table not found.")

        # ── 4. BlogPost: add CTA widget columns ──────────────────────────────────
        if 'blog_posts' in tables:
            columns = [col['name'] for col in inspector.get_columns('blog_posts')]

            for col_name, col_type in [
                ('cta_title', 'VARCHAR(120)'),
                ('cta_description', 'VARCHAR(300)'),
                ('cta_link', 'VARCHAR(255)'),
            ]:
                if col_name not in columns:
                    print(f"Adding '{col_name}' column to 'blog_posts' table...")
                    try:
                        db.session.execute(text(
                            f'ALTER TABLE blog_posts ADD COLUMN {col_name} {col_type}'
                        ))
                        db.session.commit()
                        print(f"SUCCESS: Added '{col_name}' column.")
                    except Exception as e:
                        db.session.rollback()
                        print(f"ERROR updating database: {e}")
                else:
                    print(f"SKIP: '{col_name}' column already exists.")
        else:
            print("ERROR: 'blog_posts' table not found.")


if __name__ == '__main__':
    update_database()
