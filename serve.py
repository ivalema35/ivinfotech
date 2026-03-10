from waitress import serve
from app import app, db, _migrate_db, _seed_testimonials, _seed_jobs, _seed_blogs, _seed_portfolio, _seed_team, seed_settings

def setup_production_db():
    with app.app_context():
        print("Production DB Setup & Seeding Running...")
        db.create_all()
        _migrate_db()  
        _seed_testimonials()
        _seed_jobs()
        _seed_blogs()
        _seed_portfolio()
        _seed_team()
        seed_settings()
        print("Database Ready!")

if __name__ == '__main__':
    setup_production_db()
    print("Waitress Server Running at 127.0.0.1:8080")
    # Host 127.0.0.1 rakha hai taaki direct access block rahe, sirf Nginx access kare
    serve(app, host='127.0.0.1', port=8080, threads=6)