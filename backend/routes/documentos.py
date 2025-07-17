from flask import Blueprint, request, jsonify, redirect
from models import db, Document
import os
from datetime import datetime
import boto3
from botocore.exceptions import NoCredentialsError, ClientError # Importar ClientError
from werkzeug.utils import secure_filename

documentos_bp = Blueprint("documentos", __name__)

# --- Función para obtener el cliente S3 (ahora reutilizable) ---
def get_s3_client():
    CELLAR_BUCKET = os.getenv('CELLAR_ADDON_BUCKET')
    CELLAR_HOST = os.getenv('CELLAR_ADDON_HOST')
    CELLAR_KEY_ID = os.getenv('CELLAR_ADDON_KEY_ID')
    CELLAR_KEY_SECRET = os.getenv('CELLAR_ADDON_KEY_SECRET')

    if not all([CELLAR_BUCKET, CELLAR_HOST, CELLAR_KEY_ID, CELLAR_KEY_SECRET]):
        print("WARNING: Missing one or more Cellar S3 environment variables. S3 operations will not work.")
        return None

    try:
        s3_client = boto3.client(
            's3',
            endpoint_url=f'https://{CELLAR_HOST}',
            aws_access_key_id=CELLAR_KEY_ID,
            aws_secret_access_key=CELLAR_KEY_SECRET
        )
        # Opcional: una pequeña prueba para verificar la conexión, útil en desarrollo
        # s3_client.list_buckets()
        return s3_client
    except Exception as e:
        print(f"ERROR: Could not initialize S3 client (Cellar): {e}")
        return None

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


@documentos_bp.route("/api/presigned_url", methods=["POST"])
def get_presigned_url():
    s3_client = get_s3_client()
    if not s3_client:
        return jsonify({"ok": False, "error": "El servicio de almacenamiento (S3) no está configurado correctamente."}), 500

    data = request.json
    file_name = data.get("file_name") # Nombre original del archivo del frontend
    file_type = data.get("file_type") # Tipo MIME del archivo (ej: application/pdf)

    if not file_name or not file_type:
        return jsonify({"ok": False, "error": "file_name y file_type son requeridos."}), 400

    # Generar un nombre de archivo único para S3 para evitar colisiones
    # No usamos secure_filename aquí porque el frontend enviará el nombre original.
    # Lo importante es el Key en S3.
    filename_on_s3 = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{file_name}"
    CELLAR_BUCKET = os.getenv('CELLAR_ADDON_BUCKET') # Necesario para la URL

    if not CELLAR_BUCKET:
        return jsonify({"ok": False, "error": "Nombre del bucket S3 no configurado."}), 500

    try:
        # Generar la URL pre-firmada para la operación PUT Object
        presigned_post = s3_client.generate_presigned_post(
            Bucket=CELLAR_BUCKET,
            Key=filename_on_s3,
            Fields={"Content-Type": file_type, "acl": "public-read"}, # Asegura el Content-Type
            Conditions=[
                {"Content-Type": file_type},
                {"acl": "public-read"},
                ["content-length-range", 1, 104857600] # Limite de 1 a 100MB (100 * 1024 * 1024)
            ],
            ExpiresIn=3600 # La URL será válida por 1 hora (en segundos)
        )
        
        # Guardamos el nombre temporal en S3 para asociarlo después con los metadatos de BD
        # No guardar en BD aún, solo preparar.
        return jsonify({"ok": True, "presigned_post": presigned_post, "s3_key": filename_on_s3})

    except ClientError as e:
        print(f"Error al generar URL pre-firmada: {e}")
        return jsonify({"ok": False, "error": f"Error del cliente S3: {str(e)}"}), 500
    except Exception as e:
        print(f"Error inesperado al generar URL pre-firmada: {e}")
        return jsonify({"ok": False, "error": f"Error inesperado: {str(e)}"}), 500


@documentos_bp.route("/api/upload", methods=["POST"])
def confirmar_subida_documento():
    # Esta función ahora solo recibe la confirmación del frontend y guarda en BD.
    # El archivo PDF ya fue subido directamente a S3 por el frontend.
    data = request.json
    s3_key = data.get("s3_key") # El nombre/ruta del archivo en S3
    name = data.get("name", "")
    codigos = data.get("codigos", "")

    if not s3_key or not name:
        return jsonify({"ok": False, "error": "s3_key y name son requeridos para confirmar la subida."}), 400

    try:
        # Guardar la información del documento en la base de datos
        doc = Document(name=name, path=s3_key, codigos_extraidos=codigos)
        db.session.add(doc)
        db.session.commit()

        return jsonify({"ok": True, "msg": "Documento registrado en la base de datos."})

    except Exception as e:
        db.session.rollback()
        print(f"Error al registrar documento en BD después de subida S3: {e}")
        return jsonify({"ok": False, "error": f"Error al registrar el documento: {str(e)}"}), 500


@documentos_bp.route("/static/uploads/<path:filename>")
def download_pdf(filename):
    CELLAR_BUCKET = os.getenv('CELLAR_ADDON_BUCKET')
    CELLAR_HOST = os.getenv('CELLAR_ADDON_HOST')
    
    if not CELLAR_BUCKET or not CELLAR_HOST:
        return "El servicio de almacenamiento no está configurado para descargas.", 500

    file_url = f"https://{CELLAR_BUCKET}.{CELLAR_HOST}/{filename}"
    print(f"Redirecting to S3 URL: {file_url}")
    return redirect(file_url)

@documentos_bp.route("/api/delete", methods=["POST"])
def eliminar_documento():
    s3_client = get_s3_client()
    if not s3_client:
        return jsonify({"ok": False, "error": "El servicio de almacenamiento no está configurado."}), 500

    doc_id = request.json.get("id")
    doc = Document.query.get(doc_id)

    if not doc:
        return jsonify({"ok": False, "msg": "Documento no encontrado"}), 404

    try:
        CELLAR_BUCKET = os.getenv('CELLAR_ADDON_BUCKET') # Necesario para la operación
        if not CELLAR_BUCKET:
            return jsonify({"ok": False, "error": "Nombre del bucket S3 no configurado para eliminación."}), 500

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