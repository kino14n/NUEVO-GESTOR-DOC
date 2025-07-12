import os

# Lee la URL de la base de datos desde la variable de entorno
# Usa una de respaldo solo si estás en local
SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL') or 'mysql+pymysql://usuario:clave@host/dbname'

# Clave secreta de Flask
SECRET_KEY = os.getenv("SECRET_KEY", "esto-es-un-secreto")

# Carpeta donde se guardan los PDFs subidos
UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", "./uploads")

# Extensiones de archivos válidas
ALLOWED_EXTENSIONS = {'pdf'}
