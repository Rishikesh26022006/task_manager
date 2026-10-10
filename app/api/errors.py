from flask import jsonify
from werkzeug.exceptions import HTTPException
from sqlalchemy.exc import SQLAlchemyError

from app.database.db import db


def register_error_handlers(app):

    # 404 not found, 405 wrong method, 400 bad JSON, 415 wrong content type, etc.
    @app.errorhandler(HTTPException)
    def handle_http_error(error):
        return jsonify({"error": error.description}), error.code

    # any database problem that we did not catch ourselves
    @app.errorhandler(SQLAlchemyError)
    def handle_db_error(error):
        db.session.rollback()
        app.logger.error("Database error: %s", error)
        return jsonify({"error": "Database error, please try again"}), 500

    # anything else we did not expect
    @app.errorhandler(Exception)
    def handle_other_error(error):
        app.logger.error("Unexpected error: %s", error)
        return jsonify({"error": "Something went wrong on the server"}), 500