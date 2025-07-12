from flask import Blueprint, request, jsonify, current_app, send_file, redirect, url_for
from werkzeug.utils import secure_filename
import os
import csv
import zipfile
from io import BytesIO, StringIO
from datetime import datetime
from models import Document, db

bp = Blueprint('documentos', __name__, url_prefix='/api')

ALLOWED_EXTENSIONS = {'pdf'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@bp.route('/upload', methods=['POST'])
def upload():
    nombre = request.form.get('nombre')
    fecha_str = request.form.get('fecha')
    codigos = request.form.get('codigos')
    file = request.files.get('archivo')

    if not nombre or not fecha_str or not file:
        return jsonify({'error': 'Faltan datos obligatorios'}), 400

    if not allowed_file(file.filename):
        return jsonify({'error': 'Archivo no permitido'}), 400

    filename = secure_filename(file.filename)
    upload_folder = current_app.config['UPLOAD_FOLDER']
    os.makedirs(upload_folder, exist_ok=True)
    filepath = os.path.join(upload_folder, filename)
    file.save(filepath)

    try:
        fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date()
    except Exception:
        return jsonify({'error': 'Formato de fecha inválido'}), 400

    doc = Document(
        name=nombre,
        date=fecha,
        path=filename,
        codigos_extraidos=codigos
    )
    db.session.add(doc)
    db.session.commit()

    return jsonify({'success': True, 'id': doc.id})

@bp.route('/search', methods=['POST'])
def search():
    data = request.get_json()
    code = data.get('code', '')

    resultados = Document.query.filter(
        (Document.name.ilike(f'%{code}%')) |
        (Document.codigos_extraidos.ilike(f'%{code}%'))
    ).all()

    res = {doc.name: {'date': doc.date.strftime('%Y-%m-%d'), 'path': doc.path, 'codigos_extraidos': doc.codigos_extraidos} for doc in resultados}
    return jsonify(res)

@bp.route('/docs', methods=['GET'])
def docs_list():
    search = request.args.get('search', '')
    query = Document.query
    if search:
        like = f"%{search}%"
        query = query.filter(
            (Document.name.ilike(like)) | (Document.codigos_extraidos.ilike(like))
        )
    docs = query.order_by(Document.date.desc()).all()

    out = []
    for d in docs:
        out.append({
            'id': d.id,
            'name': d.name,
            'date': d.date.strftime('%Y-%m-%d'),
            'path': d.path,
            'codigos_extraidos': d.codigos_extraidos
        })
    return jsonify(out)

@bp.route('/docs/<int:id>', methods=['DELETE'])
def delete_doc(id):
    doc = Document.query.get(id)
    if not doc:
        return jsonify({'error': 'Documento no encontrado'}), 404

    try:
        os.remove(os.path.join(current_app.config['UPLOAD_FOLDER'], doc.path))
    except Exception as e:
        current_app.logger.error(f"Error al eliminar archivo: {e}")

    db.session.delete(doc)
    db.session.commit()
    return jsonify({'success': True})

@bp.route('/docs/<int:id>', methods=['PUT'])
def edit_doc(id):
    doc = Document.query.get(id)
    if not doc:
        return jsonify({'error': 'Documento no encontrado'}), 404

    data = request.get_json()
    nombre = data.get('nombre')
    fecha_str = data.get('fecha')
    codigos = data.get('codigos')

    if nombre:
        doc.name = nombre
    if fecha_str:
        try:
            doc.date = datetime.strptime(fecha_str, '%Y-%m-%d').date()
        except:
            pass
    if codigos:
        doc.codigos_extraidos = codigos

    db.session.commit()
    return jsonify({'success': True})

@bp.route('/search_code', methods=['POST'])
def search_code():
    data = request.get_json()
    code = data.get('code', '')
    results = Document.query.filter(Document.codigos_extraidos.ilike(f"{code}%")).all()

    out = []
    for d in results:
        out.append({
            'id': d.id,
            'name': d.name,
            'date': d.date.strftime('%Y-%m-%d'),
            'path': d.path,
            'codigos_extraidos': d.codigos_extraidos
        })
    return jsonify(out)

@bp.route('/codes', methods=['GET'])
def autocomplete_codes():
    term = request.args.get('starts_with', '')
    if not term:
        return jsonify([])

    codes = db.session.query(Document.codigos_extraidos).filter(Document.codigos_extraidos.ilike(f'{term}%')).limit(10).all()
    unique_codes = set()
    for c in codes:
        for code in (c[0] or "").split(','):
            code = code.strip()
            if code.lower().startswith(term.lower()):
                unique_codes.add(code)
    return jsonify(list(unique_codes))

@bp.route('/download_csv', methods=['GET'])
def download_csv():
    docs = Document.query.all()
    si = StringIO()
    cw = csv.writer(si)
    cw.writerow(['id', 'name', 'date', 'path', 'codigos_extraidos'])
    for d in docs:
        cw.writerow([d.id, d.name, d.date.strftime('%Y-%m-%d'), d.path, d.codigos_extraidos])
    output = si.getvalue()
    return current_app.response_class(
        output,
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment;filename=documentos.csv'}
    )

@bp.route('/download_zip', methods=['GET'])
def download_zip():
    memory_file = BytesIO()
    with zipfile.ZipFile(memory_file, 'w') as zf:
        upload_folder = current_app.config['UPLOAD_FOLDER']
        docs = Document.query.all()
        for d in docs:
            file_path = os.path.join(upload_folder, d.path)
            if os.path.isfile(file_path):
                zf.write(file_path, d.path)
    memory_file.seek(0)
    return send_file(memory_file, mimetype='application/zip', as_attachment=True, download_name='documentos.zip')
