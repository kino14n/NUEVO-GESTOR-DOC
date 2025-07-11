
from flask import Blueprint, jsonify, send_file, request
from models import db, Documento
import csv
import io
import zipfile
import os

bp = Blueprint('exportar', __name__)

@bp.route('/export_csv', methods=['GET'])
def export_csv():
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['ID', 'Codigo', 'Nombre', 'Descripcion', 'Fecha', 'Ruta PDF'])
    documentos = Documento.query.all()
    for d in documentos:
        writer.writerow([d.id, d.codigo, d.nombre, d.descripcion, d.fecha.strftime('%Y-%m-%d') if d.fecha else '', d.ruta_pdf])
    output.seek(0)
    return send_file(io.BytesIO(output.getvalue().encode()), mimetype='text/csv', as_attachment=True, download_name='documentos.csv')

@bp.route('/export_zip', methods=['POST'])
def export_zip():
    ids = request.json.get('ids', [])
    docs = Documento.query.filter(Documento.id.in_(ids)).all()
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w') as zipf:
        for doc in docs:
            if doc.ruta_pdf and os.path.isfile(doc.ruta_pdf):
                zipf.write(doc.ruta_pdf, os.path.basename(doc.ruta_pdf))
    zip_buffer.seek(0)
    return send_file(zip_buffer, mimetype='application/zip', as_attachment=True, download_name='documentos.zip')
