from flask import Blueprint, request, jsonify, g
from sqlalchemy.exc import SQLAlchemyError

from app.database.db import db
from app.models.task import Task, STATUS_LIST
from app.auth.decorators import login_required, admin_required

task_bp = Blueprint("tasks", __name__, url_prefix="/api/tasks")


# admin can use any task, a normal user only their own
def can_use_task(task):
    if g.current_user.role == "admin":
        return True
    return task.user_id == g.current_user.id


# CREATE a task
@task_bp.route("", methods=["POST"])
@login_required
def create_task():
    data = request.get_json()

    if not data:
        return jsonify({"error": "Request body must be JSON"}), 400

    title = data.get("title")
    description = data.get("description")

    if not title or not title.strip():
        return jsonify({"error": "title is required"}), 400

    # the task always belongs to the person who creates it, status starts as Pending
    new_task = Task(
        user_id=g.current_user.id,
        title=title.strip(),
        description=description,
        status="Pending",
    )

    try:
        db.session.add(new_task)
        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()
        return jsonify({"error": "Database error, please try again"}), 500

    return jsonify({"message": "Task created", "task": new_task.to_dict()}), 201


# LIST tasks
@task_bp.route("", methods=["GET"])
@login_required
def list_tasks():
    if g.current_user.role == "admin":
        tasks = Task.query.order_by(Task.id).all()
    else:
        tasks = Task.query.filter_by(user_id=g.current_user.id).order_by(Task.id).all()

    result = []
    for task in tasks:
        result.append(task.to_dict())

    return jsonify({"count": len(result), "tasks": result}), 200


# VIEW one task
@task_bp.route("/<int:task_id>", methods=["GET"])
@login_required
def view_task(task_id):
    task = db.session.get(Task, task_id)

    if task is None:
        return jsonify({"error": "Task not found"}), 404

    if not can_use_task(task):
        return jsonify({"error": "You are not allowed to see this task"}), 403

    return jsonify({"task": task.to_dict()}), 200


# UPDATE title and description
@task_bp.route("/<int:task_id>", methods=["PUT"])
@login_required
def update_task(task_id):
    task = db.session.get(Task, task_id)

    if task is None:
        return jsonify({"error": "Task not found"}), 404

    if not can_use_task(task):
        return jsonify({"error": "You are not allowed to edit this task"}), 403

    data = request.get_json()

    if not data:
        return jsonify({"error": "Request body must be JSON"}), 400

    # a normal user is not allowed to change the status
    if "status" in data and g.current_user.role != "admin":
        return jsonify({"error": "Only admin can change the status"}), 403

    if "title" in data:
        if not data["title"] or not data["title"].strip():
            return jsonify({"error": "title cannot be empty"}), 400
        task.title = data["title"].strip()

    if "description" in data:
        task.description = data["description"]

    try:
        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()
        return jsonify({"error": "Database error, please try again"}), 500

    return jsonify({"message": "Task updated", "task": task.to_dict()}), 200


# UPDATE status (admin only)
@task_bp.route("/<int:task_id>/status", methods=["PATCH"])
@login_required
@admin_required
def update_status(task_id):
    task = db.session.get(Task, task_id)

    if task is None:
        return jsonify({"error": "Task not found"}), 404

    data = request.get_json()

    if not data or "status" not in data:
        return jsonify({"error": "status is required"}), 400

    if data["status"] not in STATUS_LIST:
        return jsonify({"error": "status must be one of: " + ", ".join(STATUS_LIST)}), 400

    task.status = data["status"]

    try:
        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()
        return jsonify({"error": "Database error, please try again"}), 500

    return jsonify({"message": "Status updated", "task": task.to_dict()}), 200