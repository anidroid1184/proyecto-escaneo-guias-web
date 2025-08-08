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


@main_bp.route('/', methods=['GET', 'POST'])
def index():
    current_session = g.session

    if request.method == 'POST':
        file = request.files.get('excel_file')

        if not file or file.filename == '':
            flash('No se seleccionó archivo Excel.', 'danger')
            return render_template('index.html',
                                   current_session=current_session)

        if not allowed_file(file.filename, Config.ALLOWED_EXTENSIONS):
            flash('Tipo de archivo no permitido para el Excel.', 'danger')
            return render_template('index.html',
                                   current_session=current_session)

        if current_session.is_closed:
            flash('La sesión actual está cerrada. No se pueden cargar más guías.',
                  'danger')
            return render_template('index.html',
                                   current_session=current_session)

        filepath = os.path.join(Config.UPLOAD_FOLDER,
                                secure_filename(file.filename))
        file.save(filepath)

        try:
            if filepath.endswith('.csv'):
                df = pd.read_csv(filepath)
            else:
                df = pd.read_excel(filepath)
        except Exception as e:
            flash(f'Error al leer el archivo Excel: {e}', 'danger')
            return render_template('index.html',
                                   current_session=current_session)

        n_added_guia = 0
        n_ignored_guia = 0
        n_added_session_status = 0

        for _, row in df.iterrows():
            tracking = sanitize_string(str(row.get('TRACKING', '')).strip())
            guia_internacional = sanitize_string(
                str(row.get('GUIA INTERNACIONAL', '')).strip())

            if not (tracking and guia_internacional):
                n_ignored_guia += 1
                continue

            guia = Guia.query.filter_by(tracking=tracking).first()
            if not guia:
                guia = Guia(tracking=tracking,
                            guia_internacional=guia_internacional,
                            fecha_recibido=None)
                db.session.add(guia)
                db.session.flush()
                n_added_guia += 1
            else:
                if guia.guia_internacional != guia_internacional:
                    guia.guia_internacional = guia_internacional
                existing_guia_status = GuiaSessionStatus.query.filter_by(
                    session_id=current_session.id, guia_id=guia.id).first()
                if existing_guia_status:
                    n_ignored_guia += 1
                    continue

            guia_status = GuiaSessionStatus(session_id=current_session.id,
                                            guia_id=guia.id,
                                            status='NO RECIBIDO')
            db.session.add(guia_status)
            n_added_session_status += 1

        db.session.commit()
        flash(f'Guías cargadas para la sesión del {current_session.session_date}. '
              f'{n_added_guia} nuevas guías añadidas, '
              f'{n_added_session_status} guías esperadas cargadas. '
              f'{n_ignored_guia} guías ignoradas (duplicados en Excel o ya en sesión).',
              'success')
        return redirect(url_for('main.index'))

    total_pending_packages = GuiaSessionStatus.query.filter(
        GuiaSessionStatus.session_id == current_session.id,
        GuiaSessionStatus.status.in_(['NO RECIBIDO', 'NO ESCANEADO'])
    ).count()

    not_registered_packages = GuiaSessionStatus.query.filter(
        GuiaSessionStatus.session_id == current_session.id,
        GuiaSessionStatus.status == 'NO ESPERADO'
    ).count()

    missing_to_scan_packages = GuiaSessionStatus.query.filter(
        GuiaSessionStatus.session_id == current_session.id,
        GuiaSessionStatus.status == 'NO RECIBIDO'
    ).count()

    return render_template('index.html',
                           current_session=current_session,
                           total_pending_packages=total_pending_packages,
                           not_registered_packages=not_registered_packages,
                           missing_to_scan_packages=missing_to_scan_packages)


@main_bp.route('/upload', methods=['GET', 'POST'])
def upload():
    flash('La carga de Excel ahora se realiza al iniciar una nueva sesión en la '
          'página principal.', 'info')
    return redirect(url_for('main.index'))
