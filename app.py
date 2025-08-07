import os
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from werkzeug.utils import secure_filename
from datetime import datetime
import pandas as pd
from models import db, Persona, Registro
from forms import PersonaForm
import re

# Configuración básica de la app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'clave_prueba'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = os.path.join(os.getcwd(), 'uploads')
app.config['EXPORT_FOLDER'] = os.path.join(os.getcwd(), 'exports')
app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024  # 2MB máximo por archivo

# Inicializar SQLAlchemy
with app.app_context():
    db.init_app(app)
    db.create_all()

# Extensiones permitidas para carga de archivos
ALLOWED_EXTENSIONS = {'xlsx', 'csv'}


def allowed_file(filename: str) -> bool:
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Función para sanitizar cadenas (solo letras, números y algunos símbolos permitidos)


def sanitize_string(s: str) -> str:
    return re.sub(r'[^\w\s\-\.\,\áéíóúÁÉÍÓÚñÑ]', '', s)

# Ruta principal: escaneo e ingreso manual


@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

# Procesamiento de código escaneado o ingresado manualmente


@app.route('/scan', methods=['POST'])
def scan():
    data = request.get_json()
    codigo = data.get('codigo', '').strip()
    codigo = sanitize_string(codigo)
    if not codigo:
        return jsonify({'error': 'codigo_vacio'}), 400
    persona = Persona.query.filter_by(codigo_barras=codigo).first()
    if not persona:
        return jsonify({'error': 'no_registrado', 'codigo': codigo}), 404
    # Buscar último registro de la persona
    ultimo = Registro.query.filter_by(persona_id=persona.id).order_by(
        Registro.timestamp.desc()).first()
    if not ultimo or ultimo.tipo == 'salida':
        tipo = 'entrada'
    else:
        tipo = 'salida'
    # Crear nuevo registro
    nuevo = Registro(persona_id=persona.id, tipo=tipo)
    db.session.add(nuevo)
    db.session.commit()
    return jsonify({
        'nombre': persona.nombre,
        'documento': persona.documento,
        'codigo_barras': persona.codigo_barras,
        'tipo': tipo,
        'timestamp': nuevo.timestamp.strftime('%Y-%m-%d %H:%M:%S')
    })

# Formulario de alta manual de persona


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = PersonaForm()
    # Prellenar código si viene por querystring
    if request.method == 'GET' and 'codigo' in request.args:
        form.codigo_barras.data = sanitize_string(request.args['codigo'])
    if form.validate_on_submit():
        # Validar unicidad de documento y código de barras
        nombre = sanitize_string(form.nombre.data.strip())
        documento = sanitize_string(form.documento.data.strip())
        codigo_barras = sanitize_string(form.codigo_barras.data.strip())
        if Persona.query.filter_by(documento=documento).first():
            flash('El documento ya está registrado.', 'danger')
            return render_template('register.html', form=form)
        if Persona.query.filter_by(codigo_barras=codigo_barras).first():
            flash('El código de barras ya está registrado.', 'danger')
            return render_template('register.html', form=form)
        persona = Persona(
            nombre=nombre,
            documento=documento,
            codigo_barras=codigo_barras
        )
        db.session.add(persona)
        db.session.commit()
        # Registrar entrada inmediata
        registro = Registro(persona_id=persona.id, tipo='entrada')
        db.session.add(registro)
        db.session.commit()
        flash('Persona registrada y entrada registrada exitosamente.', 'success')
        return redirect(url_for('index'))
    return render_template('register.html', form=form)

# Vista de carga de Excel


@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No se seleccionó archivo.', 'danger')
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            flash('Nombre de archivo vacío.', 'danger')
            return redirect(request.url)
        if not allowed_file(file.filename):
            flash('Tipo de archivo no permitido.', 'danger')
            return redirect(request.url)
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        # Validar tamaño real del archivo
        if os.path.getsize(filepath) > app.config['MAX_CONTENT_LENGTH']:
            os.remove(filepath)
            flash('El archivo excede el tamaño permitido.', 'danger')
            return redirect(request.url)
        # Procesar archivo con pandas
        try:
            if filename.endswith('.csv'):
                df = pd.read_csv(filepath)
            else:
                df = pd.read_excel(filepath)
        except Exception as e:
            flash(f'Error al leer el archivo: {e}', 'danger')
            return redirect(request.url)
        n_añadidas = 0
        n_ignoradas = 0
        for _, row in df.iterrows():
            nombre = sanitize_string(str(row.get('nombre', '')).strip())
            documento = sanitize_string(str(row.get('documento', '')).strip())
            codigo_barras = sanitize_string(
                str(row.get('codigo_barras', '')).strip())
            if not (nombre and documento and codigo_barras):
                n_ignoradas += 1
                continue
            if Persona.query.filter((Persona.documento == documento) | (Persona.codigo_barras == codigo_barras)).first():
                n_ignoradas += 1
                continue
            persona = Persona(nombre=nombre, documento=documento,
                              codigo_barras=codigo_barras)
            db.session.add(persona)
            n_añadidas += 1
        db.session.commit()
        flash(f'{n_añadidas} personas añadidas, {n_ignoradas} ignoradas (duplicados o datos incompletos).', 'success')
        return redirect(url_for('upload'))
    return render_template('upload.html')

# Tabla de registros con filtros


@app.route('/registros', methods=['GET'])
def registros():
    # Filtros por querystring
    nombre = request.args.get('nombre', '').strip()
    documento = request.args.get('documento', '').strip()
    tipo = request.args.get('tipo', '').strip()
    fecha_inicio = request.args.get('fecha_inicio', '').strip()
    fecha_fin = request.args.get('fecha_fin', '').strip()
    query = Registro.query.join(Persona)
    if nombre:
        query = query.filter(Persona.nombre.ilike(f'%{nombre}%'))
    if documento:
        query = query.filter(Persona.documento.ilike(f'%{documento}%'))
    if tipo:
        query = query.filter(Registro.tipo == tipo)
    if fecha_inicio:
        try:
            dt_inicio = datetime.strptime(fecha_inicio, '%Y-%m-%d')
            query = query.filter(Registro.timestamp >= dt_inicio)
        except ValueError:
            pass
    if fecha_fin:
        try:
            dt_fin = datetime.strptime(fecha_fin, '%Y-%m-%d')
            query = query.filter(Registro.timestamp <= dt_fin)
        except ValueError:
            pass
    registros = query.order_by(Registro.timestamp.desc()).all()
    return render_template('registros.html', registros=registros)

# Exportar registros a Excel


@app.route('/export', methods=['GET'])
def export():
    query = Registro.query.join(Persona)
    # Aplicar mismos filtros que en /registros
    nombre = request.args.get('nombre', '').strip()
    documento = request.args.get('documento', '').strip()
    tipo = request.args.get('tipo', '').strip()
    fecha_inicio = request.args.get('fecha_inicio', '').strip()
    fecha_fin = request.args.get('fecha_fin', '').strip()
    if nombre:
        query = query.filter(Persona.nombre.ilike(f'%{nombre}%'))
    if documento:
        query = query.filter(Persona.documento.ilike(f'%{documento}%'))
    if tipo:
        query = query.filter(Registro.tipo == tipo)
    if fecha_inicio:
        try:
            dt_inicio = datetime.strptime(fecha_inicio, '%Y-%m-%d')
            query = query.filter(Registro.timestamp >= dt_inicio)
        except ValueError:
            pass
    if fecha_fin:
        try:
            dt_fin = datetime.strptime(fecha_fin, '%Y-%m-%d')
            query = query.filter(Registro.timestamp <= dt_fin)
        except ValueError:
            pass
    registros = query.order_by(Registro.timestamp.desc()).all()
    # Construir DataFrame para exportar
    data = []
    for r in registros:
        data.append({
            'Nombre': r.persona.nombre,
            'Documento': r.persona.documento,
            'Código': r.persona.codigo_barras,
            'Tipo': r.tipo,
            'Fecha y Hora': r.timestamp.strftime('%Y-%m-%d %H:%M:%S')
        })
    df = pd.DataFrame(data)
    filename = f'registros_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
    filepath = os.path.join(app.config['EXPORT_FOLDER'], filename)
    df.to_excel(filepath, index=False)
    return send_from_directory(app.config['EXPORT_FOLDER'], filename, as_attachment=True)

# Manejo de errores generales


@app.errorhandler(413)
def file_too_large(e):
    flash('El archivo es demasiado grande (máx 2MB).', 'danger')
    return redirect(request.url)


@app.errorhandler(404)
def not_found(e):
    return render_template('404.html'), 404


@app.errorhandler(500)
def server_error(e):
    return render_template('500.html'), 500


if __name__ == '__main__':
    # Crear carpetas necesarias si no existen
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['EXPORT_FOLDER'], exist_ok=True)
    app.run(debug=True, host='0.0.0.0', port=5000)
