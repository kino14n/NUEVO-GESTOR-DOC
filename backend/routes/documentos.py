from flask import Blueprint, request, jsonify, redirect
from models import db, Document
import os
from datetime import datetime
import boto3
from botocore.exceptions import NoCredentialsError # 
from werkzeug.utils import secure_filename # Importado para seguridad al subir archivos

documentos_bp = Blueprint("documentos", __name__)

# --- Configuración de S3 (Cellar) desde variables de entorno ---
# Asegúrate de que 'CELLAR_ADDON_BUCKET' esté configurado en Clever Cloud.
CELLAR_BUCKET = os.getenv('CELLAR_ADDON_BUCKET') # 
CELLAR_HOST = os.getenv('CELLAR_ADDON_HOST') # 
CELLAR_KEY_ID = os.getenv('CELLAR_ADDON_KEY_ID') # 
CELLAR_KEY_SECRET = os.getenv('CELLAR_ADDON_KEY_SECRET') # 

s3_client = None # Inicializamos a None por defecto
if all([CELLAR_BUCKET, CELLAR_HOST, CELLAR_KEY_ID, CELLAR_KEY_SECRET]):
    try:
        s3_client = boto3.client(
            's3',
            endpoint_url=f'https://{CELLAR_HOST}', # 
            aws_access_key_id=CELLAR_KEY_ID, # 
            aws_secret_access_key=CELLAR_KEY_SECRET # 
        )
        # Opcional: una pequeña prueba para verificar la conexión, útil en desarrollo
        # s3_client.list_buckets() 
        print("S3 client (Cellar) initialized successfully.")
    except Exception as e:
        print(f"ERROR: Could not initialize S3 client (Cellar): {e}") # 
        s3_client = None # Si falla, s3_client permanece en None
else:
    print("WARNING: Missing one or more Cellar S3 environment variables. S3 operations will not work.")

@documentos_bp.route("/api/docs", methods=["GET"])
def listar_documentos():
    docs = Document.query.order_by(Document.date.desc()).all()
    result = [
        {
            "id": doc.id,
            "name": doc.name,
            "date": doc.date.strftime("%Y-%m-%d"),
            "path": doc.path, # 'path' ahora almacena el nombre del archivo en S3
            "codigos_extraidos": doc.codigos_extraidos,
        } for doc in docs
    ]
    return jsonify({"ok": True, "docs": result})

@documentos_bp.route("/api/upload", methods=["POST"])
def subir_documento():
    # Verifica si el cliente S3 se inicializó correctamente
    if not s3_client:
        print("Error: S3 client is not available for upload.")
        return jsonify({"ok": False, "error": "El servicio de almacenamiento (S3) no está configurado correctamente."}), 500

    file = request.files.get("file")
    name = request.form.get("name", "")
    codigos = request.form.get("codigos", "")

    if not file or not name or file.filename == '':
        return jsonify({"ok": False, "error": "Nombre, archivo y un nombre de archivo válido son requeridos"}), 400

    # Generar un nombre de archivo único para S3 para evitar colisiones
    original_filename = secure_filename(file.filename)
    filename_on_s3 = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{original_filename}"

    try:
        # **************************************************************************
        # SOLUCIÓN PARA 'MissingContentLength': Rebobinar el puntero del archivo.
        # Esto es crucial antes de pasar el objeto 'file' a upload_fileobj. 
        file.seek(0)
        # **************************************************************************
        
        s3_client.upload_fileobj(
            file,
            CELLAR_BUCKET,
            filename_on_s3, # Usamos el nombre de archivo único para S3
            ExtraArgs={'ACL': 'public-read'} # 'public-read' si quieres que sean accesibles directamente por URL
        )
        
        # Guardar la información del documento en la base de datos
        doc = Document(name=name, path=filename_on_s3, codigos_extraidos=codigos)
        db.session.add(doc)
        db.session.commit()

        return jsonify({"ok": True, "msg": "Documento subido a almacenamiento persistente"})

    except Exception as e:
        db.session.rollback() # Si algo falla con S3, la transacción de BD se revierte
        print(f"Error al subir el archivo a S3 o guardar en BD: {e}")
        return jsonify({"ok": False, "error": f"Error al subir el documento: {str(e)}"}), 500

@documentos_bp.route("/static/uploads/<path:filename>")
def download_pdf(filename):
    if not s3_client:
        return "El servicio de almacenamiento no está configurado.", 500
        
    # Construir la URL pública del archivo en Cellar S3
    # Nota: Asegúrate de que tu bucket permite acceso público si usas 'public-read' en la subida
    # La URL de un objeto S3 compatible es típicamente: https://BUCKET_NAME.HOST/KEY
    file_url = f"https://{CELLAR_BUCKET}.{CELLAR_HOST}/{filename}"
    print(f"Redirecting to S3 URL: {file_url}") # Para depuración
    return redirect(file_url)

@documentos_bp.route("/api/delete", methods=["POST"])
def eliminar_documento():
    if not s3_client:
        return jsonify({"ok": False, "error": "El servicio de almacenamiento no está configurado."}), 500

    doc_id = request.json.get("id")
    doc = Document.query.get(doc_id)

    if not doc:
        return jsonify({"ok": False, "msg": "Documento no encontrado"}), 404

    try:
        # Eliminar el objeto de S3
        s3_client.delete_object(Bucket=CELLAR_BUCKET, Key=doc.path)
        
        # Eliminar el registro de la base de datos
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
    
    # Solo actualiza si los valores no son None (es decir, si se enviaron en el request)
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
    q = request.json.get("query", "").strip().lower() # Limpia y convierte a minúsculas
    
    if not q: # Si la query está vacía, no hay nada que buscar.
        return jsonify({"ok": True, "resultados": []})

    # La búsqueda inteligente usa LIKE con comodines '%' en ambos lados
    # para encontrar coincidencias parciales en múltiples campos.
    # Esto es lo que esperabas para la "búsqueda inteligente".
    docs = Document.query.filter(
        (Document.name.ilike(f"%{q}%")) | # Busca 'q' en el nombre
        (Document.codigos_extraidos.ilike(f"%{q}%")) | # Busca 'q' en códigos extraídos
        (Document.path.ilike(f"%{q}%")) # Opcional: buscar también en la ruta/nombre de archivo en S3
    ).order_by(Document.date.desc()).all() # Ordena por fecha descendente (más recientes primero)
    
    result = [
        {
            "id": doc.id,
            "name": doc.name,
            "date": doc.date.strftime("%Y-%m-%d"),
            "path": doc.path,
            "codigos_extraidos": doc.codigos_extraidos,
        } for doc in docs
    ]
    
    print(f"Búsqueda inteligente para '{q}' encontró {len(result)} resultados.") # Para depuración
    return jsonify({"ok": True, "resultados": result})