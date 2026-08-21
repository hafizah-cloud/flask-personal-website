"""A portfolio website with an authenticated SQLite guestbook."""

from __future__ import annotations

import os
from urllib.parse import urljoin, urlsplit
from datetime import datetime, timezone

from flask import Flask, flash, redirect, render_template, request, url_for
from flask_login import (
    LoginManager,
    UserMixin,
    current_user,
    login_required,
    login_user,
    logout_user,
)
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash, generate_password_hash


db = SQLAlchemy()
login_manager = LoginManager()


class User(UserMixin, db.Model):
    """A user who can sign in and post guestbook messages."""

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(60), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)

    def set_password(self, password: str) -> None:
        """Store a one-way password hash instead of the original password."""

        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        """Return whether a supplied password matches the stored hash."""

        return check_password_hash(self.password_hash, password)


class Comment(db.Model):
    """A signed-in user's message displayed on the guestbook wall."""

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(60), nullable=False)
    body = db.Column(db.String(500), nullable=False)
    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )


def _is_safe_url(target: str, host_url: str) -> bool:
    """Allow post-login redirects only to another path on this website."""

    host = urlsplit(host_url)
    candidate = urlsplit(urljoin(host_url, target))
    return candidate.scheme in {"http", "https"} and candidate.netloc == host.netloc


def _create_demo_user(app: Flask) -> None:
    """Create the assignment's tester account once, storing only a hash."""

    username = app.config["DEMO_USERNAME"].strip()
    password = app.config["DEMO_PASSWORD"]
    if not username or not password:
        return

    existing_user = db.session.scalar(db.select(User).where(User.username == username))
    if existing_user is None:
        user = User(username=username)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()


def create_app(test_config: dict | None = None) -> Flask:
    """Create and configure the Flask application."""

    app = Flask(__name__, instance_relative_config=True)
    os.makedirs(app.instance_path, exist_ok=True)

    default_database = "sqlite:///" + os.path.join(
        app.instance_path, "comments.db"
    ).replace("\\", "/")

    app.config.from_mapping(
        SECRET_KEY=os.environ.get("SECRET_KEY", "dev-change-this-before-publishing"),
        SQLALCHEMY_DATABASE_URI=os.environ.get("DATABASE_URL", default_database),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        SITE_OWNER=os.environ.get("SITE_OWNER", "Hafizah"),
        LINKEDIN_URL=os.environ.get("LINKEDIN_URL", "https://www.linkedin.com/"),
        DEMO_USERNAME=os.environ.get("DEMO_USERNAME", "tester"),
        DEMO_PASSWORD=os.environ.get("DEMO_PASSWORD", "super-secret"),
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_SECURE=os.environ.get("COOKIE_SECURE", "0") == "1",
    )

    if test_config:
        app.config.update(test_config)

    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = "login"
    login_manager.login_message = "Please log in before posting a message."
    login_manager.login_message_category = "error"

    @login_manager.user_loader
    def load_user(user_id: str) -> User | None:
        try:
            return db.session.get(User, int(user_id))
        except (TypeError, ValueError):
            return None

    @app.context_processor
    def inject_site_details() -> dict:
        owner_words = app.config["SITE_OWNER"].split()
        owner_initials = "".join(word[0] for word in owner_words[:2]).upper() or "ME"
        return {
            "site_owner": app.config["SITE_OWNER"],
            "owner_initials": owner_initials,
            "linkedin_url": app.config["LINKEDIN_URL"],
        }

    @app.get("/")
    def home():
        return render_template("home.html")

    @app.get("/projects")
    def projects():
        return render_template("projects.html")

    @app.route("/login", methods=("GET", "POST"))
    def login():
        if current_user.is_authenticated:
            return redirect(url_for("comments"))

        if request.method == "POST":
            username = request.form.get("username", "").strip()
            password = request.form.get("password", "")
            user = db.session.scalar(db.select(User).where(User.username == username))

            if user is None or not user.check_password(password):
                flash("Incorrect username or password.", "error")
            else:
                login_user(user)
                flash(f"Welcome back, {user.username}!", "success")
                next_url = request.args.get("next", "")
                if next_url and _is_safe_url(next_url, request.host_url):
                    return redirect(next_url)
                return redirect(url_for("comments"))

        return render_template("login.html")

    @app.post("/logout")
    @login_required
    def logout():
        logout_user()
        flash("You have been logged out.", "success")
        return redirect(url_for("login"))

    @app.get("/comments")
    def comments():
        all_comments = db.session.execute(
            db.select(Comment).order_by(Comment.created_at.desc(), Comment.id.desc())
        ).scalars().all()
        return render_template("comments.html", comments=all_comments)

    @app.post("/comments")
    @login_required
    def add_comment():
        body = request.form.get("body", "").strip()

        if not body:
            flash("Please enter a message.", "error")
        elif len(body) > 500:
            flash("Your message must be 500 characters or fewer.", "error")
        else:
            db.session.add(Comment(name=current_user.username, body=body))
            db.session.commit()
            flash("Thanks — your message is now on the wall!", "success")
            return redirect(url_for("comments", posted="1") + "#comments-list", 303)

        return redirect(url_for("comments") + "#comment-form", 303)

    @app.errorhandler(404)
    def page_not_found(_error):
        return render_template("404.html"), 404

    with app.app_context():
        db.create_all()
        _create_demo_user(app)

    return app


app = create_app()


if __name__ == "__main__":
    app.run(debug=True)
