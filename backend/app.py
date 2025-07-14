import os
import io
import csv
import zipfile
from datetime import datetime
from flask import Flask, request, jsonify, send_from_directory, send_file
from flask_cors import CORS
from werkzeug.utils import secure_filename
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# ---- Configuración de Base de Datos usando variables de entorno Clever Cloud ----
DB_NAME = os.getenv('MYSQL_ADDON_DB')
DB_USER = os.getenv('MYSQL_ADDON_USER')
DB_PASSWORD = os.getenv('MYSQL_ADDON_PASSWORD')
DB_HOST = os.getenv('MYSQL_ADDON_HOST')
DB_PORT = os.getenv('MYSQL_ADDON_PORT', '3306')


DB_URL = (
    f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    "?charset=utf8mb4"
)

UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')

# Si existe un archivo llamado uploads, bórralo antes de crear la carpeta
if os.path.exists(UPLOAD_FOLDER) and not os.path.isdir(UPLOAD_FOLDER):
    os.remove(UPLOAD_FOLDER)
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
CORS(app)

engine = create_engine(DB_URL, pool_pre_ping=True)
Session = sessionmaker(bind=engine)

# ============= SUBIR DOCUMENTO =============
@app.route('/api/upload', methods=['POST'])
def upload():
    file = request.files.get('file')
    name = request.form.get('name')
    codigos = request.form.get('codigos', '')
    if not file or not name:
        return jsonify({'ok': False, 'error': 'Archivo y nombre requeridos'}), 400
    filename = secure_filename(file.filename)
    save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(save_path)
    session = Session()
    try:
        session.execute(
            text("INSERT INTO documents (name, path, codigos_extraidos) VALUES (:name, :path, :codigos)"),
            {'name': name, 'path': filename, 'codigos': codigos}
        )
        session.commit()
        doc_id = session.execute(text("SELECT LAST_INSERT_ID()")).scalar()
        if codigos:
            for code in codigos.split(','):
                code = code.strip()
                if code:
                    session.execute(
                        text("INSERT INTO codes (document_id, code) VALUES (:doc_id, :code)"),
                        {'doc_id': doc_id, 'code': code}
                    )
            session.commit()
        return jsonify({'ok': True})
    except Exception as e:
        session.rollback()
        return jsonify({'ok': False, 'error': str(e)})
    finally:
        session.close()

# ============= LISTAR DOCUMENTOS =============
@app.route('/api/docs', methods=['GET'])
def docs():
    session = Session()
    q = request.args.get('search', '').strip()
    try:
        if q:
            rows = session.execute(
                text("SELECT * FROM documents WHERE name LIKE :q OR codigos_extraidos LIKE :q ORDER BY id DESC"),
                {'q': f"%{q}%"}
            ).fetchall()
        else:
            rows = session.execute(text("SELECT * FROM documents ORDER BY id DESC")).fetchall()
        docs = [dict(row) for row in rows]
        return jsonify({'ok': True, 'docs': docs})
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)})
    finally:
        session.close()

# ============= EDITAR DOCUMENTO =============
@app.route('/api/edit', methods=['POST'])
def edit():
    data = request.get_json()
    doc_id = data.get('id')
    name = data.get('name')
    codigos = data.get('codigos', '')
    session = Session()
    try:
        session.execute(
            text("UPDATE documents SET name=:name, codigos_extraidos=:codigos WHERE id=:id"),
            {'name': name, 'codigos': codigos, 'id': doc_id}
        )
        session.execute(text("DELETE FROM codes WHERE document_id=:id"), {'id': doc_id})
        for code in codigos.split(','):
            code = code.strip()
            if code:
                session.execute(
                    text("INSERT INTO codes (document_id, code) VALUES (:id, :code)"),
                    {'id': doc_id, 'code': code}
                )
        session.commit()
        return jsonify({'ok': True})
    except Exception as e:
        session.rollback()
        return jsonify({'ok': False, 'error': str(e)})
    finally:
        session.close()

# ============= ELIMINAR DOCUMENTO =============
@app.route('/api/delete', methods=['POST'])
def delete():
    data = request.get_json()
    doc_id = data.get('id')
    session = Session()
    try:
        doc = session.execute(text("SELECT * FROM documents WHERE id=:id"), {'id': doc_id}).fetchone()
        if doc:
            pdf_path = os.path.join(app.config['UPLOAD_FOLDER'], doc['path'])
            if os.path.exists(pdf_path):
                os.remove(pdf_path)
            session.execute(text("DELETE FROM codes WHERE document_id=:id"), {'id': doc_id})
            session.execute(text("DELETE FROM documents WHERE id=:id"), {'id': doc_id})
            session.commit()
            return jsonify({'ok': True})
        return jsonify({'ok': False, 'msg': 'No existe el documento'})
    except Exception as e:
        session.rollback()
        return jsonify({'ok': False, 'error': str(e)})
    finally:
        session.close()

# ============= BÚSQUEDA INTELIGENTE =============
@app.route('/api/search', methods=['POST'])
def search():
    data = request.get_json()
    q = data.get('query', '').strip()
    session = Session()
    try:
        rows = session.execute(
            text("SELECT * FROM documents WHERE name LIKE :q OR codigos_extraidos LIKE :q ORDER BY id DESC"),
            {'q': f"%{q}%"}
        ).fetchall()
        resultados = [dict(row) for row in rows]
        return jsonify({'ok': True, 'resultados': resultados})
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)})
    finally:
        session.close()

# ============= AUTOCOMPLETADO CÓDIGOS =============
@app.route('/api/suggest')
def suggest():
    q = request.args.get('q', '').strip()
    session = Session()
    try:
        codes = []
        if q:
            result = session.execute(
                text("SELECT code FROM codes WHERE code LIKE :q LIMIT 10"),
                {'q': f"{q}%"}
            )
            codes = [row.code for row in result]
        return jsonify({'ok': True, 'codes': codes})
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)})
    finally:
        session.close()

# ============= EXPORTAR CSV =============
@app.route('/api/export_csv')
def export_csv():
    session = Session()
    try:
        rows = session.execute(text("SELECT * FROM documents")).fetchall()
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(['id', 'name', 'date', 'path', 'codigos_extraidos'])
        for row in rows:
            writer.writerow([row.id, row.name, row.date, row.path, row.codigos_extraidos])
        output.seek(0)
        return send_file(
            io.BytesIO(output.getvalue().encode()),
            mimetype='text/csv',
            as_attachment=True,
            download_name='documentos.csv'
        )
    finally:
        session.close()

# ============= EXPORTAR ZIP DE PDFs =============
@app.route('/api/export_zip', methods=['POST'])
def export_zip():
    session = Session()
    archivos = request.json.get('archivos', [])
    try:
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w') as zf:
            if archivos:
                docs = session.execute(
                    text("SELECT path FROM documents WHERE path IN :archivos"),
                    {'archivos': tuple(archivos)}
                ).fetchall()
            else:
                docs = session.execute(text("SELECT path FROM documents")).fetchall()
            for doc in docs:
                path = os.path.join(app.config['UPLOAD_FOLDER'], doc.path)
                if os.path.exists(path):
                    zf.write(path, doc.path)
        zip_buffer.seek(0)
        return send_file(
            zip_buffer,
            mimetype='application/zip',
            as_attachment=True,
            download_name='documentos.zip'
        )
    finally:
        session.close()

# ============= SERVIR PDF INDIVIDUAL (para ver en frontend) =============
@app.route('/static/uploads/<path:filename>')
def serve_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/')
def home():
    return "Backend corriendo OK!"

# --- NO CAMBIES ESTE NOMBRE ---
if __name__ == '__main__':
    app.run(debug=True)
