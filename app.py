"""
IV Infotech -- Flask Application
=================================
Run:  python app.py
URL:  http://localhost:5000
"""

import os
import re
import json
import secrets
from datetime import datetime

from flask import Flask, render_template, redirect, url_for, request, jsonify, flash, abort, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

# ── App factory ────────────────────────────────────────────────────────────────
basedir = os.path.abspath(os.path.dirname(__file__))

app = Flask(
    __name__,
    template_folder='templates',
    static_folder='assets',
    static_url_path='/assets',
)

app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', secrets.token_hex(32))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'admin.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# ── Upload folder (resumes — stored OUTSIDE static for security) ───────────────
UPLOAD_FOLDER = os.path.join(basedir, 'uploads', 'resumes')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
ALLOWED_RESUME_EXT = {'pdf', 'doc', 'docx'}

# ── Blog image upload (inside static so Flask can serve them directly) ──────────
BLOG_IMG_FOLDER = os.path.join(basedir, 'assets', 'uploads', 'blog')
os.makedirs(BLOG_IMG_FOLDER, exist_ok=True)
ALLOWED_IMG_EXT = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

# ── Portfolio image upload (inside static) ───────────────────────────────────
PORTFOLIO_IMG_FOLDER = os.path.join(basedir, 'assets', 'uploads', 'portfolio')
os.makedirs(PORTFOLIO_IMG_FOLDER, exist_ok=True)

# ── Team photo upload (inside static so Flask can serve directly) ─────────────
TEAM_IMG_FOLDER = os.path.join(basedir, 'assets', 'uploads', 'team')
os.makedirs(TEAM_IMG_FOLDER, exist_ok=True)

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'admin_login'
login_manager.login_message_category = 'warning'


# ── Jinja2 custom filters ──────────────────────────────────────────────────────
@app.template_filter('hex_rgb')
def hex_rgb_filter(hex_color):
    """Convert #RRGGBB (or #RGB) to 'R,G,B' string for use in CSS rgba() calls.
    Example: '#2F55F4' | hex_rgb  →  '47,85,244'
    """
    h = (hex_color or '#000000').lstrip('#')
    if len(h) == 3:
        h = h[0]*2 + h[1]*2 + h[2]*2
    try:
        r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
        return f'{r},{g},{b}'
    except Exception:
        return '0,0,0'


# ── Models ─────────────────────────────────────────────────────────────────────
class AdminUser(UserMixin, db.Model):
    __tablename__ = 'admin_users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Testimonial(db.Model):
    __tablename__ = 'testimonials'
    id          = db.Column(db.Integer, primary_key=True)
    client_name = db.Column(db.String(120), nullable=False)
    client_role = db.Column(db.String(120), nullable=False)
    content     = db.Column(db.Text, nullable=False)
    rating      = db.Column(db.Integer, default=5, nullable=False)
    is_active   = db.Column(db.Boolean, default=True, nullable=False)
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)


class JobOpening(db.Model):
    __tablename__ = 'job_openings'
    id          = db.Column(db.Integer, primary_key=True)
    title       = db.Column(db.String(160), nullable=False)
    description = db.Column(db.Text, nullable=False)
    location    = db.Column(db.String(120), nullable=False, default='Mehsana')
    job_type    = db.Column(db.String(60), nullable=False, default='Full-Time')
    icon_class  = db.Column(db.String(60), nullable=False, default='fas fa-code')
    tags        = db.Column(db.String(255), nullable=True)   # comma-separated
    is_active   = db.Column(db.Boolean, default=True, nullable=False)
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)
    applications = db.relationship('JobApplication', backref='job', lazy=True)


class BlogPost(db.Model):
    __tablename__ = 'blog_posts'
    id             = db.Column(db.Integer, primary_key=True)
    title          = db.Column(db.String(255), nullable=False)
    slug           = db.Column(db.String(255), unique=True, nullable=False, index=True)
    category       = db.Column(db.String(100), nullable=False, default='General')
    excerpt        = db.Column(db.Text, nullable=True)
    content        = db.Column(db.Text, nullable=False)
    featured_image = db.Column(db.String(512), nullable=True)
    author_name    = db.Column(db.String(120), nullable=False, default='IV Infotech')
    author_role    = db.Column(db.String(120), nullable=True)
    read_time      = db.Column(db.String(40), nullable=True)
    is_published   = db.Column(db.Boolean, default=False, nullable=False)
    created_at     = db.Column(db.DateTime, default=datetime.utcnow)


class JobApplication(db.Model):
    __tablename__ = 'job_applications'
    id                   = db.Column(db.Integer, primary_key=True)
    job_id               = db.Column(db.Integer, db.ForeignKey('job_openings.id'), nullable=True)
    first_name           = db.Column(db.String(80), nullable=False)
    last_name            = db.Column(db.String(80), nullable=False)
    email                = db.Column(db.String(120), nullable=False)
    phone                = db.Column(db.String(30), nullable=False)
    experience_formatted = db.Column(db.Text, nullable=True)
    resume_filename      = db.Column(db.String(255), nullable=True)
    created_at           = db.Column(db.DateTime, default=datetime.utcnow)


class Portfolio(db.Model):
    __tablename__ = 'portfolios'
    id              = db.Column(db.Integer, primary_key=True)
    title           = db.Column(db.String(255), nullable=False)
    slug            = db.Column(db.String(255), unique=True, nullable=False, index=True)
    category        = db.Column(db.String(60), nullable=False, default='Web')   # Web / CRM / App / AI
    client_name     = db.Column(db.String(120), nullable=True)
    theme_color     = db.Column(db.String(20), nullable=False, default='#2F55F4')  # kept for backward compat
    primary_color   = db.Column(db.String(20), nullable=False, server_default='#2F55F4')
    secondary_color = db.Column(db.String(20), nullable=False, server_default='#10B981')
    bg_color        = db.Column(db.String(20), nullable=False, server_default='#0f1117')
    is_published    = db.Column(db.Boolean, default=False, nullable=False)
    # Hero & Snapshot
    hero_outcome    = db.Column(db.String(255), nullable=True)   # "+40% discovery & -32% checkout drop-off"
    hero_description= db.Column(db.Text, nullable=True)
    hero_image_web  = db.Column(db.String(512), nullable=True)   # desktop mockup image URL
    hero_image_app  = db.Column(db.String(512), nullable=True)   # phone mockup image URL
    kpi_1_value     = db.Column(db.String(40), nullable=True)
    kpi_1_label     = db.Column(db.String(80), nullable=True)
    kpi_2_value     = db.Column(db.String(40), nullable=True)
    kpi_2_label     = db.Column(db.String(80), nullable=True)
    kpi_3_value     = db.Column(db.String(40), nullable=True)
    kpi_3_label     = db.Column(db.String(80), nullable=True)
    industry        = db.Column(db.String(120), nullable=True)
    market          = db.Column(db.String(120), nullable=True)
    goal            = db.Column(db.String(255), nullable=True)
    client_story_p1 = db.Column(db.Text, nullable=True)
    client_story_p2 = db.Column(db.Text, nullable=True)
    # JSON lists
    challenges      = db.Column(db.Text, nullable=True)  # JSON: [{tag,severity,title,desc,impact}]
    solution_steps  = db.Column(db.Text, nullable=True)  # JSON: [{tag,title,points:[]}]
    services        = db.Column(db.Text, nullable=True)  # JSON: [{num,icon_svg,title,desc,deliverables:[]}]
    results         = db.Column(db.Text, nullable=True)  # JSON: {cards:[{metric,label,insight}], rows:[{metric,before,after}]}
    features        = db.Column(db.Text, nullable=True)  # JSON: [{icon,title,desc,benefit}]
    testimonials    = db.Column(db.Text, nullable=True)  # JSON: [{quote,client_name,client_role,rating}]
    gallery         = db.Column(db.Text, nullable=True)  # JSON: [{type:"web"|"app",url,label,alt}]
    created_at      = db.Column(db.DateTime, default=datetime.utcnow)

    # ── helpers ──
    def get_challenges(self):
        try: return json.loads(self.challenges or '[]')
        except: return []

    def get_solution_steps(self):
        try: return json.loads(self.solution_steps or '[]')
        except: return []

    def get_services(self):
        try: return json.loads(self.services or '[]')
        except: return []

    def get_results(self):
        try: return json.loads(self.results or '{}')
        except: return {}

    def get_features(self):
        try: return json.loads(self.features or '[]')
        except: return []

    def get_testimonials(self):
        """Return testimonials formatted for BZ_TESTIMONIALS (portfolio-details.min.js)."""
        try:
            items = json.loads(self.testimonials or '[]')
            result = []
            for t in items:
                name   = t.get('client_name', '')
                parts  = [p for p in name.split() if p]
                initials = ''.join(p[0] for p in parts[:2]).upper() or '??'
                result.append({
                    'quote':    t.get('quote', ''),
                    'name':     name,
                    'role':     t.get('client_role', ''),
                    'rating':   int(t.get('rating', 5)),
                    'initials': initials,
                })
            return result
        except:
            return []

    def get_gallery(self):
        try: return json.loads(self.gallery or '[]')
        except: return []


class TeamMember(db.Model):
    """A team member or founder shown on the /our-team page."""
    __tablename__ = 'team_members'
    id             = db.Column(db.Integer, primary_key=True)
    name           = db.Column(db.String(120), nullable=False)
    role           = db.Column(db.String(120), nullable=False)
    category       = db.Column(db.String(30),  nullable=False, default='Core Team')  # 'Founder' | 'Core Team'
    bio            = db.Column(db.Text,         nullable=True)
    image_filename = db.Column(db.String(512),  nullable=False, default='images/team/member.jpg')
    linkedin_url   = db.Column(db.String(512),  nullable=True)
    twitter_url    = db.Column(db.String(512),  nullable=True)
    display_order  = db.Column(db.Integer,      nullable=False, default=0)
    is_active      = db.Column(db.Boolean,      nullable=False, default=True)


class Inquiry(db.Model):
    __tablename__ = 'inquiries'
    id               = db.Column(db.Integer, primary_key=True)
    name             = db.Column(db.String(120), nullable=False)
    email            = db.Column(db.String(120), nullable=False)
    phone            = db.Column(db.String(30),  nullable=True)
    service_interest = db.Column(db.String(120), nullable=True)
    message          = db.Column(db.Text,        nullable=True)
    source_page      = db.Column(db.String(255), nullable=True)
    status           = db.Column(db.String(30),  nullable=False, default='New')  # New / In Progress / Closed
    created_at       = db.Column(db.DateTime, default=datetime.utcnow)


class SiteSettings(db.Model):
    """Key-value store for editable site-wide settings."""
    __tablename__ = 'site_settings'
    id    = db.Column(db.Integer, primary_key=True)
    key   = db.Column(db.String(100), unique=True, nullable=False, index=True)
    value = db.Column(db.Text, nullable=True, default='')


# ── Site Settings helpers ──────────────────────────────────────────────────────
_SETTINGS_DEFAULTS = {
    # Company
    'company_name':       'IV Infotech',
    'company_tagline':    'Architecting the Digital Future of Gujarat & Beyond.',
    # Contact
    'phone_primary':      '+91 9924426361',
    'phone_secondary':    '',
    'email_primary':      'info@ivinfotech.com',
    'email_secondary':    '',
    # Address
    'address_line1':      'T-332, S Cube, Radhanpur Rd',
    'address_line2':      'opp. Bansari Township',
    'address_city':       'Mehsana',
    'address_state':      'Gujarat',
    'address_pincode':    '384002',
    'working_hours':      'Mon – Sat, 9:00 AM – 6:00 PM',
    # Social
    'social_linkedin':    'https://www.linkedin.com/company/ivinfotechmeh/',
    'social_instagram':   'https://www.instagram.com/ivinfotech.official/',
    'social_twitter':     'https://x.com/ivinfotech2025',
    'social_facebook':    '',
    'social_youtube':     '',
    # Map
    'map_embed_url':      'https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d3623.7539410410863!2d72.36963712346962!3d23.588046317180107!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x395c20c9e4a4a4a5%3A0x5d5d5d5d5d5d5d5d!2sMehsana%2C%20Gujarat!5e0!3m2!1sen!2sin!4v1707987654321',
    'maps_directions_url':'https://maps.app.goo.gl/QE9zsxqci2KHLYPq9',
}


def get_site_settings():
    """Return all settings as a dict, falling back to defaults for missing keys."""
    rows = SiteSettings.query.all()
    result = dict(_SETTINGS_DEFAULTS)
    for row in rows:
        result[row.key] = row.value or ''
    return result


def seed_settings():
    """Insert default settings rows that don't exist yet."""
    for key, value in _SETTINGS_DEFAULTS.items():
        if not SiteSettings.query.filter_by(key=key).first():
            db.session.add(SiteSettings(key=key, value=value))
    db.session.commit()


@app.context_processor
def inject_site_settings():
    """Inject `site` dict into every template automatically."""
    try:
        return {'site': get_site_settings()}
    except Exception:
        return {'site': dict(_SETTINGS_DEFAULTS)}


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(AdminUser, int(user_id))


# ── Admin Auth Routes ──────────────────────────────────────────────────────────
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if current_user.is_authenticated:
        return redirect(url_for('admin_dashboard'))
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        user = AdminUser.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user, remember=True)
            flash('Welcome back, ' + user.username + '!', 'success')
            return redirect(request.args.get('next') or url_for('admin_dashboard'))
        flash('Invalid username or password.', 'danger')
    return render_template('admin/login.html')


@app.route('/admin/logout')
@login_required
def admin_logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('admin_login'))


@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    total_apps       = JobApplication.query.count()
    total_inquiries  = Inquiry.query.count()
    total_portfolio  = Portfolio.query.count()
    total_blog       = BlogPost.query.count()
    recent_apps      = JobApplication.query.order_by(JobApplication.created_at.desc()).limit(5).all()
    recent_inquiries = Inquiry.query.order_by(Inquiry.created_at.desc()).limit(5).all()
    return render_template(
        'admin/dashboard.html',
        total_apps=total_apps,
        total_inquiries=total_inquiries,
        total_portfolio=total_portfolio,
        total_blog=total_blog,
        recent_apps=recent_apps,
        recent_inquiries=recent_inquiries,
    )


# ── Admin: Testimonials CRUD ───────────────────────────────────────────────────
@app.route('/admin/testimonials')
@login_required
def admin_testimonials():
    all_testimonials = Testimonial.query.order_by(Testimonial.created_at.desc()).all()
    return render_template('admin/testimonials.html', testimonials=all_testimonials)


@app.route('/admin/testimonials/add', methods=['POST'])
@login_required
def admin_testimonials_add():
    t = Testimonial(
        client_name=request.form['client_name'].strip(),
        client_role=request.form['client_role'].strip(),
        content=request.form['content'].strip(),
        rating=int(request.form.get('rating', 5)),
        is_active='is_active' in request.form,
    )
    db.session.add(t)
    db.session.commit()
    flash('Testimonial added successfully.', 'success')
    return redirect(url_for('admin_testimonials'))


@app.route('/admin/testimonials/edit/<int:tid>', methods=['POST'])
@login_required
def admin_testimonials_edit(tid):
    t = db.session.get(Testimonial, tid)
    if t is None:
        abort(404)
    t.client_name = request.form['client_name'].strip()
    t.client_role = request.form['client_role'].strip()
    t.content     = request.form['content'].strip()
    t.rating      = int(request.form.get('rating', 5))
    t.is_active   = 'is_active' in request.form
    db.session.commit()
    flash('Testimonial updated.', 'success')
    return redirect(url_for('admin_testimonials'))


@app.route('/admin/testimonials/delete/<int:tid>', methods=['POST'])
@login_required
def admin_testimonials_delete(tid):
    t = db.session.get(Testimonial, tid)
    if t is None:
        abort(404)
    db.session.delete(t)
    db.session.commit()
    flash('Testimonial deleted.', 'info')
    return redirect(url_for('admin_testimonials'))


# ── Admin: Job Openings CRUD ───────────────────────────────────────────────────
@app.route('/admin/jobs')
@login_required
def admin_jobs():
    jobs = JobOpening.query.order_by(JobOpening.created_at.desc()).all()
    return render_template('admin/jobs.html', jobs=jobs)


@app.route('/admin/jobs/add', methods=['POST'])
@login_required
def admin_jobs_add():
    j = JobOpening(
        title=request.form['title'].strip(),
        description=request.form['description'].strip(),
        location=request.form['location'].strip(),
        job_type=request.form['job_type'].strip(),
        icon_class=request.form.get('icon_class', 'fas fa-code').strip(),
        tags=request.form.get('tags', '').strip(),
        is_active='is_active' in request.form,
    )
    db.session.add(j)
    db.session.commit()
    flash('Job opening added successfully.', 'success')
    return redirect(url_for('admin_jobs'))


@app.route('/admin/jobs/edit/<int:jid>', methods=['POST'])
@login_required
def admin_jobs_edit(jid):
    j = db.session.get(JobOpening, jid)
    if j is None:
        abort(404)
    j.title       = request.form['title'].strip()
    j.description = request.form['description'].strip()
    j.location    = request.form['location'].strip()
    j.job_type    = request.form['job_type'].strip()
    j.icon_class  = request.form.get('icon_class', 'fas fa-code').strip()
    j.tags        = request.form.get('tags', '').strip()
    j.is_active   = 'is_active' in request.form
    db.session.commit()
    flash('Job opening updated.', 'success')
    return redirect(url_for('admin_jobs'))


@app.route('/admin/jobs/delete/<int:jid>', methods=['POST'])
@login_required
def admin_jobs_delete(jid):
    j = db.session.get(JobOpening, jid)
    if j is None:
        abort(404)
    db.session.delete(j)
    db.session.commit()
    flash('Job opening deleted.', 'info')
    return redirect(url_for('admin_jobs'))


# ── Admin: Blog Posts CRUD ───────────────────────────────────────────────────────
@app.route('/admin/blog')
@login_required
def admin_blog():
    posts = BlogPost.query.order_by(BlogPost.created_at.desc()).all()
    return render_template('admin/blog.html', posts=posts)


def _save_blog_image(file_obj):
    """Save uploaded blog image and return the URL path, or None."""
    if not file_obj or not file_obj.filename:
        return None
    ext = file_obj.filename.rsplit('.', 1)[-1].lower()
    if ext not in ALLOWED_IMG_EXT:
        return None
    safe = secure_filename(file_obj.filename)
    unique = datetime.utcnow().strftime('%Y%m%d_%H%M%S_') + safe
    file_obj.save(os.path.join(BLOG_IMG_FOLDER, unique))
    return '/assets/uploads/blog/' + unique


def _save_team_img(file_obj):
    """Save an uploaded team member photo.  Returns the static-relative path or None.
    Stored path is relative to the Flask static folder, e.g. 'uploads/team/20260309_photo.jpg'.
    """
    if not file_obj or not file_obj.filename:
        return None
    ext = file_obj.filename.rsplit('.', 1)[-1].lower()
    if ext not in ALLOWED_IMG_EXT:
        return None
    safe   = secure_filename(file_obj.filename)
    unique = datetime.utcnow().strftime('%Y%m%d_%H%M%S_') + safe
    file_obj.save(os.path.join(TEAM_IMG_FOLDER, unique))
    return 'uploads/team/' + unique


@app.route('/admin/blog/add', methods=['GET', 'POST'])
@login_required
def admin_blog_add():
    if request.method == 'POST':
        featured_image = _save_blog_image(request.files.get('featured_image'))
        post = BlogPost(
            title=request.form['title'].strip(),
            slug=request.form['slug'].strip(),
            category=request.form.get('category', '').strip(),
            excerpt=request.form.get('excerpt', '').strip(),
            content=request.form.get('content', '').strip(),
            featured_image=featured_image,
            author_name=request.form.get('author_name', 'IV Infotech').strip(),
            author_role=request.form.get('author_role', '').strip(),
            read_time=request.form.get('read_time', '').strip(),
            is_published='is_published' in request.form,
        )
        db.session.add(post)
        db.session.commit()
        flash('Blog post created successfully.', 'success')
        return redirect(url_for('admin_blog'))
    return render_template('admin/blog.html', posts=[], _mode='add')


@app.route('/admin/blog/edit/<int:pid>', methods=['GET', 'POST'])
@login_required
def admin_blog_edit(pid):
    post = db.session.get(BlogPost, pid)
    if post is None:
        abort(404)
    if request.method == 'POST':
        post.title       = request.form['title'].strip()
        post.slug        = request.form['slug'].strip()
        post.category    = request.form.get('category', '').strip()
        post.excerpt     = request.form.get('excerpt', '').strip()
        post.content     = request.form.get('content', '').strip()
        post.author_name = request.form.get('author_name', 'IV Infotech').strip()
        post.author_role = request.form.get('author_role', '').strip()
        post.read_time   = request.form.get('read_time', '').strip()
        post.is_published = 'is_published' in request.form
        new_img = _save_blog_image(request.files.get('featured_image'))
        if new_img:
            post.featured_image = new_img
        db.session.commit()
        flash('Blog post updated.', 'success')
        return redirect(url_for('admin_blog'))
    return render_template('admin/blog.html', posts=[], _edit_post=post)


@app.route('/admin/blog/delete/<int:pid>', methods=['POST'])
@login_required
def admin_blog_delete(pid):
    post = db.session.get(BlogPost, pid)
    if post is None:
        abort(404)
    db.session.delete(post)
    db.session.commit()
    flash('Blog post deleted.', 'info')
    return redirect(url_for('admin_blog'))


# ── DB migration helper (add missing columns to existing SQLite tables) ─────────
def _migrate_db():
    """Idempotent: add new Portfolio columns to the existing DB without data loss."""
    from sqlalchemy import text
    migrations = [
        ("portfolios", "primary_color",   "VARCHAR(20) NOT NULL DEFAULT '#2F55F4'"),
        ("portfolios", "secondary_color", "VARCHAR(20) NOT NULL DEFAULT '#10B981'"),
        ("portfolios", "bg_color",        "VARCHAR(20) NOT NULL DEFAULT '#0f1117'"),
    ]
    try:
        with db.engine.connect() as conn:
            for table, col, typedef in migrations:
                rows = conn.execute(text(f"PRAGMA table_info({table})")).fetchall()
                existing = {r[1] for r in rows}
                if col not in existing:
                    conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {col} {typedef}"))
                    conn.commit()
    except Exception:
        pass  # table may not exist yet on first run — db.create_all() will create it


# ── Admin: Portfolio CRUD ──────────────────────────────────────────────────────
def _save_portfolio_img(file_obj, slug=None):
    """Save an uploaded portfolio image.  If slug is given, files go into
    assets/uploads/portfolio/<slug>/ (per-project isolation)."""
    if not file_obj or not file_obj.filename:
        return None
    ext = file_obj.filename.rsplit('.', 1)[-1].lower()
    if ext not in ALLOWED_IMG_EXT:
        return None
    safe = secure_filename(file_obj.filename)
    unique = datetime.utcnow().strftime('%Y%m%d_%H%M%S_') + safe
    if slug:
        folder = os.path.join(PORTFOLIO_IMG_FOLDER, secure_filename(slug))
        os.makedirs(folder, exist_ok=True)
        file_obj.save(os.path.join(folder, unique))
        return '/assets/uploads/portfolio/' + secure_filename(slug) + '/' + unique
    file_obj.save(os.path.join(PORTFOLIO_IMG_FOLDER, unique))
    return '/assets/uploads/portfolio/' + unique


def _portfolio_from_form(p, form, files):
    """Populate a Portfolio object from admin form data (multipart) or JSON dict."""
    p.title           = form.get('title', '').strip()
    raw_slug          = form.get('slug', '').strip()
    p.slug            = re.sub(r'[^a-z0-9-]', '', raw_slug.lower().replace(' ', '-')) or p.slug
    p.category        = form.get('category', 'Web').strip()
    p.client_name     = form.get('client_name', '').strip()
    p.primary_color   = form.get('primary_color', form.get('theme_color', '#2F55F4')).strip()
    p.secondary_color = form.get('secondary_color', '#10B981').strip()
    p.bg_color        = form.get('bg_color', '#0f1117').strip()
    p.theme_color     = p.primary_color   # keep in sync for backward compat
    p.is_published    = form.get('is_published') in (True, 'true', '1', 'on', 'yes') \
                        if isinstance(form.get('is_published'), (str, bool)) else ('is_published' in form)
    p.hero_outcome    = form.get('hero_outcome', '').strip()
    p.hero_description= form.get('hero_description', '').strip()
    p.kpi_1_value     = form.get('kpi_1_value', '').strip()
    p.kpi_1_label     = form.get('kpi_1_label', '').strip()
    p.kpi_2_value     = form.get('kpi_2_value', '').strip()
    p.kpi_2_label     = form.get('kpi_2_label', '').strip()
    p.kpi_3_value     = form.get('kpi_3_value', '').strip()
    p.kpi_3_label     = form.get('kpi_3_label', '').strip()
    p.industry        = form.get('industry', '').strip()
    p.market          = form.get('market', '').strip()
    p.goal            = form.get('goal', '').strip()
    p.client_story_p1 = form.get('client_story_p1', '').strip()
    p.client_story_p2 = form.get('client_story_p2', '').strip()
    # JSON text fields passed as raw JSON strings
    for field in ('challenges', 'solution_steps', 'services', 'results', 'features', 'testimonials', 'gallery'):
        raw = form.get(field, '')
        if isinstance(raw, (list, dict)):
            setattr(p, field, json.dumps(raw))
        elif isinstance(raw, str):
            raw = raw.strip()
            try:
                json.loads(raw)   # validate only
                setattr(p, field, raw)
            except ValueError:
                pass   # leave existing value untouched on bad JSON
    # Hero images (only for multipart/form-data, not JSON)
    if files:
        new_web = _save_portfolio_img(files.get('hero_image_web'), slug=p.slug or None)
        if new_web:
            p.hero_image_web = new_web
        new_app = _save_portfolio_img(files.get('hero_image_app'), slug=p.slug or None)
        if new_app:
            p.hero_image_app = new_app
    # hero_image URLs can also come from JSON payload
    if form.get('hero_image_web'):
        p.hero_image_web = form.get('hero_image_web')
    if form.get('hero_image_app'):
        p.hero_image_app = form.get('hero_image_app')


@app.route('/admin/portfolio')
@login_required
def admin_portfolio():
    portfolios = Portfolio.query.order_by(Portfolio.created_at.desc()).all()
    return render_template('admin/portfolio.html', portfolios=portfolios)


@app.route('/admin/portfolio/add', methods=['GET', 'POST'])
@login_required
def admin_portfolio_add():
    if request.method == 'POST':
        p = Portfolio()
        _portfolio_from_form(p, request.form, request.files)
        db.session.add(p)
        db.session.commit()
        flash('Portfolio entry created.', 'success')
        return redirect(url_for('admin_portfolio'))
    return render_template('admin/portfolio_form.html', portfolio=None)


@app.route('/admin/portfolio/edit/<int:pid>', methods=['GET', 'POST'])
@login_required
def admin_portfolio_edit(pid):
    p = db.session.get(Portfolio, pid)
    if p is None:
        abort(404)
    if request.method == 'POST':
        _portfolio_from_form(p, request.form, request.files)
        db.session.commit()
        flash('Portfolio entry updated.', 'success')
        return redirect(url_for('admin_portfolio'))
    return render_template('admin/portfolio_form.html', portfolio=p)


@app.route('/admin/portfolio/delete/<int:pid>', methods=['POST'])
@login_required
def admin_portfolio_delete(pid):
    p = db.session.get(Portfolio, pid)
    if p is None:
        abort(404)
    db.session.delete(p)
    db.session.commit()
    flash('Portfolio entry deleted.', 'info')
    return redirect(url_for('admin_portfolio'))


# ── Admin: Portfolio gallery image upload (AJAX, legacy flat folder) ──────────
@app.route('/admin/portfolio/upload-image', methods=['POST'])
@login_required
def admin_portfolio_upload_image():
    url = _save_portfolio_img(request.files.get('file'))
    if url:
        return jsonify({'success': True, 'url': url})
    return jsonify({'success': False, 'error': 'Invalid file'}), 400


# ── Admin: Per-project image upload (Visual Builder) ─────────────────────────
@app.route('/admin/api/upload_portfolio_image/<slug>', methods=['POST'])
@login_required
def api_upload_portfolio_image(slug):
    """Upload an image to assets/uploads/portfolio/<slug>/.  Returns the absolute URL."""
    clean_slug = re.sub(r'[^a-z0-9-]', '', slug.lower())
    if not clean_slug:
        return jsonify({'success': False, 'error': 'Invalid slug'}), 400
    file_obj = request.files.get('file')
    url = _save_portfolio_img(file_obj, slug=clean_slug)
    if url:
        return jsonify({'success': True, 'url': url})
    return jsonify({'success': False, 'error': 'Invalid or missing file (allowed: png, jpg, jpeg, gif, webp)'}), 400


# ── Admin: Portfolio Draft Preview (no is_published filter) ──────────────────
@app.route('/admin/portfolio/preview/<slug>')
@login_required
def admin_portfolio_preview(slug):
    """Renders portfolio-details.html for any portfolio regardless of published status.
    Used exclusively as the iframe src in the Visual Builder so draft edits are visible."""
    portfolio = Portfolio.query.filter_by(slug=slug).first_or_404()
    return render_template('portfolio-details.html', active_page='portfolio', portfolio=portfolio)


# ── Admin: Visual Builder (split-screen live editor) ──────────────────────────
@app.route('/admin/portfolio/build')
@app.route('/admin/portfolio/build/<int:pid>')
@login_required
def admin_portfolio_build(pid=None):
    portfolio = None
    if pid:
        portfolio = db.session.get(Portfolio, pid)
        if not portfolio:
            abort(404)
    return render_template('admin/portfolio_builder.html', portfolio=portfolio)


# ── Admin: Visual Builder JSON save/publish ────────────────────────────────────
@app.route('/admin/portfolio/save', methods=['POST'])
@login_required
def admin_portfolio_save():
    """Accepts a JSON body with all portfolio fields.  Creates or updates a Portfolio."""
    data = request.get_json(force=True, silent=True)
    if not data:
        return jsonify({'success': False, 'error': 'No JSON payload'}), 400

    pid    = data.get('id')
    action = data.get('action', 'draft')   # 'draft' | 'publish'

    if pid:
        p = db.session.get(Portfolio, pid)
        if not p:
            return jsonify({'success': False, 'error': 'Portfolio not found'}), 404
    else:
        # Auto-create slug from title if missing
        title = data.get('title', '').strip()
        if not title:
            return jsonify({'success': False, 'error': 'Title is required'}), 400
        raw_slug = data.get('slug', title).strip()
        slug = re.sub(r'[^a-z0-9-]+', '-', raw_slug.lower()).strip('-')
        # Ensure uniqueness
        base, i = slug, 1
        while Portfolio.query.filter_by(slug=slug).first():
            slug = f'{base}-{i}'; i += 1
        data['slug'] = slug
        p = Portfolio()
        db.session.add(p)

    # Override is_published based on action
    data['is_published'] = (action == 'publish')
    _portfolio_from_form(p, data, None)
    db.session.commit()
    return jsonify({'success': True, 'id': p.id, 'slug': p.slug,
                    'status': 'Published' if p.is_published else 'Draft'})


# ── Admin: Job Applications (read-only view) ────────────────────────────────────
@app.route('/admin/applications')
@login_required
def admin_applications():
    apps = JobApplication.query.order_by(JobApplication.created_at.desc()).all()
    return render_template('admin/applications.html', applications=apps)


@app.route('/admin/applications/resume/<path:filename>')
@login_required
def admin_download_resume(filename):
    """Serve resume files — protected behind login."""
    safe = secure_filename(filename)
    return send_from_directory(app.config['UPLOAD_FOLDER'], safe)


# ── Public API: Receive job application (dual-submit alongside n8n) ────────────
@app.route('/api/apply_job', methods=['POST'])
def api_apply_job():
    first_name = request.form.get('first_name', '').strip()
    last_name  = request.form.get('last_name', '').strip()
    email      = request.form.get('email', '').strip()
    phone      = request.form.get('phone', '').strip()
    if not (first_name and last_name and email and phone):
        return jsonify({'success': False, 'error': 'Missing required fields.'}), 400

    exp_fmt    = request.form.get('experience_formatted') or request.form.get('experience_type', 'Fresher')
    job_id_raw = request.form.get('job_id', '').strip()

    # Resolve FK — silently ignore invalid ids
    job_id = None
    if job_id_raw:
        try:
            cand = int(job_id_raw)
            if db.session.get(JobOpening, cand):
                job_id = cand
        except (ValueError, TypeError):
            pass

    # Save resume file
    resume_filename = None
    resume_file = request.files.get('resume_file')
    if resume_file and resume_file.filename:
        ext = resume_file.filename.rsplit('.', 1)[-1].lower()
        if ext in ALLOWED_RESUME_EXT:
            safe_name = secure_filename(resume_file.filename)
            unique_name = datetime.utcnow().strftime('%Y%m%d_%H%M%S_') + safe_name
            resume_file.save(os.path.join(app.config['UPLOAD_FOLDER'], unique_name))
            resume_filename = unique_name

    application = JobApplication(
        job_id=job_id,
        first_name=first_name,
        last_name=last_name,
        email=email,
        phone=phone,
        experience_formatted=exp_fmt,
        resume_filename=resume_filename,
    )
    db.session.add(application)
    db.session.commit()
    return jsonify({'success': True, 'message': 'Application saved.'})


# ── CLI: Create default admin ──────────────────────────────────────────────────
@app.cli.command('create-admin')
def create_admin():
    """Create default admin user (admin / admin@iv2026)."""
    with app.app_context():
        db.create_all()
        if AdminUser.query.filter_by(username='admin').first():
            print('Admin user already exists.')
            return
        user = AdminUser(username='admin')
        user.set_password('admin@iv2026')
        db.session.add(user)
        db.session.commit()
        print('Admin user created: admin / admin@iv2026')

# ── Context processor: inject `now` into every template (used by footer year) ──
@app.context_processor
def inject_globals():
    return {'now': datetime.utcnow()}

# ── Page Routes ────────────────────────────────────────────────────────────────
@app.route('/')
def index_page():
    home_testimonials = Testimonial.query.filter_by(is_active=True).order_by(Testimonial.created_at.desc()).all()
    return render_template('index.html', active_page='home', testimonials=home_testimonials)

@app.route('/about')
def about():
    return render_template('about.html', active_page='about')

@app.route('/our-team')
def our_team():
    founders  = TeamMember.query.filter_by(category='Founder',   is_active=True).order_by(TeamMember.display_order.asc()).all()
    core_team = TeamMember.query.filter_by(category='Core Team', is_active=True).order_by(TeamMember.display_order.asc()).all()
    return render_template('our-team.html', active_page='about', founders=founders, core_team=core_team)

@app.route('/testimonials')
def testimonials():
    testimonials = Testimonial.query.filter_by(is_active=True).order_by(Testimonial.created_at.desc()).all()
    return render_template('testimonials.html', active_page='about', testimonials=testimonials)

@app.route('/career')
def career():
    jobs = JobOpening.query.filter_by(is_active=True).order_by(JobOpening.created_at.desc()).all()
    return render_template('career.html', active_page='about', jobs=jobs)

@app.route('/services')
def services():
    return render_template('services.html', active_page='services')

@app.route('/custom-mobile-application-development')
def custom_mobile_app():
    return render_template('custom-mobile-application-development.html', active_page='services')

@app.route('/custom-website-software-development')
def custom_website_dev():
    return render_template('custom-website-software-development.html', active_page='services')

@app.route('/crm-erp-custom-software-development')
def crm_erp_dev():
    return render_template('crm-erp-custom-software-development.html', active_page='services')

@app.route('/ecommerce-website-app-development-india')
def ecommerce_dev():
    return render_template('ecommerce-website-app-development-india.html', active_page='services')

@app.route('/digital-marketing')
def digital_marketing():
    return render_template('digital-marketing.html', active_page='services')

@app.route('/ui-ux-design-agency-india')
def ui_ux_design():
    return render_template('ui-ux-design-agency-india.html', active_page='services')

@app.route('/best-web-hosting-services')
def web_hosting():
    return render_template('best-web-hosting-services.html', active_page='services')

@app.route('/ai-automation')
def ai_automation():
    return render_template('ai-automation.html', active_page='services')

@app.route('/hire-php-developers')
def hire_php():
    return render_template('hire-php-developers.html', active_page='hire')

@app.route('/hire-laravel-developers')
def hire_laravel():
    return render_template('hire-laravel-developers.html', active_page='hire')

@app.route('/hire-android-developers')
def hire_android():
    return render_template('hire-android-developers.html', active_page='hire')

@app.route('/hire-flutter-developers')
def hire_flutter():
    return render_template('hire-flutter-developers.html', active_page='hire')

@app.route('/hire-html-developers')
def hire_html():
    return render_template('hire-html-developers.html', active_page='hire')

@app.route('/hire-ui-ux-designers')
def hire_ui_ux():
    return render_template('hire-ui-ux-designers.html', active_page='hire')

@app.route('/hire-ai-engineers')
def hire_ai():
    return render_template('hire-ai-engineers.html', active_page='hire')

@app.route('/portfolio')
def portfolio():
    portfolios = Portfolio.query.filter_by(is_published=True).order_by(Portfolio.created_at.desc()).all()
    return render_template('portfolio.html', active_page='portfolio', portfolios=portfolios)

@app.route('/portfolio/<slug>')
def portfolio_detail(slug):
    portfolio = Portfolio.query.filter_by(slug=slug, is_published=True).first_or_404()
    return render_template('portfolio-details.html', active_page='portfolio', portfolio=portfolio)

@app.route('/portfolio-details')
def portfolio_details():
    # Legacy redirect — if Belzzo slug exists, redirect to it; otherwise show first published
    p = Portfolio.query.filter_by(slug='belzzo-kids-footwear', is_published=True).first()
    if p is None:
        p = Portfolio.query.filter_by(is_published=True).order_by(Portfolio.created_at.desc()).first()
    if p:
        return redirect(url_for('portfolio_detail', slug=p.slug))
    return render_template('portfolio-details.html', active_page='portfolio', portfolio=None)

@app.route('/blog')
def blog():
    posts = BlogPost.query.filter_by(is_published=True).order_by(BlogPost.created_at.desc()).all()
    return render_template('blog.html', active_page='blog', posts=posts)

@app.route('/blog/<slug>')
def blog_post(slug):
    post = BlogPost.query.filter_by(slug=slug, is_published=True).first_or_404()
    related_posts = (BlogPost.query
                     .filter(BlogPost.slug != slug, BlogPost.is_published == True)
                     .order_by(db.func.random())
                     .limit(3).all())
    return render_template('blog-slug-template.html', active_page='blog', post=post, related_posts=related_posts)

@app.route('/contact')
def contact():
    return render_template('contact.html', active_page='contact')

@app.route('/index')
def index_redirect():
    return redirect(url_for('index_page'))

# ── Contact Form (POST) ────────────────────────────────────────────────────────
@app.route('/contact/submit', methods=['POST'])
def contact_submit():
    """Handle contact form submissions.  Replace with real email / CRM logic."""
    data = {
        'name':    request.form.get('name', ''),
        'email':   request.form.get('email', ''),
        'phone':   request.form.get('phone', ''),
        'service': request.form.get('service', ''),
        'message': request.form.get('message', ''),
    }
    # TODO: send email, write to DB, push to n8n webhook, etc.
    return jsonify({'success': True, 'message': 'Thank you! We will contact you soon.'})


# ── Public API: Submit Inquiry (universal contact / hire forms) ─────────────────
@app.route('/api/submit-inquiry', methods=['POST'])
def api_submit_inquiry():
    data = request.get_json(silent=True) or {}
    name  = (data.get('name') or '').strip()
    email = (data.get('email') or '').strip()
    if not name or not email:
        return jsonify({'success': False, 'error': 'Name and email are required.'}), 400
    inquiry = Inquiry(
        name             = name,
        email            = email,
        phone            = (data.get('phone') or '').strip() or None,
        service_interest = (data.get('service_interest') or '').strip() or None,
        message          = (data.get('message') or '').strip() or None,
        source_page      = (data.get('source_page') or '').strip() or None,
        status           = 'New',
    )
    db.session.add(inquiry)
    db.session.commit()
    return jsonify({'success': True, 'message': 'Inquiry submitted successfully!'})


# ── Admin: Inquiries dashboard ──────────────────────────────────────────────────
@app.route('/admin/inquiries')
@login_required
def admin_inquiries():
    inquiries = Inquiry.query.order_by(Inquiry.created_at.desc()).all()
    return render_template('admin/inquiries.html', inquiries=inquiries)


@app.route('/admin/inquiries/status/<int:iid>', methods=['POST'])
@login_required
def admin_inquiry_status(iid):
    inquiry = db.session.get(Inquiry, iid)
    if inquiry is None:
        return jsonify({'success': False, 'error': 'Not found'}), 404
    body = request.get_json(silent=True) or {}
    new_status = body.get('status', '').strip()
    if new_status not in ('New', 'In Progress', 'Closed'):
        return jsonify({'success': False, 'error': 'Invalid status'}), 400
    inquiry.status = new_status
    db.session.commit()
    return jsonify({'success': True})


# ── Admin: Team Members CRUD ──────────────────────────────────────────
@app.route('/admin/team')
@login_required
def admin_team():
    members = TeamMember.query.order_by(
        TeamMember.category.desc(), TeamMember.display_order.asc()
    ).all()
    return render_template('admin/team.html', members=members)


@app.route('/admin/team/add', methods=['POST'])
@login_required
def admin_team_add():
    new_img = _save_team_img(request.files.get('photo'))
    m = TeamMember(
        name          = request.form['name'].strip(),
        role          = request.form['role'].strip(),
        category      = request.form.get('category', 'Core Team'),
        bio           = request.form.get('bio', '').strip(),
        image_filename= new_img or request.form.get('image_filename', 'images/team/member.jpg').strip(),
        linkedin_url  = request.form.get('linkedin_url', '').strip(),
        twitter_url   = request.form.get('twitter_url', '').strip(),
        display_order = int(request.form.get('display_order', 99) or 99),
        is_active     = 'is_active' in request.form,
    )
    db.session.add(m)
    db.session.commit()
    flash('Team member added successfully.', 'success')
    return redirect(url_for('admin_team'))


@app.route('/admin/team/edit/<int:mid>', methods=['POST'])
@login_required
def admin_team_edit(mid):
    m = db.session.get(TeamMember, mid)
    if m is None:
        abort(404)
    m.name          = request.form['name'].strip()
    m.role          = request.form['role'].strip()
    m.category      = request.form.get('category', 'Core Team')
    m.bio           = request.form.get('bio', '').strip()
    m.linkedin_url  = request.form.get('linkedin_url', '').strip()
    m.twitter_url   = request.form.get('twitter_url', '').strip()
    m.display_order = int(request.form.get('display_order', m.display_order) or m.display_order)
    m.is_active     = 'is_active' in request.form
    new_img = _save_team_img(request.files.get('photo'))
    if new_img:
        m.image_filename = new_img
    db.session.commit()
    flash('Team member updated.', 'success')
    return redirect(url_for('admin_team'))


@app.route('/admin/team/delete/<int:mid>', methods=['POST'])
@login_required
def admin_team_delete(mid):
    m = db.session.get(TeamMember, mid)
    if m is None:
        abort(404)
    db.session.delete(m)
    db.session.commit()
    flash('Team member deleted.', 'info')
    return redirect(url_for('admin_team'))


# ── Admin: Site Settings ───────────────────────────────────────────────────────
@app.route('/admin/settings', methods=['GET', 'POST'])
@login_required
def admin_settings():
    if request.method == 'POST':
        for key in _SETTINGS_DEFAULTS:
            value = request.form.get(key, '').strip()
            row = SiteSettings.query.filter_by(key=key).first()
            if row:
                row.value = value
            else:
                db.session.add(SiteSettings(key=key, value=value))
        db.session.commit()
        flash('Settings saved successfully.', 'success')
        return redirect(url_for('admin_settings'))
    settings = get_site_settings()
    return render_template('admin/settings.html', settings=settings)


# ── Thank You page ───────────────────────────────────────────────────────────
@app.route('/thank-you')
def thank_you():
    return render_template('thank-you.html')

# ── 404 handler ────────────────────────────────────────────────────────────────
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

# ── Seed: existing testimonials ────────────────────────────────────────────────
def _seed_testimonials():
    """Populate testimonials table with existing reviews (runs only when empty)."""
    if Testimonial.query.count() > 0:
        return
    seed = [
        Testimonial(client_name='JMA Salam', client_role='Client', rating=5,
            content='A big Thanks to the Team @ IV Infotech. This was our 2nd web-based project delivered by you guys and I am pleased with the efficiency in delivering the project as per our requirements. Appreciate the support & communication provided throughout the project making it seamless.'),
        Testimonial(client_name='Moksha Stocks', client_role='Company', rating=5,
            content='These people have provided me very good development service as well as advised me new features. I strongly recommend these people if anyone looking for web development and CRM development. Because my old CRM was having so many issues no one could identify. IV Infotech helped me a lot.'),
        Testimonial(client_name='Akash Patel', client_role='Client', rating=5,
            content='IV Infotech is highly qualified and professional staff was recommended to provide technical expertise in solving a long-standing problem. They were very responsive and quickly solved the problem. Since provided us with prompt quality service.'),
        Testimonial(client_name='Sagar Krupa', client_role='Intern', rating=5,
            content='As an intern, I got here Fullstack Developer level training. After training, I applied to some companies and got a job with a good package. Thank you IV Infotech for providing me best practical knowledge. Highly recommend for job-oriented training.'),
        Testimonial(client_name='Patel Raj', client_role='Client', rating=5,
            content='In the last week, I am pleased to inform that it was a wonderful experience. I have gained confidence in dealing with PHP queries in real time. Really thankful and I recommend others to be part of IV Infotech family.'),
        Testimonial(client_name='Kartik Kava', client_role='Team Member', rating=5,
            content='Best work environment and co-operative team. They provide fast solutions for Client Projects. Highly recommend!'),
        Testimonial(client_name='Vinod Vyas', client_role='Developer', rating=5,
            content='Ronak is a quality developer you can trust. He communicated well, understood the requirements and delivered the application.'),
        Testimonial(client_name='Nikunj Patel', client_role='Trainee', rating=5,
            content='Hi, I am doing my PHP Development training at IV Infotech. They provided it in a good environment to learn and concern to individual queries.'),
        Testimonial(client_name='Harsh Patel', client_role='Client', rating=5,
            content='I am fully satisfied with the mobile app development and website development services provided by IV Infotech. Very professional team!'),
    ]
    db.session.bulk_save_objects(seed)
    db.session.commit()
    print(f'Seeded {len(seed)} testimonials.')


# ── Seed: job openings ────────────────────────────────────────────────────────
def _seed_jobs():
    """Populate job_openings table with default positions (runs only when empty)."""
    if JobOpening.query.count() > 0:
        return
    seed = [
        JobOpening(title='Laravel Developer',
            description='Build scalable APIs, admin panels, and SaaS products using Laravel, MySQL, and Redis.',
            location='Mehsana', job_type='Full-Time', icon_class='fab fa-laravel',
            tags='Laravel, PHP, MySQL, REST APIs'),
        JobOpening(title='AI Automation Engineer',
            description='Design and deploy AI models & Agents, LLM integrations, RAG pipelines, and intelligent automation systems.',
            location='Mehsana / Remote', job_type='Full-Time', icon_class='fas fa-robot',
            tags='Python, N8N, LangChain, OpenAI'),
        JobOpening(title='UI/UX Designer',
            description='Craft user-centered interfaces for web & mobile products. Wireframes, prototypes, and design systems.',
            location='Mehsana', job_type='Full-Time', icon_class='fas fa-paint-brush',
            tags='Figma, Prototyping, Design Systems'),
        JobOpening(title='Flutter Developer',
            description='Build cross-platform mobile apps with Flutter & Dart. Work on e-commerce, SaaS, and enterprise apps.',
            location='Mehsana', job_type='Full-Time', icon_class='fas fa-mobile-alt',
            tags='Flutter, Dart, Firebase, REST APIs'),
        JobOpening(title='Digital Marketing Executive',
            description='Drive SEO, social media, Google Ads, and content marketing campaigns for diverse client portfolios.',
            location='Mehsana', job_type='Full-Time', icon_class='fas fa-chart-line',
            tags='SEO, Google Ads, Social Media, Analytics'),
        JobOpening(title='Full-Stack Web Developer',
            description='Work across the stack — React/Vue on the front-end, Node.js or Laravel on the back-end, and cloud deployments.',
            location='Mehsana', job_type='Full-Time', icon_class='fas fa-code',
            tags='React, Node.js, MongoDB, AWS'),
    ]
    db.session.bulk_save_objects(seed)
    db.session.commit()
    print(f'Seeded {len(seed)} job openings.')


# ── Seed: blog posts ─────────────────────────────────────────────────────────
def _seed_blogs():
    """Populate blog_posts table with the original 7 static articles (skips any slug that already exists)."""
    seed_slugs = [
        'how-ai-powered-automation-is-transforming-small-businesses-in-2026',
        'nextjs-vs-nuxtjs-which-framework-should-you-choose-in-2026',
        'building-custom-gpt-powered-chatbots-for-enterprise-customer-support',
        '10-seo-strategies-that-actually-work-in-2026',
        'flutter-vs-react-native-in-2026-the-definitive-cross-platform-showdown',
        'building-design-systems-that-scale-a-startups-practical-guide',
        'headless-cms-vs-traditional-cms-what-enterprise-teams-need-to-know',
    ]
    existing = {p.slug for p in BlogPost.query.filter(BlogPost.slug.in_(seed_slugs)).all()}
    to_insert = []
    all_posts = [
        BlogPost(
            title='How AI-Powered Automation Is Transforming Small Businesses in 2026',
            slug='how-ai-powered-automation-is-transforming-small-businesses-in-2026',
            category='AI & Automation',
            excerpt='Discover how small and mid-sized businesses are leveraging AI automation to cut operational costs by 40%, streamline complex workflows, and deliver hyper-personalised customer experiences.',
            featured_image='https://images.unsplash.com/photo-1677442136019-21780ecad995?w=800&q=80',
            author_name='Aarav Mehta',
            author_role='AI & Automation Lead',
            read_time='8 min read',
            is_published=True,
            created_at=datetime(2026, 2, 15),
            content='<p>Artificial Intelligence is no longer the exclusive playground of Fortune 500 companies. In 2026, small and mid-sized businesses (SMBs) are harnessing AI-powered automation to compete at a level that was once unimaginable — cutting costs, reducing errors, and unlocking growth at scale.</p><h2>Why AI Automation Matters for SMBs</h2><p>Traditional business processes — invoicing, customer follow-ups, inventory management, HR onboarding — consume thousands of employee-hours annually. AI automation turns these repetitive workflows into self-running machines, freeing your team to focus on high-value creative and strategic work.</p><h2>Key Areas Where AI Is Making an Impact</h2><p>From customer service chatbots that resolve 80% of tickets without human intervention, to predictive inventory systems that cut stockouts by half, the ROI of AI automation is becoming impossible to ignore. Tools like n8n, Make (Integromat), and custom LangChain agents are democratising access to enterprise-grade automation.</p><h2>Real-World Results: 40% Cost Reduction</h2><p>A mid-sized e-commerce brand in Gujarat implemented an AI-powered order-processing and customer support pipeline. Within six months, operational costs dropped 38%, customer satisfaction scores jumped 22 points, and the team of 4 handled a workload previously requiring 11 staff members.</p><h2>Getting Started with AI Automation</h2><p>Start by identifying your three most time-consuming repetitive tasks. Map the workflow, then evaluate low-code automation platforms. For complex decision-making, integrate an LLM using the OpenAI API or a self-hosted model. The barrier to entry has never been lower.</p><h2>Conclusion</h2><p>AI automation is the great equaliser. SMBs that embrace it now will build compounding competitive advantages — faster delivery, leaner operations, and superior customer experiences. The question is no longer <em>if</em> you should automate, but <em>what to automate first</em>.</p>'
        ),
        BlogPost(
            title='Next.js vs Nuxt.js: Which Framework Should You Choose in 2026?',
            slug='nextjs-vs-nuxtjs-which-framework-should-you-choose-in-2026',
            category='Web Development',
            excerpt='A detailed comparison covering performance, SEO capabilities, developer experience, and ecosystem maturity to help you pick the right meta-framework for your next project.',
            featured_image='https://images.unsplash.com/photo-1555066931-4365d14bab8c?w=600&q=80',
            author_name='Priya Sharma',
            author_role='Full-Stack Web Developer',
            read_time='6 min read',
            is_published=True,
            created_at=datetime(2026, 2, 10),
            content='<p>The meta-framework wars of 2026 are well and truly alive. Next.js (React) and Nuxt.js (Vue) both offer SSR, SSG, ISR, and edge rendering — but the right choice depends on your team, your project, and your long-term goals.</p><h2>Performance Benchmarks</h2><p>In our internal benchmarks on a Vercel + Netlify infrastructure, Next.js 15 edged out Nuxt 4 on Time to First Byte (TTFB) for dynamic SSR pages by roughly 12ms. For statically generated pages, both frameworks perform nearly identically with sub-100ms load times globally.</p><h2>SEO Capabilities</h2><p>Both frameworks now support the Metadata API pattern for granular head tag control. Next.js has a slight edge with its built-in <code>generateMetadata</code> async function, while Nuxt relies on the excellent <code>useHead</code> composable via Nuxt SEO suite. Neither framework leaves SEO on the table in 2026.</p><h2>Developer Experience</h2><p>Vue developers will feel immediately at home with Nuxt\'s file-based routing, auto-imports, and composable-first architecture. React developers benefit from Next.js\'s massive ecosystem, the App Router\'s Server Components model, and an enormous community knowledge base on Stack Overflow and GitHub.</p><h2>Ecosystem Maturity</h2><p>Next.js wins on raw ecosystem size — npm packages, UI libraries, and deployment platform integrations. Nuxt\'s ecosystem is smaller but remarkably cohesive, with official modules for auth, image optimisation, content management, and internationalisation maintained by the core team.</p><h2>The Verdict</h2><p>Choose <strong>Next.js</strong> if your team is React-native, you need maximum ecosystem choice, or you\'re building a large-scale application with complex data requirements. Choose <strong>Nuxt.js</strong> if your team prefers Vue\'s composition API, you value developer ergonomics, or you\'re building a content-heavy site where Nuxt Content shines.</p>'
        ),
        BlogPost(
            title='Building Custom GPT-Powered Chatbots for Enterprise Customer Support',
            slug='building-custom-gpt-powered-chatbots-for-enterprise-customer-support',
            category='AI & Automation',
            excerpt='Learn how to build and deploy context-aware AI chatbots using OpenAI APIs, LangChain, and RAG architecture that actually understand your business and resolve customer queries.',
            featured_image='https://images.unsplash.com/photo-1620712943543-bcc4688e7485?w=600&q=80',
            author_name='Aarav Mehta',
            author_role='AI & Automation Lead',
            read_time='7 min read',
            is_published=True,
            created_at=datetime(2026, 2, 5),
            content='<p>Generic chatbots frustrate customers. They answer with scripted non-responses that leave users reaching for the phone anyway. The new generation of GPT-powered enterprise chatbots — built on RAG architecture — are fundamentally different. They understand your business context and provide genuinely useful answers.</p><h2>The Architecture: RAG Explained</h2><p>Retrieval-Augmented Generation (RAG) combines the power of a vector database with a large language model. Your company\'s documentation, FAQs, product catalogues, and support history are chunked, embedded, and stored in a vector DB (Pinecone, Weaviate, or pgvector). When a user asks a question, the system retrieves the most semantically relevant chunks and injects them into the LLM prompt as context.</p><h2>The Tech Stack</h2><p>A production-ready enterprise chatbot in 2026 typically uses: <strong>OpenAI GPT-4o</strong> (or a self-hosted Llama 3 for data-sensitive environments), <strong>LangChain</strong> for orchestration, <strong>Pinecone</strong> for vector storage, <strong>FastAPI</strong> for the backend API, and a React or Vue frontend with streaming responses via Server-Sent Events.</p><h2>Building the Knowledge Base</h2><p>Index your support tickets, product documentation, return policies, and FAQs. Use OpenAI\'s text-embedding-3-small model for cost-effective embeddings. Implement a re-ranking step using a cross-encoder to improve retrieval precision before sending context to the LLM.</p><h2>Handling Escalations Gracefully</h2><p>Define clear confidence thresholds. When the retrieved context relevance score falls below 0.75, route the conversation to a human agent via your CRM using a webhook. Log all low-confidence interactions for continuous knowledge base improvement.</p><h2>Results You Can Expect</h2><p>Enterprises deploying RAG-based chatbots are reporting 65–80% ticket deflection rates, average handling time reductions of 45%, and CSAT scores that match or exceed human agents for Tier 1 queries. The ROI is compelling.</p>'
        ),
        BlogPost(
            title='10 SEO Strategies That Actually Work in 2026 (Backed by Data)',
            slug='10-seo-strategies-that-actually-work-in-2026',
            category='Digital Marketing',
            excerpt='From AI-generated content optimisation to Core Web Vitals mastery — the only SEO playbook you need this year, backed by real campaign data from 50+ client websites.',
            featured_image='https://images.unsplash.com/photo-1533750349088-cd871a92f312?w=600&q=80',
            author_name='Neha Patel',
            author_role='Digital Marketing Manager',
            read_time='5 min read',
            is_published=True,
            created_at=datetime(2026, 1, 28),
            content='<p>SEO in 2026 is unrecognisable from 2020. Google\'s AI Overviews, zero-click searches, and the rise of LLM-driven discovery have rewritten the rules. Here are the 10 strategies our team has validated across 50+ client websites in the past 12 months.</p><h2>1. Optimise for AI Overviews (AIO)</h2><p>Structure your content to directly answer questions in the first 100 words. Use clear H2/H3 hierarchies, concise bullet points, and factual claims with citations. Content that earns AIO placement sees 3–5x more impressions even without top-10 rankings.</p><h2>2. Prioritise Core Web Vitals Relentlessly</h2><p>LCP under 2.5s, CLS under 0.1, INP under 200ms — these are table stakes. Use Next.js Image Optimisation, lazy loading, and CDN edge caching. Core Web Vitals now directly influence ranking in competitive SERPs.</p><h2>3. Build Topical Authority with Semantic Clusters</h2><p>One-off articles no longer move the needle. Build pillar pages with 10–20 supporting cluster articles covering every sub-topic. Internal linking with descriptive anchor text signals topical depth to Google\'s Helpful Content system.</p><h2>4. Leverage Entity SEO</h2><p>Add structured data (JSON-LD) for every applicable schema type — Article, FAQPage, HowTo, BreadcrumbList, Organization, and Person. Entity disambiguation through Knowledge Panel management builds long-term brand authority.</p><h2>5. Video SEO via YouTube</h2><p>Google prominently features YouTube videos in search results. A 3-minute explainer video with an optimised title, description, chapters, and transcript can rank in the top 3 for high-competition queries when a text article cannot.</p><h2>The Bottom Line</h2><p>SEO success in 2026 requires matching search intent with precision, building genuine topical authority, and delivering an exceptional page experience. The fundamentals have not changed; the execution requirements have simply raised the bar significantly.</p>'
        ),
        BlogPost(
            title='Flutter vs React Native in 2026: The Definitive Cross-Platform Showdown',
            slug='flutter-vs-react-native-in-2026-the-definitive-cross-platform-showdown',
            category='Mobile Apps',
            excerpt='We benchmark performance, UI fidelity, hot reload speed, and plugin ecosystems across real-world projects to settle the Flutter vs React Native debate once and for all.',
            featured_image='https://images.unsplash.com/photo-1512941937669-90a1b58e7e9c?w=600&q=80',
            author_name='Rohit Jain',
            author_role='Mobile App Developer',
            read_time='8 min read',
            is_published=True,
            created_at=datetime(2026, 1, 22),
            content='<p>The cross-platform mobile development landscape has stabilised significantly since the turbulent early 2020s. Flutter and React Native have both matured enormously — but they serve genuinely different use cases. Here\'s our honest 2026 verdict based on shipping 20+ production apps.</p><h2>Performance: Flutter Wins on Raw Speed</h2><p>Flutter\'s Impeller rendering engine eliminates shader compilation jank entirely. In our benchmarks — 1000-item scrollable lists, complex animations, and camera-intensive apps — Flutter consistently delivers 60fps with lower CPU usage than React Native\'s New Architecture (Fabric + JSI).</p><h2>UI Fidelity and Custom Design</h2><p>Flutter gives you pixel-perfect control. Since it renders every pixel with its own engine, your app looks identical on Android and iOS. React Native uses native components, which means platform-specific visual differences require additional work to reconcile but also means your UI feels genuinely "native".</p><h2>Ecosystem and Third-Party Libraries</h2><p>React Native\'s npm ecosystem is vastly larger, with mature libraries for payments (Stripe), maps (Google Maps), analytics, and virtually every API integration. Flutter\'s pub.dev ecosystem has grown rapidly but still has gaps, particularly for niche hardware integrations and banking SDKs.</p><h2>Developer Experience</h2><p>Flutter\'s hot reload is world-class — 300ms state-preserving reloads. Dart is easy to learn for JavaScript developers and enforces null safety by default. React Native developers benefit from JS/TS familiarity and the ability to hire from the massive React web talent pool.</p><h2>The Verdict</h2><p>Choose <strong>Flutter</strong> for design-heavy apps, games, custom UI, or when performance is paramount. Choose <strong>React Native</strong> when your team is JS-first, you need maximum native library access, or you\'re sharing code with a React web codebase. Both are excellent choices in 2026.</p>'
        ),
        BlogPost(
            title="Building Design Systems That Scale: A Startup's Practical Guide",
            slug='building-design-systems-that-scale-a-startups-practical-guide',
            category='UI/UX Design',
            excerpt='How to create a design system from scratch that keeps your product consistent, speeds up dev handoff, and evolves gracefully with your brand as you scale from 5 to 500 screens.',
            featured_image='https://images.unsplash.com/photo-1561070791-2526d30994b5?w=600&q=80',
            author_name='Meera Kulkarni',
            author_role='UI/UX Design Lead',
            read_time='5 min read',
            is_published=True,
            created_at=datetime(2026, 1, 18),
            content='<p>Most startups discover their design system problem the hard way: inconsistent button styles across 30 screens, a rebrand that requires updating 200 components manually, and a dev team building the same modal for the fourth time. The solution is a design system — and the best time to build one is before it becomes urgent.</p><h2>Start with Design Tokens, Not Components</h2><p>Design tokens are the atoms of your system: colour palette, typography scale, spacing units, border radii, shadow levels, and motion durations. Define these in a <code>tokens.json</code> file before touching a single component. Tools like Style Dictionary or Tokens Studio for Figma transform tokens into platform-specific variables automatically.</p><h2>Build the Foundation Layer First</h2><p>Foundation components — Button, Input, Badge, Card, Modal, Toast — are used everywhere and must be pristine. Invest time building them with full prop coverage, accessibility (WCAG 2.2 AA), keyboard navigation, and comprehensive Storybook documentation. A well-built foundation prevents 80% of future inconsistencies.</p><h2>Documentation Is the Product</h2><p>A design system without documentation is a design system nobody uses. For every component: document its purpose, props/variants, usage guidelines (do/don\'t), accessibility notes, and Figma → code correspondence. Use Storybook with MDX docs or Zeroheight for a polished documentation site.</p><h2>Governance: How to Evolve Without Breaking Things</h2><p>Define a clear RFC (Request for Change) process. Any team member can propose a new component or token change, but a designated "design system owner" reviews for consistency before merging. Use semantic versioning and automated visual regression testing (Chromatic) to catch breaking changes before they reach production.</p><h2>Conclusion</h2><p>A design system is a multiplier — it makes every future screen faster to design and build. The investment pays dividends from the moment you have more than one person working on your product. Start small, be consistent, and let it evolve organically with your needs.</p>'
        ),
        BlogPost(
            title='Headless CMS vs Traditional CMS: What Enterprise Teams Need to Know',
            slug='headless-cms-vs-traditional-cms-what-enterprise-teams-need-to-know',
            category='Web Development',
            excerpt='An honest comparison of Strapi, Sanity, and WordPress covering content modelling, API performance, editorial experience, and total cost of ownership for enterprise teams in 2026.',
            featured_image='https://images.unsplash.com/photo-1558494949-ef010cbdcc31?w=600&q=80',
            author_name='Priya Sharma',
            author_role='Full-Stack Web Developer',
            read_time='6 min read',
            is_published=True,
            created_at=datetime(2026, 1, 15),
            content='<p>The CMS landscape in 2026 offers more choice than ever — and more confusion. Enterprise teams face a critical architecture decision: stick with the comfortable monolith of WordPress, or leap into the headless world of Strapi or Sanity. The stakes are high: your CMS underpins every piece of content your business publishes.</p><h2>What Is a Headless CMS?</h2><p>A headless CMS decouples the content repository (the "body") from the presentation layer (the "head"). Content is managed via a rich admin UI and delivered to any front-end — web, mobile, digital signage, voice assistants — through a REST or GraphQL API. This separation enables omnichannel content delivery and developer freedom.</p><h2>WordPress in 2026: Still Relevant?</h2><p>WordPress powers 43% of the web for a reason: it\'s mature, has an enormous plugin ecosystem, and editorial teams know how to use it. WordPress used headlessly (via WP REST API or WPGraphQL with a Next.js frontend) remains a legitimate enterprise choice, especially when migration cost is a constraint.</p><h2>Strapi: The Open-Source Headless Champion</h2><p>Strapi v5 is production-ready, self-hostable, and offers full content-type customisation, role-based access control, and excellent REST + GraphQL APIs. For teams needing data sovereignty and custom business logic, Strapi is the default recommendation.</p><h2>Sanity: The Structured Content Platform</h2><p>Sanity\'s real-time collaborative editing, GROQ query language, and portable text format are genuinely innovative. For media-rich publishing workflows, global editorial teams, and content that needs to be reused across many surfaces, Sanity\'s content lake architecture is a compelling proposition.</p><h2>Total Cost of Ownership</h2><p>Traditional CMS TCO is deceptively high when you include plugin licensing, security patching, and performance optimisation. Headless CMS TCO is front-loaded (initial build investment) but lower ongoing. For content-heavy enterprises with a 3+ year horizon, headless wins on TCO by a significant margin.</p>'
        ),
    ]
    for p in all_posts:
        if p.slug not in existing:
            to_insert.append(p)
    if not to_insert:
        return
    db.session.bulk_save_objects(to_insert)
    db.session.commit()
    print(f'Seeded {len(to_insert)} blog posts.')


@app.cli.command('seed-blogs')
def seed_blogs_cmd():
    """Seed blog_posts table with the 7 original static articles."""
    with app.app_context():
        _seed_blogs()
        print('Done.')


# ── Seed: portfolio ───────────────────────────────────────────────────────────
def _seed_portfolio():
    """Seed the portfolios table with 3 original case studies (skips existing slugs)."""
    seed_slugs = [
        'belzzo-kids-footwear',
        'manufacturing-erp-system',
        'hyperlocal-food-delivery-app',
    ]
    existing = {p.slug for p in Portfolio.query.filter(Portfolio.slug.in_(seed_slugs)).all()}

    belzzo_challenges = json.dumps([
        {"tag": "UX", "severity": "Critical", "title": "Checkout complexity",
         "desc": "Multi-step checkout and missing trust cues created friction at the final conversion point.",
         "impact": "Direct revenue loss — buyers reached the cart but abandoned before completing purchase."},
        {"tag": "UX", "severity": "High", "title": "Product discovery friction",
         "desc": "No filters, poor categorisation — customers couldn't navigate a growing catalog efficiently.",
         "impact": "Shoppers left without finding what they needed — high bounce rate across catalog pages."},
        {"tag": "UX", "severity": "High", "title": "Mobile experience gaps",
         "desc": "Site was not optimised for mobile, despite the majority of Belzzo's audience browsing on phones.",
         "impact": "Over half of potential customers experienced a broken journey — most dropped off immediately."},
        {"tag": "Technical", "severity": "High", "title": "Performance & SEO",
         "desc": "Slow load times and no technical SEO foundation left the site invisible to search engines.",
         "impact": "Zero organic acquisition — no compounding traffic channel and a poor user experience under load."},
        {"tag": "Trust", "severity": "Medium", "title": "Missing trust signals",
         "desc": "No reviews, testimonials, or security badges to reassure parents buying for their children.",
         "impact": "Parents hesitated to purchase from an unfamiliar brand — high exit rate on product pages."},
        {"tag": "Technical", "severity": "Critical", "title": "No analytics visibility",
         "desc": "No tracking in place — impossible to identify where users dropped off or what was working.",
         "impact": "Every decision was a guess — conversion issues went undetected and compounded over time."},
    ])
    belzzo_solution_steps = json.dumps([
        {"tag": "Design", "title": "UI/UX & Brand Design",
         "points": ["Kids-friendly visuals with a consistent design system", "Seasonal hero banners for campaign-ready layouts"]},
        {"tag": "Catalog", "title": "Product Listing & Filters",
         "points": ["Smart filters by size, category, brand and price", "High-res images with quick add-to-cart"]},
        {"tag": "Checkout & Performance", "title": "Checkout, Speed & SEO",
         "points": ["Minimal-step checkout with UPI, cards & wallets", "Image optimization, clean URLs, meta tags & GA4"]},
    ])
    belzzo_services = json.dumps([
        {"num": "01", "title": "UI/UX Design", "desc": "End-to-end design from wireframes to pixel-perfect prototypes.", "deliverables": ["Wireframes", "Design System"]},
        {"num": "02", "title": "Frontend Development", "desc": "React-based responsive UI with smooth interactions.", "deliverables": ["React Components", "Animations"]},
        {"num": "03", "title": "Backend & Catalog", "desc": "Node.js API, inventory management, and payment gateway integration.", "deliverables": ["REST API", "Payment Integration"]},
        {"num": "04", "title": "Performance & SEO", "desc": "Core Web Vitals optimisation, GA4 setup, and structured data for organic growth.", "deliverables": ["Core Web Vitals", "GA4 & Tracking"]},
    ])
    belzzo_results = json.dumps({
        "cards": [
            {"metric": "+40%", "label": "Product discovery improvement", "insight": "Better filters & categories"},
            {"metric": "3.2 sec", "label": "Page load time (optimized)", "insight": "56% faster than before"},
            {"metric": "58%", "label": "Reduction in bounce rate", "insight": "More engaged visitors"},
        ],
        "rows": [
            {"metric": "Avg. page load time", "before": "5.8 sec", "after": "2.1 sec"},
            {"metric": "Mobile Lighthouse score", "before": "42", "after": "94"},
            {"metric": "Checkout completion rate", "before": "62%", "after": "89%"},
            {"metric": "Organic traffic potential", "before": "Minimal", "after": "+150% indexed"},
        ]
    })
    belzzo_gallery = json.dumps([
        {"type": "web", "url": "/assets/images/portfolio-details/Screenshot%202026-02-26%20121652.png", "label": "Home Page", "alt": "Belzzo home page — collections overview"},
        {"type": "web", "url": "/assets/images/portfolio-details/Screenshot%202026-02-26%20121706.png", "label": "Popular Products", "alt": "Belzzo popular products with category filters"},
        {"type": "web", "url": "/assets/images/portfolio-details/Screenshot%202026-02-26%20121717.png", "label": "Featured Offers", "alt": "Belzzo featured offers and promotions section"},
        {"type": "web", "url": "/assets/images/portfolio-details/Screenshot%202026-02-27%20093226.png", "label": "Product Detail", "alt": "Belzzo product detail page"},
        {"type": "web", "url": "/assets/images/portfolio-details/Screenshot%202026-02-27%20093307.png", "label": "Collections", "alt": "Belzzo collections page"},
        {"type": "app", "url": "/assets/images/portfolio-details/Belzzo_app_1.png", "label": "Home", "alt": "Belzzo app — home screen"},
        {"type": "app", "url": "/assets/images/portfolio-details/Belzzo_app_2.png", "label": "Shop", "alt": "Belzzo app — shop screen"},
        {"type": "app", "url": "/assets/images/portfolio-details/Belzzo_app_3.png", "label": "Product", "alt": "Belzzo app — product screen"},
        {"type": "app", "url": "/assets/images/portfolio-details/Belzzo_app_4.png", "label": "Cart", "alt": "Belzzo app — cart screen"},
        {"type": "app", "url": "/assets/images/portfolio-details/Belzzo_app_5.png", "label": "Offers", "alt": "Belzzo app — offers screen"},
    ])

    erp_challenges = json.dumps([
        {"tag": "Process", "severity": "Critical", "title": "Paper-based production tracking",
         "desc": "Shop-floor records were maintained on paper, causing data loss and production delays.",
         "impact": "Management had no real-time visibility into work-in-progress, leading to missed delivery commitments."},
        {"tag": "Technical", "severity": "High", "title": "Disconnected inventory & purchase systems",
         "desc": "Inventory, purchase orders, and billing ran on separate spreadsheets with no sync.",
         "impact": "Stock discrepancies, over-purchasing, and manual reconciliation consuming 20+ hours/week."},
        {"tag": "Finance", "severity": "High", "title": "GST billing errors",
         "desc": "Manual GST calculation across multiple tax slabs resulted in frequent billing mistakes.",
         "impact": "Compliance risk and customer disputes that damaged trust and delayed payments."},
        {"tag": "UX", "severity": "Medium", "title": "Zero vendor portal",
         "desc": "Vendors submitted quotes and invoices via WhatsApp and email with no structured workflow.",
         "impact": "Procurement cycle stretched to 7+ days and created a high risk of duplicate payments."},
    ])
    erp_solution_steps = json.dumps([
        {"tag": "Inventory", "title": "Real-time Inventory Module",
         "points": ["Barcode-driven stock-in / stock-out with batch tracking", "Auto-reorder triggers when stock falls below threshold"]},
        {"tag": "Production", "title": "Production Line Tracker",
         "points": ["Digital work orders linked to BOM (Bill of Materials)", "Live dashboard showing WIP status across all shop floors"]},
        {"tag": "Finance", "title": "GST Billing & Purchase Orders",
         "points": ["Auto-calculated GST invoices with e-Invoice API integration", "Multi-approval purchase order workflow with vendor portal"]},
    ])
    erp_services = json.dumps([
        {"num": "01", "title": "System Architecture", "desc": "Multi-module ERP design with role-based access control.", "deliverables": ["ERD", "API Blueprint"]},
        {"num": "02", "title": "Inventory & Production", "desc": "Real-time stock management and production tracking.", "deliverables": ["Barcode System", "WIP Dashboard"]},
        {"num": "03", "title": "Finance & GST", "desc": "Automated billing, e-invoicing, and financial reporting.", "deliverables": ["GST Invoices", "P&L Reports"]},
        {"num": "04", "title": "Deployment & Training", "desc": "On-premise + cloud hybrid deployment with staff onboarding.", "deliverables": ["Admin Training", "SLA Support"]},
    ])
    erp_results = json.dumps({
        "cards": [
            {"metric": "60%", "label": "Reduction in manual data entry", "insight": "Automated workflows replaced spreadsheets"},
            {"metric": "2 days", "label": "Purchase cycle (was 7 days)", "insight": "3.5x faster procurement"},
            {"metric": "Zero", "label": "GST billing errors post-launch", "insight": "Auto-calculation & validation"},
        ],
        "rows": [
            {"metric": "Manual entry hours/week", "before": "20+ hrs", "after": "< 4 hrs"},
            {"metric": "Purchase cycle time", "before": "7 days", "after": "2 days"},
            {"metric": "Stock accuracy", "before": "74%", "after": "98.5%"},
            {"metric": "GST filing preparation time", "before": "3 days", "after": "4 hours"},
        ]
    })
    erp_gallery = json.dumps([
        {"type": "web", "url": "https://images.unsplash.com/photo-1551288049-bebda4e38f71?w=1200&q=80", "label": "Dashboard", "alt": "ERP main dashboard with KPIs"},
        {"type": "web", "url": "https://images.unsplash.com/photo-1556761175-5973dc0f32e7?w=1200&q=80", "label": "Inventory", "alt": "Inventory management module"},
        {"type": "web", "url": "https://images.unsplash.com/photo-1460925895917-afdab827c52f?w=1200&q=80", "label": "Analytics", "alt": "Production analytics and reporting"},
    ])

    food_challenges = json.dumps([
        {"tag": "UX", "severity": "Critical", "title": "Real-time order tracking absent",
         "desc": "Customers had no visibility into their order status after placing an order.",
         "impact": "High support ticket volume and customer churn due to uncertainty about delivery time."},
        {"tag": "Technical", "severity": "High", "title": "Driver assignment is manual",
         "desc": "Dispatchers had to manually call drivers and assign orders, causing delays at peak hours.",
         "impact": "Average delivery time 45% higher than competitor apps during the dinner rush."},
        {"tag": "Business", "severity": "High", "title": "No dynamic pricing engine",
         "desc": "Fixed delivery fees regardless of distance, time, or demand resulted in thin margins.",
         "impact": "Platform became unprofitable at peak hours when delivery costs spiked."},
        {"tag": "Technical", "severity": "Medium", "title": "Restaurant panel lacked automation",
         "desc": "Menu updates, stock-outs, and order acceptance were all manual processes for restaurant owners.",
         "impact": "Outdated menus and missed orders damaged the platform's reputation with customers."},
    ])
    food_solution_steps = json.dumps([
        {"tag": "Mobile", "title": "Customer App (Flutter)",
         "points": ["Live GPS tracking with driver location on map", "Push notifications for every order lifecycle event"]},
        {"tag": "Platform", "title": "Dynamic Pricing & Assignment",
         "points": ["Surge pricing algorithm based on demand, distance, and weather", "Auto-assignment engine matching nearest available driver in <5 seconds"]},
        {"tag": "Portal", "title": "Restaurant Management Panel",
         "points": ["Real-time order management with sound alerts", "One-click menu and stock-out toggle"]},
    ])
    food_services = json.dumps([
        {"num": "01", "title": "Flutter Mobile App", "desc": "Cross-platform customer and driver apps with real-time sync.", "deliverables": ["Customer App", "Driver App"]},
        {"num": "02", "title": "Node.js Backend", "desc": "Scalable REST API with Socket.io for real-time order events.", "deliverables": ["WebSocket API", "Notification Service"]},
        {"num": "03", "title": "Restaurant Panel", "desc": "Web-based management portal for menu and order management.", "deliverables": ["Menu Manager", "Order Dashboard"]},
        {"num": "04", "title": "Maps & Pricing Engine", "desc": "Google Maps integration and dynamic surge pricing algorithm.", "deliverables": ["Live GPS Tracking", "Surge Pricing"]},
    ])
    food_results = json.dumps({
        "cards": [
            {"metric": "8,000+", "label": "Orders per week at peak", "insight": "3x growth in 4 months"},
            {"metric": "28 min", "label": "Average delivery time (was 47)", "insight": "40% faster delivery"},
            {"metric": "4.7★", "label": "App store rating", "insight": "Based on 2,400+ reviews"},
        ],
        "rows": [
            {"metric": "Average delivery time", "before": "47 min", "after": "28 min"},
            {"metric": "Driver assignment time", "before": "3–5 min (manual)", "after": "< 5 seconds"},
            {"metric": "Support tickets/week", "before": "320+", "after": "80"},
            {"metric": "Platform margin at peak", "before": "Negative", "after": "+12% net"},
        ]
    })
    food_gallery = json.dumps([
        {"type": "app", "url": "https://images.unsplash.com/photo-1526498460520-4c246339dccb?w=600&q=80", "label": "Home", "alt": "Food delivery app — home screen"},
        {"type": "app", "url": "https://images.unsplash.com/photo-1512941937669-90a1b58e7e9c?w=600&q=80", "label": "Order Tracking", "alt": "Live GPS order tracking screen"},
        {"type": "app", "url": "https://images.unsplash.com/photo-1555066931-4365d14bab8c?w=600&q=80", "label": "Restaurant", "alt": "Restaurant listing screen"},
    ])

    all_posts = [
        Portfolio(
            title='Belzzo Kids Footwear E-Commerce Store',
            slug='belzzo-kids-footwear',
            category='Web',
            client_name='Belzzo',
            theme_color='#2F55F4',
            is_published=True,
            hero_outcome='+40% product discovery & -32% checkout drop-off',
            hero_description='IV Infotech built a fast, conversion-focused kids footwear store — smart catalog navigation, streamlined checkout, and a mobile-first experience that drives sales.',
            hero_image_web='/assets/images/portfolio-details/Screenshot 2026-02-26 121652.png',
            hero_image_app='/assets/images/portfolio-details/Screenshot 2026-02-26 121913.png',
            kpi_1_value='+40%', kpi_1_label='Discovery',
            kpi_2_value='-32%', kpi_2_label='Checkout Drop',
            kpi_3_value='90+',  kpi_3_label='Mobile Score',
            industry='Kids Footwear', market='India', goal='Conversion-focused online store',
            client_story_p1='Belzzo is a fast-growing kids footwear brand in India. They needed a conversion-ready eCommerce store with intuitive product discovery, mobile-first design, and a frictionless checkout to boost sales.',
            client_story_p2='IV Infotech partnered with Belzzo to design and build a scalable platform covering UI/UX, storefront development, SEO, and analytics from the ground up.',
            challenges=belzzo_challenges,
            solution_steps=belzzo_solution_steps,
            services=belzzo_services,
            results=belzzo_results,
            gallery=belzzo_gallery,
            created_at=datetime(2026, 2, 26),
        ),
        Portfolio(
            title='Manufacturing ERP System',
            slug='manufacturing-erp-system',
            category='CRM',
            client_name='Gujarat Manufacturing Co.',
            theme_color='#10B981',
            is_published=True,
            hero_outcome='60% reduction in manual entry & 3.5x faster procurement',
            hero_description='IV Infotech built an end-to-end ERP covering inventory, GST billing, production line tracking, and a vendor portal for a mid-sized Gujarat manufacturing firm.',
            hero_image_web='https://images.unsplash.com/photo-1551288049-bebda4e38f71?w=800&q=80',
            hero_image_app=None,
            kpi_1_value='60%',  kpi_1_label='Less Manual Entry',
            kpi_2_value='2 days', kpi_2_label='Purchase Cycle',
            kpi_3_value='98.5%', kpi_3_label='Stock Accuracy',
            industry='Manufacturing', market='India (B2B)', goal='End-to-end digital operations',
            client_story_p1='A mid-sized auto-parts manufacturer in Gujarat was running operations on paper records and disconnected spreadsheets. Growth had plateaued because the team spent more time on data coordination than production.',
            client_story_p2='IV Infotech designed and delivered a custom ERP covering every department — from the shop floor to the finance team — in a single integrated platform.',
            challenges=erp_challenges,
            solution_steps=erp_solution_steps,
            services=erp_services,
            results=erp_results,
            gallery=erp_gallery,
            created_at=datetime(2026, 1, 20),
        ),
        Portfolio(
            title='Hyperlocal Food Delivery App',
            slug='hyperlocal-food-delivery-app',
            category='App',
            client_name='QuickBite',
            theme_color='#F59E0B',
            is_published=True,
            hero_outcome='8,000+ orders/week & 40% faster delivery time',
            hero_description='IV Infotech built a full-stack  on-demand food delivery platform with live GPS tracking, dynamic surge pricing, and a restaurant management panel — deployed in 3 cities in 90 days.',
            hero_image_web=None,
            hero_image_app='https://images.unsplash.com/photo-1526498460520-4c246339dccb?w=600&q=80',
            kpi_1_value='8K+', kpi_1_label='Orders / Week',
            kpi_2_value='28 min', kpi_2_label='Avg Delivery',
            kpi_3_value='4.7★', kpi_3_label='App Rating',
            industry='Food & Delivery', market='India (Tier 2 cities)', goal='Hyperlocal delivery platform',
            client_story_p1='QuickBite entered a competitive Tier-2 market with a bold promise: average delivery under 30 minutes. To deliver on this, they needed a technology partner who could build fast and scale faster.',
            client_story_p2='IV Infotech delivered the entire platform — customer app, driver app, restaurant panel, and backend — in 90 days, going live in Mehsana, Gandhinagar, and Patan simultaneously.',
            challenges=food_challenges,
            solution_steps=food_solution_steps,
            services=food_services,
            results=food_results,
            gallery=food_gallery,
            created_at=datetime(2026, 1, 10),
        ),
    ]

    to_insert = [p for p in all_posts if p.slug not in existing]
    if not to_insert:
        return
    db.session.bulk_save_objects(to_insert)
    db.session.commit()
    print(f'Seeded {len(to_insert)} portfolio entries.')


@app.cli.command('seed-portfolio')
def seed_portfolio_cmd():
    """Seed portfolios table with 3 original case studies."""
    with app.app_context():
        _seed_portfolio()
        print('Done.')


# ── Seed: team members ─────────────────────────────────────────────────────
_TEAM_SEED = [
    # ---- Founder ----
    dict(name='Ronak Patel',    role='Founder & CEO',            category='Founder',
         bio='With over a decade of experience in software architecture and business strategy, '
             'Ronak Patel leads IV Infotech\u2019s vision of delivering world-class digital solutions from '
             'Mehsana to global clients. He drives the company\u2019s growth in AI, mobile, and '
             'enterprise software markets.',
         image_filename='images/team/founder1.jpg',
         linkedin_url='', twitter_url='', display_order=0),
    # ---- Core Team ----
    dict(name='Mukesh Suthar',  role='Full Stack Developer',      category='Core Team',
         image_filename='images/team/member9.jpeg',
         linkedin_url='https://www.linkedin.com/in/mukesh-suthar-764542253/',
         display_order=1),
    dict(name='Harshil Patel',  role='Mobile App Developer',      category='Core Team',
         image_filename='images/team/member2.jpg',
         linkedin_url='https://www.linkedin.com/in/harshil-patel-5b557024a',
         display_order=2),
    dict(name='Pooja Chauhan',  role='SEO & Content Strategist',  category='Core Team',
         image_filename='images/team/member4.jpg',
         linkedin_url='https://www.linkedin.com/in/pooja-rathod-582373327/',
         display_order=3),
    dict(name='Rutul Patel',    role='Laravel Developer',         category='Core Team',
         image_filename='images/team/member5.jpg',
         linkedin_url='', display_order=4),
    dict(name='Raj Sathavara',  role='Full Stack Developer',      category='Core Team',
         image_filename='images/team/member1.jpg',
         linkedin_url='https://www.linkedin.com/in/sathavararaj2505',
         display_order=5),
    dict(name='Hardik Vaghela', role='AI & Automation Engineer',  category='Core Team',
         image_filename='images/team/member3.jpg',
         linkedin_url='https://www.linkedin.com/in/hardik-vaghela005/',
         display_order=6),
    dict(name='Shakshi Patel',  role='Full Stack Intern',         category='Core Team',
         image_filename='images/team/member6.jpg',
         linkedin_url='https://www.linkedin.com/in/shakshi-patel-a08b16313',
         display_order=7),
    dict(name='Tulsi Patel',    role='Full Stack Intern',         category='Core Team',
         image_filename='images/team/member8.jpg',
         linkedin_url='https://www.linkedin.com/in/tulsi-patel-69416531a',
         display_order=8),
    dict(name='Jeel Patel',     role='AI & Automation Engineer',  category='Core Team',
         image_filename='images/team/member7.jpg',
         linkedin_url='https://www.linkedin.com/in/jeel-150703-patel',
         display_order=9),
]


def _seed_team():
    """Populate team_members table with existing static team data (runs only when empty)."""
    if TeamMember.query.count() > 0:
        return
    for d in _TEAM_SEED:
        db.session.add(TeamMember(
            name           = d['name'],
            role           = d['role'],
            category       = d['category'],
            bio            = d.get('bio') or '',
            image_filename = d.get('image_filename', 'images/team/member.jpg'),
            linkedin_url   = d.get('linkedin_url', ''),
            twitter_url    = d.get('twitter_url', ''),
            display_order  = d.get('display_order', 99),
            is_active      = True,
        ))
    db.session.commit()
    print(f'Seeded {len(_TEAM_SEED)} team members.')


@app.cli.command('seed-team')
def seed_team_cmd():
    """Seed team_members table with the original static team data."""
    with app.app_context():
        _seed_team()
        print('Done.')


# ── Dev server ─────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        _migrate_db()   # add any new columns to existing tables
        _seed_testimonials()
        _seed_jobs()
        _seed_blogs()
        _seed_portfolio()
        _seed_team()
        seed_settings()
    app.run(debug=True, host='0.0.0.0', port=5000)
