from datetime import datetime
from app.database.db import db


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)   # stored hashed, never plain text
    role = db.Column(db.String(20), nullable=False, default="user")   # "user" or "admin"
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    # turn the user into a dictionary so we can send it as JSON
    # (we leave the password out on purpose)
    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "role": self.role,
            "created_at": str(self.created_at),
            "updated_at": str(self.updated_at),
        }