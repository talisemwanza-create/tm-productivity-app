from functools import wraps

from flask import request, session
from flask_restful import Resource
from marshmallow import ValidationError
from sqlalchemy.exc import IntegrityError

from config import api, app, db
from models import Note, User
from schemas import note_schema, notes_schema, user_schema


def login_required(func):
    """Return 401 unless a user is logged in; pass the user to the handler."""

    @wraps(func)
    def wrapper(*args, **kwargs):
        user = db.session.get(User, session["user_id"]) if session.get("user_id") else None
        if not user:
            return {"error": "Unauthorized. Please log in."}, 401
        return func(*args, user=user, **kwargs)

    return wrapper


class Signup(Resource):
    def post(self):
        try:
            data = user_schema.load(request.get_json(silent=True) or {})
            user = User(username=data["username"])
            user.password = data["password"]
            db.session.add(user)
            db.session.commit()
        except ValidationError as err:
            return {"errors": err.messages}, 422
        except ValueError as err:
            return {"error": str(err)}, 422
        except IntegrityError:
            db.session.rollback()
            return {"error": "Username already taken."}, 422

        session["user_id"] = user.id
        return user_schema.dump(user), 201


class Login(Resource):
    def post(self):
        data = request.get_json(silent=True) or {}
        user = User.query.filter_by(username=data.get("username")).first()
        if not user or not user.authenticate(data.get("password") or ""):
            return {"error": "Invalid username or password."}, 401
        session["user_id"] = user.id
        return user_schema.dump(user), 200


class Logout(Resource):
    def delete(self):
        session.pop("user_id", None)
        return {}, 204


class CheckSession(Resource):
    method_decorators = [login_required]

    def get(self, user):
        return user_schema.dump(user), 200

def get_owned_note(note_id, user):
    """Return (note, error_response); 404 if missing, 403 if someone else's."""
    note = db.session.get(Note, note_id)
    if not note:
        return None, ({"error": "Note not found."}, 404)
    if note.user_id != user.id:
        return None, ({"error": "Forbidden."}, 403)
    return note, None


class NoteIndex(Resource):
    method_decorators = [login_required]

    def get(self, user):
        page = request.args.get("page", 1, type=int)
        per_page = min(request.args.get("per_page", 5, type=int), 50)
        pagination = (
            Note.query.filter_by(user_id=user.id)
            .order_by(Note.created_at.desc())
            .paginate(page=page, per_page=per_page, error_out=False)
        )
        return {
            "page": pagination.page,
            "per_page": pagination.per_page,
            "total": pagination.total,
            "total_pages": pagination.pages,
            "notes": notes_schema.dump(pagination.items),
        }, 200

    def post(self, user):
        try:
            data = note_schema.load(request.get_json(silent=True) or {})
            note = Note(user_id=user.id, **data)
            db.session.add(note)
            db.session.commit()
        except ValidationError as err:
            return {"errors": err.messages}, 422
        except ValueError as err:
            return {"error": str(err)}, 422
        return note_schema.dump(note), 201


class NoteDetail(Resource):
    method_decorators = [login_required]

    def get(self, note_id, user):
        note, error = get_owned_note(note_id, user)
        return error or (note_schema.dump(note), 200)

    def patch(self, note_id, user):
        note, error = get_owned_note(note_id, user)
        if error:
            return error
        try:
            data = note_schema.load(request.get_json(silent=True) or {}, partial=True)
            for key, value in data.items():
                setattr(note, key, value)
            db.session.commit()
        except ValidationError as err:
            return {"errors": err.messages}, 422
        except ValueError as err:
            db.session.rollback()
            return {"error": str(err)}, 422
        return note_schema.dump(note), 200

    def delete(self, note_id, user):
        note, error = get_owned_note(note_id, user)
        if error:
            return error
        db.session.delete(note)
        db.session.commit()
        return {}, 204

api.add_resource(Signup, "/signup", endpoint="signup")
api.add_resource(Login, "/login", endpoint="login")
api.add_resource(Logout, "/logout", endpoint="logout")
api.add_resource(CheckSession, "/check_session", endpoint="check_session")

api.add_resource(NoteIndex, "/notes", endpoint="notes")
api.add_resource(NoteDetail, "/notes/<int:note_id>", endpoint="note_detail")

if __name__ == "__main__":
    app.run(port=5555, debug=True)