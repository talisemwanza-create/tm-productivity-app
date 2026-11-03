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


api.add_resource(Signup, "/signup", endpoint="signup")
api.add_resource(Login, "/login", endpoint="login")
api.add_resource(Logout, "/logout", endpoint="logout")
api.add_resource(CheckSession, "/check_session", endpoint="check_session")

if __name__ == "__main__":
    app.run(port=5555, debug=True)