import os

class Config:
    DB_NAME = os.getenv('DB_NAME', 'b4ntlli8yhth2jvjf7ih')
    DB_USER = os.getenv('DB_USER', 'uymzq1mb64bx8ldn')
    DB_PASSWORD = os.getenv('DB_PASSWORD', '3gYrCOKs8XCJY0DiLNhV')
    DB_HOST = os.getenv('DB_HOST', 'us-east.connect.psdb.cloud')
    DB_PORT = os.getenv('DB_PORT', '3306')

    SQLALCHEMY_DATABASE_URI = (
        f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
        "?charset=utf8mb4"
        "&ssl_ca=/etc/ssl/cert.pem"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')
