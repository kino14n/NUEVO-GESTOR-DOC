from flask import Flask, jsonify
from flask_cors import CORS

app = Flask(__name__)

# Permitir solo tu frontend de GitHub Pages
CORS(app, resources={r"/api/*": {"origins": "https://kino14n.github.io"}})

@app.route('/api/search', methods=['GET', 'POST'])
def search():
    return jsonify({"message": "¡Funciona! Endpoint /api/search con CORS habilitado."})

@app.route('/api/docs', methods=['GET', 'POST'])
def docs():
    return jsonify({"message": "¡Funciona! Endpoint /api/docs con CORS habilitado."})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
