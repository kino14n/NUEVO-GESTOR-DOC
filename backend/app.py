from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from config import Config
import os

db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)

    from routes.documentos import bp as documentos_bp
    from routes.codes import bp as codes_bp
    from routes.exportar import bp as exportar_bp
    from routes.usuarios import bp as usuarios_bp

    app.register_blueprint(documentos_bp)
    app.register_blueprint(codes_bp)
    app.register_blueprint(exportar_bp)
    app.register_blueprint(usuarios_bp)

    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    with app.app_context():
        db.create_all()

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0')
