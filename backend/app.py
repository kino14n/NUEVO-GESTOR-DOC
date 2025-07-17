import os
from flask import Flask
from flask_cors import CORS
from models import db

# --- Importar Blueprints (las rutas modulares que creaste) ---
from routes.documentos import documentos_bp
from routes.codes import codes_bp
from routes.exportar import exportar_bp
from routes.usuarios import usuarios_bp

def create_app():
    """
    Función de fábrica para crear y configurar la aplicación Flask.
    """
    app = Flask(__name__)
    CORS(app) # Habilita CORS para todas las rutas

    # --- Cargar la configuración de la base de datos ---
    # Utiliza las variables de entorno de Clever Cloud
    db_user = os.getenv('MYSQL_ADDON_USER')
    db_password = os.getenv('MYSQL_ADDON_PASSWORD')
    db_host = os.getenv('MYSQL_ADDON_HOST')
    db_port = os.getenv('MYSQL_ADDON_PORT')
    db_name = os.getenv('MYSQL_ADDON_DB')

    # Valida que todas las variables de entorno existan
    if not all([db_user, db_password, db_host, db_port, db_name]):
        raise ValueError("Faltan variables de entorno para la conexión a la base de datos.")

    # Construye la URL de conexión
    app.config['SQLALCHEMY_DATABASE_URI'] = (
        f"mysql+pymysql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}?charset=utf8mb4"
    )
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # --- Configuración de la carpeta de subida ---
    # Se asegura de que la carpeta esté dentro de la estructura del backend para el despliegue
    upload_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'uploads')
    app.config['UPLOAD_FOLDER'] = upload_folder
    os.makedirs(upload_folder, exist_ok=True)
    
    # --- Inicializar la BD con la app y registrar los Blueprints ---
    db.init_app(app)

    app.register_blueprint(documentos_bp)
    app.register_blueprint(codes_bp)
    app.register_blueprint(exportar_bp)
    app.register_blueprint(usuarios_bp)

    @app.route('/')
    def home():
        return "Backend modular del Gestor Documental funcionando correctamente."

    return app

# --- NO CAMBIES ESTO ---
# Gunicorn, Render y otros servidores WSGI buscarán este objeto "app".
app = create_app()

if __name__ == '__main__':
    # El puerto 5000 es estándar para desarrollo local con Flask
    app.run(debug=True, port=5000)