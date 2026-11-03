# Productivity Notes API

A Flask REST API with session-based authentication. Users can sign up, log in, and
manage their own private notes. Each user can only view and change their own notes.
Built with Flask, SQLAlchemy, Marshmallow, Flask-RESTful, Flask-Migrate, and Flask-Bcrypt.

## Features

- Sign up, log in, log out, and session check (stay logged in on refresh)
- Passwords hashed with bcrypt and never returned by the API
- Full CRUD for notes, restricted to the logged-in owner
- Paginated notes list
- Validation at the table, model, and schema levels

## Installation

```bash
git clone https://github.com/talisemwanza-create/tm-productivity-app.git
cd tm-productivity-app
pipenv install
pipenv shell
export FLASK_APP=server/app.py
flask db upgrade
python server/seed.py
```

## Run

```bash
flask run -p 5555
```

The API runs at http://127.0.0.1:5555.

Seeded users: `alice`, `bob`, `carol` (password for all: `password123`).

## Endpoints

| Method | Route | Auth required | Description |
|---|---|---|---|
| POST | `/signup` | No | Create a user and log in. Body: `username`, `password`. Returns 201, or 422 for invalid data or a taken username |
| POST | `/login` | No | Log in. Body: `username`, `password`. Returns 200, or 401 for bad credentials |
| DELETE | `/logout` | No | Log out. Returns 204 |
| GET | `/check_session` | Yes | Return the logged-in user. Returns 200, or 401 if not logged in |
| GET | `/notes?page=1&per_page=5` | Yes | Paginated list of your notes (newest first). Returns `page`, `per_page`, `total`, `total_pages`, `notes` |
| POST | `/notes` | Yes | Create a note. Body: `title`, `content`, `category` (optional). Returns 201 |
| GET | `/notes/<id>` | Yes | Get one of your notes. 404 if missing, 403 if it belongs to another user |
| PATCH | `/notes/<id>` | Yes | Update one of your notes. Returns 200 |
| DELETE | `/notes/<id>` | Yes | Delete one of your notes. Returns 204 |

Requests to protected routes without a session return `401`.

## Project Structure

```
server/
  config.py    # app, database, bcrypt, and API setup
  models.py    # User and Note models
  schemas.py   # Marshmallow schemas and validation
  app.py       # routes
  seed.py      # sample data
migrations/    # database migrations
```