from flask import Blueprint, request, jsonify, g
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.exc import SQLAlchemyError

from app.database.db import db
from app.models.user import User
from app.auth.jwt_helper import create_token
from app.auth.decorators import login_required

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")


@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json()

    # 1. check the request has data
    if not data:
        return jsonify({"error": "Request body must be JSON"}), 400

    name = data.get("name")
    email = data.get("email")
    password = data.get("password")

    # 2. check required fields
    if not name or not email or not password:
        return jsonify({"error": "name, email and password are required"}), 400

    if "@" not in email:
        return jsonify({"error": "Email is not valid"}), 400

    if len(password) < 6:
        return jsonify({"error": "Password must be at least 6 characters"}), 400

    # 3. check the email is not already used
    old_user = User.query.filter_by(email=email).first()
    if old_user:
        return jsonify({"error": "Email already registered"}), 409

    # 4. save the new user (public registration always gives the role "user")
    new_user = User(
        name=name,
        email=email,
        password=generate_password_hash(password),
        role="user",
    )

    try:
        db.session.add(new_user)
        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()
        return jsonify({"error": "Database error, please try again"}), 500

    return jsonify({"message": "User registered", "user": new_user.to_dict()}), 201


@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json()

    if not data:
        return jsonify({"error": "Request body must be JSON"}), 400

    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({"error": "email and password are required"}), 400

    # find the user, then compare the password with the saved hash
    user = User.query.filter_by(email=email).first()

    if user is None or not check_password_hash(user.password, password):
        return jsonify({"error": "Invalid email or password"}), 401

    token = create_token(user)

    return jsonify({"message": "Login successful", "token": token, "user": user.to_dict()}), 200


@auth_bp.route("/me", methods=["GET"])
@login_required
def me():
    # shows who the token belongs to
    return jsonify({"user": g.current_user.to_dict()}), 200