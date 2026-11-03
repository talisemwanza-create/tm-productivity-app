from datetime import datetime

from sqlalchemy.orm import validates

from config import bcrypt, db


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(30), nullable=False, unique=True)
    _password_hash = db.Column(db.String, nullable=False)

    notes = db.relationship("Note", back_populates="user", cascade="all, delete-orphan")

    @property
    def password(self):
        raise AttributeError("Password is write-only.")

    @password.setter
    def password(self, plain_text):
        self._password_hash = bcrypt.generate_password_hash(
            plain_text.encode("utf-8")
        ).decode("utf-8")

    def authenticate(self, plain_text):
        return bcrypt.check_password_hash(self._password_hash, plain_text.encode("utf-8"))

    @validates("username")
    def validate_username(self, key, value):
        if not value or len(value.strip()) < 3:
            raise ValueError("Username must be at least 3 characters.")
        return value.strip()


class Note(db.Model):
    __tablename__ = "notes"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50), nullable=False, default="general")
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    user = db.relationship("User", back_populates="notes")

    @validates("title", "content")
    def validate_not_empty(self, key, value):
        if not value or not value.strip():
            raise ValueError(f"{key} cannot be empty.")
        return value.strip()