from flask import Blueprint, request, jsonify, send_from_directory, current_app
from models import db, Document
import os
from datetime import datetime

documentos_bp = Blueprint("documentos", __name__)

UPLOAD_FOLDER = os.path.join(os.getcwd(), 'backend', 'static', 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@documentos_bp.route("/api/docs", methods=["GET"])
def listar_documentos():
    docs = Document.query.order_by(Document.date.desc()).all()
    result = [
        {
            "id": doc.id,
            "name": doc.name,
            "date": doc.date.strftime("%Y-%m-%d"),
            "path": doc.path,
            "codigos_extraidos": doc.codigos_extraidos,
        } for doc in docs
    ]
    return jsonify({"ok": True, "docs": result})

@documentos_bp.route("/api/search", methods=["POST"])
def busqueda_inteligente():
    q = request.json.get("query", "").lower()
    docs = Document.query.filter(
        (Document.name.ilike(f"%{q}%")) |
        (Document.codigos_extraidos.ilike(f"%{q}%"))
    ).order_by(Document.date.desc()).all()
    result = [
        {
            "id": doc.id,
            "name": doc.name,
            "date": doc.date.strftime("%Y-%m-%d"),
            "path": doc.path,
            "codigos_extraidos": doc.codigos_extraidos,
        } for doc in docs
    ]
    return jsonify({"ok": True, "resultados": result})

@documentos_bp.route("/api/upload", methods=["POST"])
def subir_documento():
    file = request.files.get("file")
    name = request.form.get("name", "")
    codigos = request.form.get("codigos", "")
    if not file or file.filename == "":
        return jsonify({"ok": False, "error": "Archivo no enviado"}), 400
    filename = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{file.filename}"
    ruta = os.path.join(UPLOAD_FOLDER, filename)
    file.save(ruta)
    doc = Document(
        name=name,
        date=datetime.now().date(),
        path=filename,
        codigos_extraidos=codigos
    )
    db.session.add(doc)
    db.session.commit()
    return jsonify({"ok": True, "msg": "Documento subido", "filename": filename})

@documentos_bp.route("/static/uploads/<path:filename>")
def download_pdf(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

@documentos_bp.route("/api/delete", methods=["POST"])
def eliminar_documento():
    id_ = request.json.get("id")
    doc = Document.query.get(id_)
    if not doc:
        return jsonify({"ok": False, "msg": "No existe ese documento"}), 404
    # Borra el archivo físico si existe
    archivo_path = os.path.join(UPLOAD_FOLDER, doc.path)
    if os.path.exists(archivo_path):
        os.remove(archivo_path)
    db.session.delete(doc)
    db.session.commit()
    return jsonify({"ok": True, "msg": "Documento eliminado"})

@documentos_bp.route("/api/edit", methods=["POST"])
def editar_documento():
    id_ = request.json.get("id")
    name = request.json.get("name")
    codigos = request.json.get("codigos")
    doc = Document.query.get(id_)
    if not doc:
        return jsonify({"ok": False, "msg": "Documento no encontrado"}), 404
    if name: doc.name = name
    if codigos: doc.codigos_extraidos = codigos
    db.session.commit()
    return jsonify({"ok": True, "msg": "Documento actualizado"})
