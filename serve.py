import os

os.environ.setdefault('PRODUCTION', '1')

from waitress import serve
from app import app, db, AdminUser, _migrate_db, _seed_testimonials, _seed_jobs, _seed_blogs, _seed_portfolio, _seed_team, seed_settings


def setup_production_db():
    with app.app_context():
        print("Database sync and seeding in progress...")
        db.create_all()
        _migrate_db()
        _seed_testimonials()
        _seed_jobs()
        _seed_blogs()
        _seed_portfolio()
        _seed_team()
        seed_settings()
        if not AdminUser.query.filter_by(username='admin').first():
            user = AdminUser(username='admin')
            user.set_password('admin@iv2026')
            db.session.add(user)
            db.session.commit()
            print("Default admin created: admin / admin@iv2026")
        print("Database Ready!")

if __name__ == '__main__':
    setup_production_db()
    print("Waitress Server Running on 127.0.0.1:8080")
    serve(app, host='127.0.0.1', port=8080, threads=6)