import re
import os
import pandas as pd
from datetime import date
from werkzeug.utils import secure_filename
from models import db, Guia, Registro, Session, GuiaSessionStatus

def sanitize_string(s: str) -> str:
    """
    Sanitiza una cadena, permitiendo solo letras, números y algunos símbolos.
    """
    return re.sub(r'[^\w\s\-\.\,\áéíóúÁÉÍÓÚñÑ]', '', s)


def allowed_file(filename: str, allowed_extensions: set) -> bool:
    """
    Verifica si la extensión de un archivo está permitida.
    """
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_extensions


def get_session_counts(session_id: int) -> dict:
    """
    Calcula los conteos de paquetes para una sesión dada.
    """
    total_pending_packages = GuiaSessionStatus.query.filter(
        GuiaSessionStatus.session_id == session_id,
        GuiaSessionStatus.status.in_(['NO RECIBIDO', 'NO ESCANEADO'])
    ).count()

    not_registered_packages = GuiaSessionStatus.query.filter(
        GuiaSessionStatus.session_id == session_id,
        GuiaSessionStatus.status == 'NO ESPERADO'
    ).count()

    missing_to_scan_packages = GuiaSessionStatus.query.filter(
        GuiaSessionStatus.session_id == session_id,
        GuiaSessionStatus.status == 'NO RECIBIDO'
    ).count()
    return {
        'total_pending_packages': total_pending_packages,
        'not_registered_packages': not_registered_packages,
        'missing_to_scan_packages': missing_to_scan_packages
    }


def process_excel_upload(file, current_session, app_config):
    """
    Procesa un archivo Excel/CSV cargado, añadiendo guías a la base de datos.
    """
    filepath = os.path.join(app_config['UPLOAD_FOLDER'], secure_filename(file.filename))
    file.save(filepath)

    try:
        if filepath.endswith('.csv'):
            df = pd.read_csv(filepath)
        else:
            df = pd.read_excel(filepath)
    except Exception as e:
        return {'error': f'Error al leer el archivo Excel: {e}'}

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
    return {
        'success': True,
        'n_added_guia': n_added_guia,
        'n_added_session_status': n_added_session_status,
        'n_ignored_guia': n_ignored_guia
    }
