import jwt
from datetime import datetime, timedelta
from flask import current_app


def create_token(user):
    # what we store inside the token
    data = {
        "user_id": user.id,
        "role": user.role,
        "exp": datetime.utcnow() + timedelta(hours=72),   # token expires after 72 hours
    }
    token = jwt.encode(data, current_app.config["SECRET_KEY"], algorithm="HS256")
    return token


def read_token(token):
    # returns the data inside the token, or raises an error if it is wrong or expired
    return jwt.decode(token, current_app.config["SECRET_KEY"], algorithms=["HS256"])