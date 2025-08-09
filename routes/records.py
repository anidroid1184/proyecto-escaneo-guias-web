import os
import pandas as pd
from flask import (
    Blueprint, render_template, request, redirect, url_for, flash,
    send_from_directory, g, jsonify
)
from datetime import datetime
from models import db, Guia, GuiaSessionStatus, Session
from config import Config
from utils import sanitize_string


# Función auxiliar para obtener los conteos actualizados (similar a la de scan.py)
def get_updated_counts_for_session(session_id):
    # Total de guías en la sesión que no han sido marcadas como RECIBIDO
    total_pending = GuiaSessionStatus.query.filter(
        GuiaSessionStatus.session_id == session_id,
        GuiaSessionStatus.status != 'RECIBIDO'
    ).count()
    not_registered = GuiaSessionStatus.query.filter_by(
        session_id=session_id, status='NO ESPERADO').count()
    missing_to_scan = GuiaSessionStatus.query.filter_by(
        session_id=session_id, status='NO RECIBIDO').count()
    return {
        'total_pending_packages': total_pending,
        'not_registered_packages': not_registered,
        'missing_to_scan_packages': missing_to_scan
    }


records_bp = Blueprint('records', __name__)


@records_bp.route('/registros', methods=['GET'])
def registros():
    sessions = Session.query.order_by(Session.session_date.desc()).all()

    session_id = request.args.get('session_id', type=int)
    current_session = None
    if session_id:
        current_session = Session.query.get(session_id)
    elif g.session:
        current_session = g.session
    elif sessions:
        current_session = sessions[0]

    guia_statuses = []
    footer_counts = {'total_pending_packages': 0,
                     'not_registered_packages': 0,
                     'missing_to_scan_packages': 0}

    if current_session:
        query = GuiaSessionStatus.query.filter_by(
            session_id=current_session.id).join(Guia)

        tracking = request.args.get('tracking', '').strip()
        guia_internacional = request.args.get('guia_internacional', '').strip()
        status_filter = request.args.get('status', '').strip()

        if tracking:
            query = query.filter(Guia.tracking.ilike(f'%{tracking}%'))
        if guia_internacional:
            query = query.filter(
                Guia.guia_internacional.ilike(f'%{guia_internacional}%'))
        if status_filter:
            query = query.filter(GuiaSessionStatus.status == status_filter)

        guia_statuses = query.order_by(
            GuiaSessionStatus.timestamp_status_change.desc()).all()

        # Obtener los conteos para el footer de la sesión actual
        footer_counts = get_updated_counts_for_session(current_session.id)

    return render_template('registros.html',
                           guia_statuses=guia_statuses,
                           sessions=sessions,
                           current_session=current_session,
                           selected_session_id=(current_session.id
                                                if current_session else None),
                           footer_counts=footer_counts)


@records_bp.route('/export', methods=['GET'])
def export():
    session_id = request.args.get('session_id', type=int)
    if not session_id:
        flash('Debe seleccionar una sesión para exportar.', 'danger')
        return redirect(url_for('records.registros'))

    current_session = Session.query.get(session_id)
    if not current_session:
        flash('Sesión no encontrada.', 'danger')
        return redirect(url_for('records.registros'))

    query = GuiaSessionStatus.query.filter_by(
        session_id=current_session.id).join(Guia)

    tracking = request.args.get('tracking', '').strip()
    guia_internacional = request.args.get('guia_internacional', '').strip()
    status_filter = request.args.get('status', '').strip()

    if tracking:
        query = query.filter(Guia.tracking.ilike(f'%{tracking}%'))
    if guia_internacional:
        query = query.filter(
            Guia.guia_internacional.ilike(f'%{guia_internacional}%'))
    if status_filter:
        query = query.filter(GuiaSessionStatus.status == status_filter)

    guia_statuses = query.order_by(
        GuiaSessionStatus.timestamp_status_change.desc()).all()

    data = []
    for gs in guia_statuses:
        fecha_recibido_str = (gs.guia.fecha_recibido.strftime('%Y-%m-%d %H:%M:%S')  # noqa: E501
                              if gs.guia.fecha_recibido else 'N/A')
        data.append({
            'Tracking': gs.guia.tracking or 'N/A',
            'Guía Internacional': gs.guia.guia_internacional or 'N/A',
            'Fecha Recibido (Guía)': fecha_recibido_str,
            'Estado Sesión': gs.status,
            'Fecha y Hora Estado': gs.timestamp_status_change.strftime(
                '%Y-%m-%d %H:%M:%S')
        })

    df = pd.DataFrame(data)
    filename = (
        f'guias_sesion_{current_session.session_date.strftime("%Y%m%d")}'
        '.xlsx'
    )
    filepath = os.path.join(Config.EXPORT_FOLDER, filename)
    df.to_excel(filepath, index=False)
    return send_from_directory(Config.EXPORT_FOLDER, filename,
                               as_attachment=True)


@records_bp.route(
    '/edit_guia_status/<int:guia_id>/<int:session_id>',
    methods=['GET', 'POST']
)
def edit_guia_status(guia_id, session_id):
    guia_status = GuiaSessionStatus.query.filter_by(
        guia_id=guia_id, session_id=session_id).first_or_404()
    guia = Guia.query.get(guia_id)
    current_session = Session.query.get(session_id)

    if request.method == 'POST':
        try:
            data = request.get_json()
            if not data:
                return jsonify({'error': 'Datos no proporcionados.'}), 400

            new_status = data.get('new_status')
            updated_tracking = data.get('tracking')
            updated_guia_internacional = data.get('guia_internacional')

            changes_made = False

            # Manejar actualización de estado
            if new_status and new_status in [
                'RECIBIDO', 'NO RECIBIDO', 'NO ESPERADO', 'NO ESCANEADO'
            ] and guia_status.status != new_status:
                guia_status.status = new_status
                guia_status.timestamp_status_change = datetime.utcnow()
                changes_made = True
            elif new_status and new_status not in [
                'RECIBIDO', 'NO RECIBIDO', 'NO ESPERADO', 'NO ESCANEADO'
            ]:
                return jsonify({'error': 'Estado no válido.'}), 400

            # Manejar actualización de tracking
            if updated_tracking is not None and guia.tracking != updated_tracking:
                guia.tracking = updated_tracking
                changes_made = True

            # Manejar actualización de guia_internacional
            if updated_guia_internacional is not None and guia.guia_internacional != updated_guia_internacional:
                guia.guia_internacional = updated_guia_internacional
                changes_made = True

            if not changes_made:
                return jsonify({
                    'success': True,
                    'message': 'No se detectaron cambios para guardar.',
                    'new_status': guia_status.status,
                    'tracking': guia.tracking,
                    'guia_internacional': guia.guia_internacional
                })

            db.session.commit()

            response_data = {
                'success': True,
                'message': 'Guía actualizada exitosamente.',
                'new_status': guia_status.status,
                'tracking': guia.tracking,
                'guia_internacional': guia.guia_internacional,
                'redirect_to_records': True  # Señal para el frontend
            }
            return jsonify(response_data)
        except Exception as e:
            db.session.rollback()  # Revertir cualquier cambio en caso de error
            return jsonify({'error': f'Error interno del servidor: {str(e)}'}), 500
    else:  # Esto maneja el método GET
        return render_template('edit_guia_status.html', guia_status=guia_status,
                               guia=guia, current_session=current_session)


@records_bp.route('/update_guia_fields', methods=['POST'])
def update_guia_fields():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Datos no proporcionados.'}), 400

        guia_id_raw = data.get('guia_id')
        try:
            guia_id = int(guia_id_raw)
        except (TypeError, ValueError):
            guia_id = None
        scanned_code = data.get('scanned_code', '').strip()
        field_type = data.get('field_type')

        if not guia_id or not scanned_code or not field_type:
            return jsonify({'error': ('Datos incompletos para la actualización.')}), 400

        guia = Guia.query.get(guia_id)
        if not guia:
            return jsonify({'error': 'Guía no encontrada.'}), 404

        scanned_code = sanitize_string(scanned_code)
        message = ""

        if field_type == 'tracking':
            if guia.tracking == scanned_code:
                message = ("El Tracking ya es el mismo. No se realizó ningún "
                           "cambio.")
            else:
                guia.tracking = scanned_code
                message = "Tracking actualizado exitosamente."
        elif field_type == 'guia_internacional':
            if guia.guia_internacional == scanned_code:
                message = ("La Guía Internacional ya es la misma. No se "
                           "realizó ningún cambio.")
            else:
                guia.guia_internacional = scanned_code
                message = "Guía Internacional actualizada exitosamente."
        elif field_type == 'both':
            # Lógica para reemplazar ambos si son diferentes
            updated_tracking = False
            updated_guia_internacional = False

            if guia.tracking != scanned_code:
                guia.tracking = scanned_code
                updated_tracking = True
            if guia.guia_internacional != scanned_code:
                guia.guia_internacional = scanned_code
                updated_guia_internacional = True

            if updated_tracking and updated_guia_internacional:
                message = ("Tracking y Guía Internacional actualizados "
                           "exitosamente.")
            elif updated_tracking:
                message = ("Tracking actualizado exitosamente (Guía "
                           "Internacional ya era la misma).")
            elif updated_guia_internacional:
                message = ("Guía Internacional actualizada exitosamente "
                           "(Tracking ya era el mismo).")
            else:
                message = "Ambos campos ya eran los mismos. No se realizó ningún cambio."
        else:
            return jsonify({'error': 'Tipo de campo no válido.'}), 400

        db.session.commit()

        return jsonify({
            'success': True,
            'message': message,
            'tracking': guia.tracking,
            'guia_internacional': guia.guia_internacional
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Error interno del servidor: {str(e)}'}), 500
