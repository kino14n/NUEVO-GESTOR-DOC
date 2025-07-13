from flask import Blueprint, request, jsonify

usuarios_bp = Blueprint("usuarios", __name__)

ADMIN_USER = "admin"
ADMIN_PASS = "clave123"

@usuarios_bp.route("/api/login", methods=["POST"])
def login():
    data = request.json
    if data.get("user") == ADMIN_USER and data.get("pass") == ADMIN_PASS:
        return jsonify({"ok": True, "msg": "Login exitoso"})
    return jsonify({"ok": False, "msg": "Credenciales incorrectas"}), 401
