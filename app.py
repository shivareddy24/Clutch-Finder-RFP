from flask import Flask, render_template, redirect, url_for, flash, request, session
from forms import RegistrationForm, LoginForm, PostForm, PlayerForm
from models import db, User, Post, Rating
from werkzeug.utils import secure_filename
import os
import uuid
import pandas as pd

app = Flask(__name__)

basedir = os.path.abspath(os.path.dirname(__file__))

app.config['SECRET_KEY'] = 'change-this-to-a-secure-random-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'instance', 'site.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

# ── Folders ──
PROFILE_PICS_FOLDER = os.path.join(basedir, "static", "profile_pics")
VIDEO_FOLDER = os.path.join(basedir, "static", "videos")

os.makedirs(PROFILE_PICS_FOLDER, exist_ok=True)
os.makedirs(VIDEO_FOLDER, exist_ok=True)

# ── Auto-create DB ──
with app.app_context():
    db.create_all()

# ─────────────────────────────────────────────
# 🛠 HELPERS
# ─────────────────────────────────────────────

def get_current_user():
    if 'user_id' in session:
        return User.query.get(session['user_id'])
    return None


def save_player_image(file_storage, player_name):
    if not file_storage or file_storage.filename == '':
        return 'default.jpg'

    ext = file_storage.filename.rsplit('.', 1)[1].lower()

    filename = (
        player_name.strip().lower()
        .replace(" ", "_").replace(".", "")
    ) + f"_{uuid.uuid4().hex[:6]}.{ext}"

    file_storage.save(os.path.join(PROFILE_PICS_FOLDER, filename))
    return filename


def save_video(file_storage):
    if not file_storage or file_storage.filename == '':
        return None

    filename = secure_filename(file_storage.filename)
    unique_name = str(uuid.uuid4()) + "_" + filename

    file_storage.save(os.path.join(VIDEO_FOLDER, unique_name))
    return unique_name


def build_description(category, form):
    if category == 'batsman':
        return f"Runs: {form.runs.data or 'N/A'} | Avg: {form.avg.data or 'N/A'} | HS: {form.hs.data or 'N/A'}"
    elif category == 'allrounder':
        return f"Runs: {form.runs.data or 'N/A'} | Wickets: {form.wickets.data or 'N/A'} | Eco: {form.eco.data or 'N/A'}"
    elif category == 'bowler':
        return f"Wickets: {form.wickets.data or 'N/A'} | Eco: {form.eco.data or 'N/A'} | Best: {form.best.data or 'N/A'}"
    return ""


# ─────────────────────────────────────────────
# 🏠 HOME
# ─────────────────────────────────────────────
@app.route("/")
def home():
    posts = Post.query.order_by(Post.date_posted.desc()).all()
    return render_template("home.html", posts=posts)


# ─────────────────────────────────────────────
# 📄 PLAYER DETAIL
# ─────────────────────────────────────────────
@app.route("/post/<int:post_id>")
def post_detail(post_id):
    post = Post.query.get_or_404(post_id)

    ratings = Rating.query.filter_by(post_id=post.id).all()
    avg_rating = round(sum(r.score for r in ratings) / len(ratings), 1) if ratings else 0

    return render_template("post_detail.html", post=post, avg_rating=avg_rating)


# ─────────────────────────────────────────────
# ⭐ RATE PLAYER
# ─────────────────────────────────────────────
@app.route("/rate/<int:post_id>/<int:score>")
def rate(post_id, score):
    user = get_current_user()

    if not user:
        flash("❌ Login required", "danger")
        return redirect(url_for('login'))

    existing = Rating.query.filter_by(user_id=user.id, post_id=post_id).first()

    if existing:
        existing.score = score
    else:
        rating = Rating(score=score, user_id=user.id, post_id=post_id)
        db.session.add(rating)

    db.session.commit()
    return redirect(url_for('post_detail', post_id=post_id))


# ─────────────────────────────────────────────
# ➕ ADD PLAYER
# ─────────────────────────────────────────────
@app.route("/add-player", methods=['GET', 'POST'])
def add_player():
    form = PlayerForm()

    if form.validate_on_submit():
        user = get_current_user()

        if not user:
            flash("❌ Please login first.", "danger")
            return redirect(url_for('login'))

        image_file = save_player_image(form.image.data, form.name.data)
        video_file = save_video(form.video.data if hasattr(form, 'video') else None)

        post = Post(
            title=form.name.data.strip(),
            content=build_description(form.category.data, form),
            image_file=image_file,
            video_file=video_file,
            category=form.category.data,
            author=user
        )

        db.session.add(post)
        db.session.commit()

        flash("✅ Player added!", "success")
        return redirect(url_for('dashboard'))

    return render_template("add_player.html", form=form)


# ─────────────────────────────────────────────
# 📊 DASHBOARD
# ─────────────────────────────────────────────
@app.route("/dashboard")
def dashboard():
    user = get_current_user()

    if not user:
        flash("❌ Please login first", "danger")
        return redirect(url_for('login'))

    posts = Post.query.filter_by(user_id=user.id).all()
    ratings = Rating.query.filter_by(user_id=user.id).all()

    return render_template("dashboard.html", user=user, posts=posts, ratings=ratings)
# ─────────────────────────────────────────────
# 📥 IMPORT PLAYERS (FIXED WITH STATS)
# ─────────────────────────────────────────────
def get_image_filename(name):
    filename = (
        str(name).strip().lower()
        .replace(" ", "_").replace(".", "")
        .replace("'", "").replace("-", "_")
    ) + ".jpg"

    if not os.path.exists(os.path.join(PROFILE_PICS_FOLDER, filename)):
        return "default.jpg"

    return filename


@app.route("/import-players")
def import_players():
    file_path = os.path.join(basedir, "CLUTCH FINDER.xlsx")

    if not os.path.exists(file_path):
        flash("❌ Excel file not found.", "danger")
        return redirect(url_for('home'))

    user = get_current_user()

    if not user:
        flash("❌ Please login first.", "danger")
        return redirect(url_for('login'))

    file = pd.ExcelFile(file_path)

    count = 0

    for sheet in file.sheet_names:
        df = pd.read_excel(file, sheet_name=sheet)

        for _, row in df.iterrows():

            # 🟦 BATSMEN
            if sheet == "Sheet1":
                name = row.get('BATSMEN')
                content = f"Runs: {row.get('RUNS')} | Avg: {row.get('AVG')} | HS: {row.get('HS')}"
                category = "batsman"

            # 🟩 ALL ROUNDERS
            elif sheet == "Sheet2":
                name = row.get('ALL ROUNDERS')
                content = f"Runs: {row.get('RUNS')} | Wickets: {row.get('WICKETS')} | Eco: {row.get('ECO')}"
                category = "allrounder"

            # 🟥 BOWLERS
            elif sheet == "Sheet3":
                name = row.get('BOWLERS')
                content = f"Wickets: {row.get('WICKETS')} | Eco: {row.get('ECO')} | Best: {row.get('BEST FIG')}"
                category = "bowler"

            else:
                continue

            if pd.isna(name):
                continue

            post = Post(
                title=str(name),
                content=content,   # ✅ REAL STATS
                image_file=get_image_filename(name),
                category=category,
                author=user
            )

            db.session.add(post)
            count += 1

    db.session.commit()

    flash(f"✅ Imported {count} players with stats!", "success")
    return redirect(url_for('dashboard'))


# ─────────────────────────────────────────────
# 📝 REGISTER · LOGIN · LOGOUT
# ─────────────────────────────────────────────
@app.route("/register", methods=['GET', 'POST'])
def register():
    form = RegistrationForm()

    if form.validate_on_submit():
        user = User(
            username=form.username.data,
            email=form.email.data,
            password=form.password.data
        )

        db.session.add(user)
        db.session.commit()

        flash("✅ Account created!", "success")
        return redirect(url_for('login'))

    return render_template("register.html", form=form)


@app.route("/login", methods=['GET', 'POST'])
def login():
    form = LoginForm()

    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()

        if user and user.password == form.password.data:
            session['user_id'] = user.id
            flash("✅ Logged in!", "success")
            return redirect(url_for('dashboard'))

        flash("❌ Invalid credentials", "danger")

    return render_template("login.html", form=form)


@app.route("/logout")
def logout():
    session.pop('user_id', None)
    flash("👋 Logged out", "info")
    return redirect(url_for('home'))


# ─────────────────────────────────────────────
# ℹ️ ABOUT
# ─────────────────────────────────────────────
@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/debug-images")
def debug_images():
    if not os.path.exists(PROFILE_PICS_FOLDER):
        return "❌ profile_pics folder not found!"
    files = os.listdir(PROFILE_PICS_FOLDER)
    return "<br>".join(sorted(files)) or "📂 Folder is empty."
 


# ─────────────────────────────────────────────
# 🚀 RUN
# ─────────────────────────────────────────────
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)