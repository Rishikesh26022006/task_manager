from functools import wraps
from flask import request, jsonify, g
import jwt

from app.database.db import db
from app.models.user import User
from app.auth.jwt_helper import read_token


# use this on any route that needs a logged-in user
def login_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        # the token comes in the header like:  Authorization: Bearer <token>
        header = request.headers.get("Authorization")

        if not header or not header.startswith("Bearer "):
            return jsonify({"error": "Token is missing"}), 401

        token = header.split(" ")[1]

        try:
            data = read_token(token)
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token has expired, please login again"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Token is invalid"}), 401

        # find the user who owns this token
        user = db.session.get(User, data["user_id"])
        if user is None:
            return jsonify({"error": "User not found"}), 401

        # save the user so the route can use it
        g.current_user = user

        return func(*args, **kwargs)
    return wrapper


# use this on routes that only admins can use (put it under login_required)
def admin_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if g.current_user.role != "admin":
            return jsonify({"error": "Admin access required"}), 403
        return func(*args, **kwargs)
    return wrapper