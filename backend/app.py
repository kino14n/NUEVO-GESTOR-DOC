from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "https://kino14n.github.io"}})

@app.route('/api/search', methods=['POST'])
def search():
    data = request.get_json(silent=True)
    return jsonify({
        "ok": True,
        "input": data,
        "message": "Búsqueda recibida correctamente (ejemplo desde Flask backend)"
    })

@app.route('/api/docs', methods=['GET'])
def docs():
    return jsonify({
        "docs": [
            {"id": 1, "title": "Documento 1"},
            {"id": 2, "title": "Documento 2"}
        ],
        "message": "Docs listos (ejemplo desde Flask backend)"
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
