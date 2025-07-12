from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import os

# Importa configuraciones y componentes
from config import SQLALCHEMY_DATABASE_URI, SECRET_KEY, UPLOAD_FOLDER, ALLOWED_EXTENSIONS
from models import db
from routes.documentos import bp as documentos_bp
from routes.codes import bp as codes_bp

# Inicializa la app
app = Flask(__name__)
app.secret_key = SECRET_KEY

# Configura Flask
app.config['SQLALCHEMY_DATABASE_URI'] = SQLALCHEMY_DATABASE_URI
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['ALLOWED_EXTENSIONS'] = ALLOWED_EXTENSIONS

# Habilita CORS
CORS(app)

# Inicializa la base de datos
db.init_app(app)

# Registra los Blueprints
app.register_blueprint(documentos_bp, url_prefix='/api/documentos')
app.register_blueprint(codes_bp, url_prefix='/api/codes')

# Ruta de prueba de conexión a la base de datos
@app.route('/test-db')
def test_db():
    try:
        db.session.execute("SELECT 1")
        return "✅ Conexión exitosa con MySQL (Clever Cloud)"
    except Exception as e:
        return f"❌ Error de conexión: {str(e)}"

# Ejecutar app local (opcional para desarrollo)
if __name__ == '__main__':
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    with app.app_context():
        db.create_all()
    app.run(debug=True)
