from flask import Blueprint, send_file, jsonify, request
from models import Document
import pandas as pd
import io
import zipfile
import os

exportar_bp = Blueprint("exportar", __name__)
UPLOAD_FOLDER = os.path.join(os.getcwd(), 'backend', 'static', 'uploads')

@exportar_bp.route("/api/export_csv", methods=["GET"])
def export_csv():
    docs = Document.query.all()
    data = [{
        "id": doc.id,
        "name": doc.name,
        "date": doc.date.strftime("%Y-%m-%d"),
        "path": doc.path,
        "codigos_extraidos": doc.codigos_extraidos,
    } for doc in docs]
    df = pd.DataFrame(data)
    csv_io = io.StringIO()
    df.to_csv(csv_io, index=False)
    csv_io.seek(0)
    return send_file(io.BytesIO(csv_io.read().encode()), mimetype="text/csv", as_attachment=True, download_name="documentos.csv")

@exportar_bp.route("/api/export_zip", methods=["POST"])
def export_zip():
    archivos = request.json.get("archivos", [])  # Nombres de archivos PDF
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w") as zipf:
        for archivo in archivos:
            pdf_path = os.path.join(UPLOAD_FOLDER, archivo)
            if os.path.exists(pdf_path):
                zipf.write(pdf_path, arcname=archivo)
    zip_buffer.seek(0)
    return send_file(zip_buffer, mimetype="application/zip", as_attachment=True, download_name="documentos.zip")
