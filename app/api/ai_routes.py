from flask import Blueprint, request, jsonify

from app.auth.decorators import login_required
from app.ai.gemini_client import generate_description, AIError

ai_bp = Blueprint("ai", __name__, url_prefix="/api/tasks")


@ai_bp.route("/generate-description", methods=["POST"])
@login_required
def generate_task_description():
    data = request.get_json()

    if not data:
        return jsonify({"error": "Request body must be JSON"}), 400

    title = data.get("title")

    if not isinstance(title, str) or not title.strip():
        return jsonify({"error": "title is required"}), 400

    if len(title) > 200:
        return jsonify({"error": "title must be 200 characters or less"}), 400

    try:
        description = generate_description(title.strip())
    except AIError as error:
        return jsonify({"error": error.message}), error.status_code

    return jsonify({"title": title.strip(), "description": description}), 200