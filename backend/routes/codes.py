from flask import Blueprint, request, jsonify
from models import Document

codes_bp = Blueprint("codes", __name__)

@codes_bp.route("/api/suggest", methods=["GET"])
def autocompletado():
    pref = request.args.get("q", "").upper()
    codes = Document.query.filter(Document.codigos_extraidos.ilike(f"{pref}%")).all()
    sugerencias = []
    for doc in codes:
        for code in (doc.codigos_extraidos or "").split(","):
            code = code.strip().upper()
            if code.startswith(pref) and code not in sugerencias:
                sugerencias.append(code)
    return jsonify({"ok": True, "codes": sugerencias})
