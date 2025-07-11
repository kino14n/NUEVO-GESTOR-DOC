
from flask import Blueprint, request, jsonify, current_app
from models import db, Document, Code
from werkzeug.utils import secure_filename
from datetime import datetime
import os

bp = Blueprint('documentos', __name__)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']

@bp.route('/search', methods=['POST'])
def search():
    data = request.json
    term = data.get('query', '')
    q = db.session.query(Document)
    if term:
        like = f"%{term}%"
        q = q.filter((Document.name.ilike(like)) | (Document.codigos_extraidos.ilike(like)))
    results = q.order_by(Document.date.desc()).all()
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

@bp.route('/add', methods=['POST'])
def add():
    data = request.json
    doc = Document(
        name=data['name'],
        date=datetime.strptime(data['date'], "%Y-%m-%d"),
        path=data.get('path'),
        codigos_extraidos=data.get('codigos_extraidos')
    )
    db.session.add(doc)
    db.session.commit()
    return jsonify({'success': True, 'id': doc.id})

@bp.route('/edit/<int:doc_id>', methods=['POST'])
def edit(doc_id):
    data = request.json
    doc = Document.query.get_or_404(doc_id)
    doc.name = data.get('name', doc.name)
    if data.get('date'):
        doc.date = datetime.strptime(data['date'], "%Y-%m-%d")
    doc.path = data.get('path', doc.path)
    doc.codigos_extraidos = data.get('codigos_extraidos', doc.codigos_extraidos)
    db.session.commit()
    return jsonify({'success': True})

@bp.route('/delete/<int:doc_id>', methods=['POST'])
def delete(doc_id):
    doc = Document.query.get_or_404(doc_id)
    db.session.delete(doc)
    db.session.commit()
    return jsonify({'success': True})

@bp.route('/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        upload_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        os.makedirs(os.path.dirname(upload_path), exist_ok=True)
        file.save(upload_path)
        return jsonify({'success': True, 'filename': filename, 'path': upload_path})
    return jsonify({'error': 'File not allowed'}), 400
