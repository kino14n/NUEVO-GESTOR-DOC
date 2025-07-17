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

    # --- Configuración de CORS explícita para producción ---
    # Permite peticiones únicamente desde tu dominio de GitHub Pages.
    # Esta línea resuelve el error de CORS.
    # Asegúrate de que "https://kino14n.github.io" sea EXACTAMENTE el dominio de tu frontend.
    CORS(app, resources={r"/api/*": {"origins": "https://kino14n.github.io"}})
        
    # --- Cargar la configuración de la base de datos desde variables de entorno ---
    db_user = os.getenv('MYSQL_ADDON_USER')
    db_password = os.getenv('MYSQL_ADDON_PASSWORD')
    db_host = os.getenv('MYSQL_ADDON_HOST')
    db_port = os.getenv('MYSQL_ADDON_PORT')
    db_name = os.getenv('MYSQL_ADDON_DB')

    if not all([db_user, db_password, db_host, db_port, db_name]):
        # Esto lanzará un error si las variables de entorno de la BD no están configuradas en Clever Cloud.
        raise ValueError("Faltan variables de entorno para la conexión a la base de datos.")

    app.config['SQLALCHEMY_DATABASE_URI'] = (
        f"mysql+pymysql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}?charset=utf8mb4"
    )
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False # Recomendado para Flask-SQLAlchemy

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
    # Esto es solo para ejecución local, en Clever Cloud Gunicorn manejará el puerto.
    app.run(debug=True, port=5000)