import os
from dotenv import load_dotenv

# read the values from the .env file
load_dotenv()


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY")

    user = os.getenv("DB_USER")
    password = os.getenv("DB_PASSWORD")
    host = os.getenv("DB_HOST")
    name = os.getenv("DB_NAME")

    SQLALCHEMY_DATABASE_URI = "mysql+pymysql://" + user + ":" + password + "@" + host + "/" + name
    SQLALCHEMY_TRACK_MODIFICATIONS = False