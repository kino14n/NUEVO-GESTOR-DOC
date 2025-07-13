
from flask import Blueprint, request, jsonify, session
from models import db
from models import Usuario

bp = Blueprint('usuarios', __name__)

@bp.route('/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    user = Usuario.query.filter_by(username=username).first()
    if user and user.check_password(password):
        session['user_id'] = user.id
        return jsonify({'success': True, 'is_admin': user.is_admin})
    return jsonify({'success': False, 'error': 'Credenciales incorrectas'}), 401

@bp.route('/logout', methods=['POST'])
def logout():
    session.pop('user_id', None)
    return jsonify({'success': True})
