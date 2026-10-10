from flask import Flask
from app.config import Config
from app.database.db import db
import app.models   # makes sure the models are loaded
from app.api.auth_routes import auth_bp
from app.api.task_routes import task_bp
from app.api.ai_routes import ai_bp
from app.api.errors import register_error_handlers

app = Flask(__name__)
app.config.from_object(Config)

# connect the database to our app
db.init_app(app)

# connect the routes
app.register_blueprint(auth_bp)
app.register_blueprint(task_bp)
app.register_blueprint(ai_bp)

# connect the error handlers
register_error_handlers(app)

# create the tables if they don't exist yet
with app.app_context():
    db.create_all()


@app.route("/")
def home():
    return {"message": "Task manager is running"}


if __name__ == "__main__":
    app.run(debug=True)