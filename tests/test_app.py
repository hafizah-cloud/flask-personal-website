import pytest

from app import Comment, User, create_app, db


@pytest.fixture()
def app(tmp_path):
    database_path = tmp_path / "test.db"
    test_app = create_app(
        {
            "TESTING": True,
            "SECRET_KEY": "test-key",
            "SQLALCHEMY_DATABASE_URI": f"sqlite:///{database_path.as_posix()}",
            "DEMO_USERNAME": "tester",
            "DEMO_PASSWORD": "super-secret",
        }
    )
    yield test_app
    with test_app.app_context():
        db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()


def log_in(client, username="tester", password="super-secret"):
    return client.post(
        "/login",
        data={"username": username, "password": password},
        follow_redirects=True,
    )


def test_public_pages_load(client):
    assert client.get("/").status_code == 200
    assert client.get("/projects").status_code == 200
    assert client.get("/comments").status_code == 200
    assert client.get("/login").status_code == 200


def test_missing_page_uses_custom_404(client):
    response = client.get("/not-a-real-page")
    assert response.status_code == 404
    assert b"This page wandered off" in response.data


def test_demo_user_is_seeded_with_hashed_password(app):
    with app.app_context():
        user = db.session.scalar(db.select(User).where(User.username == "tester"))
        assert user is not None
        assert user.password_hash != "super-secret"
        assert user.check_password("super-secret")


def test_valid_login_starts_session(client):
    response = log_in(client)
    assert response.status_code == 200
    assert b"Welcome back, tester!" in response.data
    assert b"Posting as <strong>tester</strong>" in response.data


def test_invalid_login_is_rejected(client):
    response = log_in(client, password="wrong-password")
    assert b"Incorrect username or password." in response.data
    assert b"Posting as" not in response.data


def test_anonymous_post_is_blocked(app, client):
    response = client.post("/comments", data={"body": "Should not be saved"})
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]
    with app.app_context():
        assert db.session.scalar(db.select(db.func.count(Comment.id))) == 0


def test_logged_in_user_can_add_comment(app, client):
    log_in(client)
    response = client.post(
        "/comments",
        data={"name": "forged-name", "body": "A clear and thoughtful portfolio!"},
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"A clear and thoughtful portfolio!" in response.data
    with app.app_context():
        comment = db.session.scalar(db.select(Comment))
        assert comment.name == "tester"


@pytest.mark.parametrize("body", ["", " ", "m" * 501])
def test_invalid_comment_is_rejected(app, client, body):
    log_in(client)
    response = client.post("/comments", data={"body": body}, follow_redirects=True)
    assert response.status_code == 200
    with app.app_context():
        assert db.session.scalar(db.select(db.func.count(Comment.id))) == 0


def test_comment_content_is_escaped(client):
    log_in(client)
    response = client.post(
        "/comments",
        data={"body": "<script>alert('x')</script>"},
        follow_redirects=True,
    )
    assert b"<script>" not in response.data
    assert b"&lt;script&gt;" in response.data


def test_logout_ends_session(client):
    log_in(client)
    response = client.post("/logout", follow_redirects=True)
    assert response.status_code == 200
    assert b"You have been logged out." in response.data
    blocked = client.post("/comments", data={"body": "Not allowed"})
    assert blocked.status_code == 302
    assert "/login" in blocked.headers["Location"]


def test_external_next_url_is_not_used(client):
    response = client.post(
        "/login?next=https://example.com/unsafe",
        data={"username": "tester", "password": "super-secret"},
    )
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/comments")
