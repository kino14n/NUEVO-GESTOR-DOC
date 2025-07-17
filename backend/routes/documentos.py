from flask import Blueprint, request, jsonify, redirect
from models import db, Document
import os
from datetime import datetime
import boto3
from botocore.exceptions import NoCredentialsError # Asegúrate de que está importado
from werkzeug.utils import secure_filename

documentos_bp = Blueprint("documentos", __name__)

# --- ELIMINA TODO ESTE BLOQUE DE INICIALIZACIÓN GLOBAL ---
# CELLAR_BUCKET = os.getenv('CELLAR_ADDON_BUCKET')
# CELLAR_HOST = os.getenv('CELLAR_ADDON_HOST')
# CELLAR_KEY_ID = os.getenv('CELLAR_ADDON_KEY_ID')
# CELLAR_KEY_SECRET = os.getenv('CELLAR_ADDON_KEY_SECRET')

# s3_client = None
# if all([CELLAR_BUCKET, CELLAR_HOST, CELLAR_KEY_ID, CELLAR_KEY_SECRET]):
#     try:
#         s3_client = boto3.client(
#             's3',
#             endpoint_url=f'https://{CELLAR_HOST}',
#             aws_access_key_id=CELLAR_KEY_ID,
#             aws_secret_access_key=CELLAR_KEY_SECRET
#         )
#         print("S3 client (Cellar) initialized successfully.")
#     except Exception as e:
#         print(f"ERROR: Could not initialize S3 client (Cellar): {e}")
#         s3_client = None
# else:
#     print("WARNING: Missing one or more Cellar S3 environment variables. S3 operations will not work.")
# --- FIN DEL BLOQUE A ELIMINAR ---

@documentos_bp.route("/api/docs", methods=["GET"])
def listar_documentos():
    # ... (esta función no necesita cambios) ...
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

@documentos_bp.route("/api/upload", methods=["POST"])
def subir_documento():
    # --- MOVER LA INICIALIZACIÓN DEL CLIENTE S3 AQUÍ ---
    # Obtener las variables de entorno dentro de la función para asegurar su frescura
    CELLAR_BUCKET = os.getenv('CELLAR_ADDON_BUCKET')
    CELLAR_HOST = os.getenv('CELLAR_ADDON_HOST')
    CELLAR_KEY_ID = os.getenv('CELLAR_ADDON_KEY_ID')
    CELLAR_KEY_SECRET = os.getenv('CELLAR_ADDON_KEY_SECRET')

    s3_client = None
    if all([CELLAR_BUCKET, CELLAR_HOST, CELLAR_KEY_ID, CELLAR_KEY_SECRET]):
        try:
            s3_client = boto3.client(
                's3',
                endpoint_url=f'https://{CELLAR_HOST}',
                aws_access_key_id=CELLAR_KEY_ID,
                aws_secret_access_key=CELLAR_KEY_SECRET
            )
            # Puedes dejar este print para verificar en los logs si se inicializa aquí
            print("S3 client (Cellar) initialized successfully INSIDE UPLOAD function.")
        except Exception as e:
            # Si hay un error al inicializar aquí, imprímelo y s3_client seguirá siendo None
            print(f"ERROR: Could not initialize S3 client (Cellar) inside upload function: {e}")
            s3_client = None
    else:
        # Si faltan variables de entorno, también se registra aquí
        print("WARNING: Missing one or more Cellar S3 environment variables INSIDE UPLOAD function. S3 operations will not work.")
    # --- FIN DE LA INICIALIZACIÓN MOVILIZADA ---

    # Verifica si el cliente S3 se inicializó correctamente (este bloque se mantiene)
    if not s3_client:
        print("Error: S3 client is not available for upload.")
        return jsonify({"ok": False, "error": "El servicio de almacenamiento (S3) no está configurado correctamente."}), 500

    file = request.files.get("file")
    name = request.form.get("name", "")
    codigos = request.form.get("codigos", "")

    if not file or not name or file.filename == '':
        return jsonify({"ok": False, "error": "Nombre, archivo y un nombre de archivo válido son requeridos"}), 400

    original_filename = secure_filename(file.filename)
    filename_on_s3 = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{original_filename}"

    try:
        file.seek(0) # ¡MANTENER ESTA LÍNEA! Es crucial para el MissingContentLength inicial.

        s3_client.upload_fileobj(
            file,
            CELLAR_BUCKET, # Esta variable ahora se obtiene dentro de la función
            filename_on_s3,
            ExtraArgs={'ACL': 'public-read'}
        )

        doc = Document(name=name, path=filename_on_s3, codigos_extraidos=codigos)
        db.session.add(doc)
        db.session.commit()

        return jsonify({"ok": True, "msg": "Documento subido a almacenamiento persistente"})

    except Exception as e:
        db.session.rollback()
        print(f"Error al subir el archivo a S3 o guardar en BD: {e}")
        return jsonify({"ok": False, "error": f"Error al subir el documento: {str(e)}"}), 500

@documentos_bp.route("/static/uploads/<path:filename>")
def download_pdf(filename):
    # También necesitará la variable CELLAR_BUCKET y CELLAR_HOST aquí
    CELLAR_BUCKET = os.getenv('CELLAR_ADDON_BUCKET')
    CELLAR_HOST = os.getenv('CELLAR_ADDON_HOST')
    # No es estrictamente necesario el s3_client para el redirect, pero sí las variables
    if not CELLAR_BUCKET or not CELLAR_HOST:
        return "El servicio de almacenamiento no está configurado para descargas.", 500

    file_url = f"https://{CELLAR_BUCKET}.{CELLAR_HOST}/{filename}"
    print(f"Redirecting to S3 URL: {file_url}")
    return redirect(file_url)

@documentos_bp.route("/api/delete", methods=["POST"])
def eliminar_documento():
    # También necesitará la inicialización del s3_client aquí
    CELLAR_BUCKET = os.getenv('CELLAR_ADDON_BUCKET')
    CELLAR_HOST = os.getenv('CELLAR_ADDON_HOST')
    CELLAR_KEY_ID = os.getenv('CELLAR_ADDON_KEY_ID')
    CELLAR_KEY_SECRET = os.getenv('CELLAR_ADDON_KEY_SECRET')

    s3_client = None
    if all([CELLAR_BUCKET, CELLAR_HOST, CELLAR_KEY_ID, CELLAR_KEY_SECRET]):
        try:
            s3_client = boto3.client(
                's3', endpoint_url=f'https://{CELLAR_HOST}',
                aws_access_key_id=CELLAR_KEY_ID, aws_secret_access_key=CELLAR_KEY_SECRET
            )
        except Exception as e:
            print(f"ERROR: Could not initialize S3 client for delete: {e}")
            s3_client = None

    if not s3_client:
        return jsonify({"ok": False, "error": "El servicio de almacenamiento no está configurado."}), 500

    doc_id = request.json.get("id")
    doc = Document.query.get(doc_id)

    if not doc:
        return jsonify({"ok": False, "msg": "Documento no encontrado"}), 404

    try:
        s3_client.delete_object(Bucket=CELLAR_BUCKET, Key=doc.path)
        db.session.delete(doc)
        db.session.commit()
        return jsonify({"ok": True, "msg": "Documento eliminado"})

    except Exception as e:
        db.session.rollback()
        print(f"Error al eliminar documento de S3 o BD: {e}")
        return jsonify({"ok": False, "error": f"Error al eliminar el documento: {str(e)}"}), 500


@documentos_bp.route("/api/edit", methods=["POST"])
def editar_documento():
    # ... (esta función no necesita cambios, ya que no interactúa con S3) ...
    id_ = request.json.get("id")
    name = request.json.get("name")
    codigos = request.json.get("codigos")
    doc = Document.query.get(id_)
    if not doc:
        return jsonify({"ok": False, "msg": "Documento no encontrado"}), 404

    if name is not None: doc.name = name
    if codigos is not None: doc.codigos_extraidos = codigos

    try:
        db.session.commit()
        return jsonify({"ok": True, "msg": "Documento actualizado"})
    except Exception as e:
        db.session.rollback()
        print(f"Error al editar documento: {e}")
        return jsonify({"ok": False, "error": f"Error al actualizar el documento: {str(e)}"}), 500

@documentos_bp.route("/api/search", methods=["POST"])
def busqueda_inteligente():
    # ... (esta función no necesita cambios, ya que no interactúa con S3) ...
    q = request.json.get("query", "").strip().lower()

    if not q:
        return jsonify({"ok": True, "resultados": []})

    docs = Document.query.filter(
        (Document.name.ilike(f"%{q}%")) |
        (Document.codigos_extraidos.ilike(f"%{q}%")) |
        (Document.path.ilike(f"%{q}%"))
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

    print(f"Búsqueda inteligente para '{q}' encontró {len(result)} resultados.")
    return jsonify({"ok": True, "resultados": result})