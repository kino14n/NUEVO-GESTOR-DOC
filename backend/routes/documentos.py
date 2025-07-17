# backend/routes/documentos.py (versión corregida con S3)
from flask import Blueprint, request, jsonify, redirect
from models import db, Document
import os
from datetime import datetime
import boto3
from botocore.exceptions import NoCredentialsError

documentos_bp = Blueprint("documentos", __name__)

# --- Configuración de S3 (Cellar) ---
CELLAR_BUCKET = os.getenv('CELLAR_ADDON_BUCKET')
CELLAR_HOST = os.getenv('CELLAR_ADDON_HOST')
CELLAR_KEY_ID = os.getenv('CELLAR_ADDON_KEY_ID')
CELLAR_KEY_SECRET = os.getenv('CELLAR_ADDON_KEY_SECRET')

s3_client = boto3.client(
    's3',
    endpoint_url=f'https://{CELLAR_HOST}',
    aws_access_key_id=CELLAR_KEY_ID,
    aws_secret_access_key=CELLAR_KEY_SECRET
)

@documentos_bp.route("/api/docs", methods=["GET"])
def listar_documentos():
    docs = Document.query.order_by(Document.date.desc()).all()
    result = [
        {
            "id": doc.id,
            "name": doc.name,
            "date": doc.date.strftime("%Y-%m-%d"),
            "path": doc.path, # El path ahora es el nombre del archivo en S3
            "codigos_extraidos": doc.codigos_extraidos,
        } for doc in docs
    ]
    return jsonify({"ok": True, "docs": result})

@documentos_bp.route("/api/upload", methods=["POST"])
def subir_documento():
    file = request.files.get("file")
    name = request.form.get("name", "")
    codigos = request.form.get("codigos", "")

    if not file or not name:
        return jsonify({"ok": False, "error": "Nombre y archivo son requeridos"}), 400

    filename = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{file.filename}"

    try:
        # Subir archivo a S3
        s3_client.upload_fileobj(
            file,
            CELLAR_BUCKET,
            filename,
            ExtraArgs={'ACL': 'public-read'} # Para que el archivo sea públicamente accesible
        )
        
        # Guardar en la base de datos
        doc = Document(name=name, path=filename, codigos_extraidos=codigos)
        db.session.add(doc)
        db.session.commit()

        return jsonify({"ok": True, "msg": "Documento subido a Cellar S3"})

    except NoCredentialsError:
        return jsonify({"ok": False, "error": "Credenciales de S3 no encontradas"}), 500
    except Exception as e:
        db.session.rollback()
        return jsonify({"ok": False, "error": str(e)}), 500


@documentos_bp.route("/static/uploads/<path:filename>")
def download_pdf(filename):
    # Redirige a la URL pública del archivo en S3
    file_url = f"https://{CELLAR_BUCKET}.{CELLAR_HOST}/{filename}"
    return redirect(file_url)

@documentos_bp.route("/api/delete", methods=["POST"])
def eliminar_documento():
    doc_id = request.json.get("id")
    doc = Document.query.get(doc_id)

    if not doc:
        return jsonify({"ok": False, "msg": "Documento no encontrado"}), 404

    try:
        # Eliminar de S3
        s3_client.delete_object(Bucket=CELLAR_BUCKET, Key=doc.path)

        # Eliminar de la base de datos
        db.session.delete(doc)
        db.session.commit()
        return jsonify({"ok": True, "msg": "Documento eliminado de S3 y DB"})

    except Exception as e:
        db.session.rollback()
        return jsonify({"ok": False, "error": str(e)}), 500

# Las demás rutas (edit, search) no necesitan cambios drásticos
# Asegúrate de que la ruta de edición no intente modificar el archivo físico
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