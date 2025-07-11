
from flask import Blueprint, request, jsonify
from models import db, Code

bp = Blueprint('codes', __name__)

@bp.route('/by_document/<int:document_id>', methods=['GET'])
def by_document(document_id):
    codes = Code.query.filter_by(document_id=document_id).all()
    return jsonify([{'id': c.id, 'code': c.code} for c in codes])

@bp.route('/add', methods=['POST'])
def add():
    data = request.json
    code = Code(
        document_id=data['document_id'],
        code=data['code']
    )
    db.session.add(code)
    db.session.commit()
    return jsonify({'success': True, 'id': code.id})

@bp.route('/delete/<int:code_id>', methods=['POST'])
def delete(code_id):
    code = Code.query.get_or_404(code_id)
    db.session.delete(code)
    db.session.commit()
    return jsonify({'success': True})

@bp.route('/suggest', methods=['POST'])
def suggest():
    prefix = request.json.get('code', '')
    codes = Code.query.filter(Code.code.ilike(f"{prefix}%")).limit(10).all()
    return jsonify([c.code for c in codes])
