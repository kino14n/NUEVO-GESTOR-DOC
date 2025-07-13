from flask import Flask
from flask_cors import CORS
from config import Config
from models import db

app = Flask(__name__)
app.config.from_object(Config)
CORS(app, resources={r"/api/*": {"origins": "https://kino14n.github.io"}})

db.init_app(app)

from routes.documentos import documentos_bp
from routes.codes import codes_bp
from routes.exportar import exportar_bp
from routes.usuarios import usuarios_bp

app.register_blueprint(documentos_bp)
app.register_blueprint(codes_bp)
app.register_blueprint(exportar_bp)
app.register_blueprint(usuarios_bp)

@app.route("/api/ping")
def ping():
    return {"pong": True, "msg": "Backend Flask activo y funcionando"}

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
