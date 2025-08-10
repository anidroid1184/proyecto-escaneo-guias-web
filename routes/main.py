import os
import pandas as pd
from flask import (
    Blueprint, render_template, request, redirect, url_for, flash, g
)
from werkzeug.utils import secure_filename
from models import db, Guia, GuiaSessionStatus
from utils import sanitize_string, allowed_file
from config import Config


main_bp = Blueprint('main', __name__)


@main_bp.route('/', methods=['GET'])
def index():
    current_session = getattr(g, 'session', None)
    footer_counts = {'total_pending_packages': 0,
                     'not_registered_packages': 0,
                     'missing_to_scan_packages': 0}
    if current_session:
        from routes.records import get_updated_counts_for_session
        footer_counts = get_updated_counts_for_session(current_session.id)

    return render_template('index.html',
                           current_session=current_session,
                           footer_counts=footer_counts)


@main_bp.route('/upload', methods=['GET', 'POST'])
def upload():
    current_session = getattr(g, 'session', None)

    if request.method == 'POST':
        if not current_session:
            flash('No hay sesión activa. No se pueden cargar guías.', 'danger')
            return render_template('upload.html', current_session=current_session)

        file = request.files.get('excel_file')
        if not file or file.filename == '':
            flash('No se seleccionó archivo Excel.', 'danger')
            return render_template('upload.html', current_session=current_session)

        if not allowed_file(file.filename, Config.ALLOWED_EXTENSIONS):
            flash('Tipo de archivo no permitido para el Excel.', 'danger')
            return render_template('upload.html', current_session=current_session)

        if getattr(current_session, 'is_closed', False):
            flash('La sesión actual está cerrada. No se pueden cargar más guías.', 'danger')
            return render_template('upload.html', current_session=current_session)

        filepath = os.path.join(Config.UPLOAD_FOLDER, secure_filename(file.filename))
        file.save(filepath)

        try:
            if filepath.endswith('.csv'):
                df = pd.read_csv(filepath)
            else:
                df = pd.read_excel(filepath)
        except Exception as e:
            flash(f'Error al leer el archivo Excel: {e}', 'danger')
            return render_template('upload.html', current_session=current_session)

        n_added_guia = 0
        n_ignored_guia = 0
        n_added_session_status = 0

        for _, row in df.iterrows():
            tracking = sanitize_string(str(row.get('TRACKING', '')).strip())
            guia_internacional = sanitize_string(str(row.get('GUIA INTERNACIONAL', '')).strip())

            if not (tracking and guia_internacional):
                n_ignored_guia += 1
                continue

            guia = Guia.query.filter_by(tracking=tracking).first()
            if not guia:
                guia = Guia(tracking=tracking, guia_internacional=guia_internacional, fecha_recibido=None)
                db.session.add(guia)
                db.session.flush()
                n_added_guia += 1
            else:
                if guia.guia_internacional != guia_internacional:
                    guia.guia_internacional = guia_internacional
                existing_guia_status = GuiaSessionStatus.query.filter_by(session_id=current_session.id, guia_id=guia.id).first()
                if existing_guia_status:
                    n_ignored_guia += 1
                    continue

            guia_status = GuiaSessionStatus(session_id=current_session.id, guia_id=guia.id, status='NO RECIBIDO')
            db.session.add(guia_status)
            n_added_session_status += 1

        db.session.commit()
        flash(f'Guías cargadas para la sesión del {current_session.session_date}. '
              f'{n_added_guia} nuevas guías añadidas, '
              f'{n_added_session_status} guías esperadas cargadas. '
              f'{n_ignored_guia} guías ignoradas (duplicados en Excel o ya en sesión).',
              'success')
        return redirect(url_for('main.upload'))

    return render_template('upload.html',
                           current_session=current_session)


@main_bp.route('/delete_current_excel', methods=['POST'])
def delete_current_excel():
    # Se elimina la restricción de sesión activa para permitir eliminar guías en cualquier momento

    current_session = getattr(g, 'session', None)
    if current_session:
        GuiaSessionStatus.query.filter_by(session_id=current_session.id).delete()
        db.session.commit()
        flash('Todas las guías cargadas para la sesión actual han sido eliminadas.', 'success')
    else:
        flash('No hay sesión activa para eliminar guías.', 'warning')
    return redirect(url_for('main.index'))
