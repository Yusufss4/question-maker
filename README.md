# Questionnaire Website

Weighted, non-anonymous survey voting with EnterPass user login and admin panel.

## Setup

```bash
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser  # optional; or use default admin / admin123
```

## Run

```bash
python manage.py runserver
```

- **User login**: http://127.0.0.1:8000/ — Enter your 4-character EnterPass (created by admin).
- **Admin login**: http://127.0.0.1:8000/admin-auth/login/ — Username and password (staff user).

Default admin (if created via env): username `admin`, password `admin123`.

## Features

- Users log in with EnterPass; vote on published surveys; see results (with names) after close time.
- Admins manage surveys (create/edit/publish), users (add/deactivate/export Excel), and reset votes.
