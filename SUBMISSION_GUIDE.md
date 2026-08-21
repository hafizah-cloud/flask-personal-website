# Mini Project B Submission Guide

## What is completed

- Task A: database-backed login and logout
- Task B: only logged-in users can post comments, enforced by the Flask server
- Real security: passwords are stored as one-way hashes
- Bonus Task A: a separate portfolio introduction page
- Bonus Task B: the required test account is created automatically

Test account:

- Username: `tester`
- Password: `super-secret`

## Test locally

```bash
python -m venv .venv
```

Activate the environment, then run:

```bash
pip install -r requirements.txt
python app.py
```

Open `http://127.0.0.1:5000`, select **Guestbook**, and test login and logout.

## Publish on PythonAnywhere

1. Upload and extract this project, or push it to GitHub and clone it in a PythonAnywhere Bash console.
2. Create and activate a virtual environment.
3. Run `pip install -r requirements.txt`.
4. In the PythonAnywhere **Web** tab, create a manually configured web app.
5. Set the virtualenv path and static mapping described in `README.md`.
6. Copy the WSGI configuration from `README.md`, replacing `YOUR-USERNAME`, the LinkedIn URL, and the secret key.
7. Reload the web app.
8. Test the public pages, `tester` login, comment posting, and logout.
9. Submit the public PythonAnywhere website URL in the assignment page.

The ZIP itself is the completed source-code deliverable. The course submission still requires the public PythonAnywhere URL, which can only be obtained after deployment to your account.
