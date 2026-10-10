from werkzeug.security import generate_password_hash

from app.main import app
from app.database.db import db
from app.models.user import User
from app.models.task import Task


# sample users (these are test accounts only)
USERS = [
    {"name": "Admin User", "email": "admin@example.com", "password": "Admin@123", "role": "admin"},
    {"name": "Rahul Sharma", "email": "rahul@example.com", "password": "User@123", "role": "user"},
    {"name": "Priya Patil", "email": "priya@example.com", "password": "User@123", "role": "user"},
]

# sample tasks: (owner email, title, description, status)
TASKS = [
    ("rahul@example.com", "Design login page", "Create the screen where users enter email and password.", "Pending"),
    ("rahul@example.com", "Write API documentation", "Document all endpoints with example requests.", "In Progress"),
    ("priya@example.com", "Fix signup validation", "Show a clear error when the email is already used.", "Testing"),
    ("priya@example.com", "Set up database backup", "Create a daily backup of the task database.", "Completed"),
    ("admin@example.com", "Review team tasks", "Check the progress of all tasks and update statuses.", "Pending"),
]


def seed():
    with app.app_context():

        # 1. add the users (skip the ones that already exist)
        for item in USERS:
            old_user = User.query.filter_by(email=item["email"]).first()

            if old_user:
                print("User already exists:", item["email"])
                continue

            new_user = User(
                name=item["name"],
                email=item["email"],
                password=generate_password_hash(item["password"]),
                role=item["role"],
            )
            db.session.add(new_user)
            print("User added:", item["email"])

        db.session.commit()

        # 2. add the tasks (skip the ones that already exist)
        for owner_email, title, description, status in TASKS:
            owner = User.query.filter_by(email=owner_email).first()

            old_task = Task.query.filter_by(user_id=owner.id, title=title).first()

            if old_task:
                print("Task already exists:", title)
                continue

            new_task = Task(
                user_id=owner.id,
                title=title,
                description=description,
                status=status,
            )
            db.session.add(new_task)
            print("Task added:", title)

        db.session.commit()
        print("Seeding finished")


if __name__ == "__main__":
    seed()