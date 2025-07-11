
from flask import Flask
from config import SQLALCHEMY_DATABASE_URI, SECRET_KEY, UPLOAD_FOLDER, ALLOWED_EXTENSIONS
from models import db
from routes.documentos import bp as documentos_bp
from routes.codes import bp as codes_bp
from flask_cors import CORS
import os

app = Flask(__name__)
app.secret_key = SECRET_KEY
app.config['SQLALCHEMY_DATABASE_URI'] = SQLALCHEMY_DATABASE_URI
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['ALLOWED_EXTENSIONS'] = ALLOWED_EXTENSIONS

CORS(app)

db.init_app(app)

app.register_blueprint(documentos_bp, url_prefix='/api/documentos')
app.register_blueprint(codes_bp, url_prefix='/api/codes')

if __name__ == '__main__':
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    with app.app_context():
        db.create_all()
    app.run(debug=True)
