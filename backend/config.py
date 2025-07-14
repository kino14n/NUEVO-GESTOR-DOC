import os

class Config:
    DB_NAME = os.getenv('DB_NAME', 'bxiooka...v6lr')  # Puedes poner aquí el valor literal si prefieres
    DB_USER = os.getenv('DB_USER', 'ucrnn5muk9xwn6ci')
    DB_PASSWORD = os.getenv('DB_PASSWORD', 'L2uKGtceIRkzhPgqCBsW')
    DB_HOST = os.getenv('DB_HOST', 'bxiokaus9xvazrlv6lr-mysql.services.clever-cloud.com')
    DB_PORT = os.getenv('DB_PORT', '3306')

    # URI de conexión SQLAlchemy
    SQLALCHEMY_DATABASE_URI = (
        f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Carpeta para archivos subidos
    UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')
