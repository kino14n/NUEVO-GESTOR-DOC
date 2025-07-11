
import os

SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL') or 'mysql+pymysql://usuario:clave@host/dbname'
SECRET_KEY = os.getenv("SECRET_KEY", "esto-es-un-secreto")
UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", "./uploads")
ALLOWED_EXTENSIONS = {'pdf'}
