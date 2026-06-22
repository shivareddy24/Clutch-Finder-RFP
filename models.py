from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


# ---------------- USER ----------------
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)

    image_file = db.Column(db.String(100), nullable=False, default='default.jpg')
    password = db.Column(db.String(60), nullable=False)

    # relationships
    posts = db.relationship('Post', backref='author', lazy=True)
    ratings = db.relationship('Rating', backref='user', lazy=True)

    def __repr__(self):
        return f"User('{self.username}', '{self.email}')"


# ---------------- POST (PLAYER) ----------------
class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    # player name
    title = db.Column(db.String(100), nullable=False)

    # timestamp
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    # stats / description
    content = db.Column(db.Text, nullable=False)

    # player image
    image_file = db.Column(db.String(100), nullable=False, default='default.jpg')

    # 🎥 NEW: video support
    video_file = db.Column(db.String(200), nullable=True)

    # category (batsman / bowler / all-rounder)
    category = db.Column(db.String(20), nullable=False, default='general')

    # foreign key → user
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    # ⭐ ratings relationship
    ratings = db.relationship('Rating', backref='post', lazy=True)

    # ⭐ helper: average rating
    def average_rating(self):
        if not self.ratings:
            return 0
        return round(sum(r.score for r in self.ratings) / len(self.ratings), 2)

    def __repr__(self):
        return f"Post('{self.title}', '{self.date_posted}')"


# ---------------- RATING ----------------
class Rating(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    score = db.Column(db.Integer, nullable=False)  # 1–5 stars

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)

    def __repr__(self):
        return f"Rating({self.score})"