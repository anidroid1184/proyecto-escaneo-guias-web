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

    return render_template('registros.html',
                           guia_statuses=guia_statuses,
                           sessions=sessions,
                           current_session=current_session,
                           selected_session_id=(current_session.id
                                                if current_session else None))


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
        fecha_recibido_str = (gs.guia.fecha_recibido.strftime('%Y-%m-%d %H:%M:%S')
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
            scanned_code = data.get('scanned_code', '').strip()
            scan_field_choice = data.get('scan_field_choice')

            updated_fields = {}
            
            # 1. Manejar actualización de estado
            if new_status and new_status in [
                'RECIBIDO', 'NO RECIBIDO', 'NO ESPERADO', 'NO ESCANEADO'
            ]:
                guia_status.status = new_status
                guia_status.timestamp_status_change = datetime.utcnow()
                updated_fields['new_status'] = new_status
            elif new_status:  # Si se envió un estado pero no es válido
                return jsonify({'error': 'Estado no válido.'}), 400

            # 2. Manejar actualización de código escaneado
            if scanned_code:
                scanned_code = sanitize_string(scanned_code)
                
                if scan_field_choice == 'tracking':
                    guia.tracking = scanned_code
                    updated_fields['tracking'] = scanned_code
                elif scan_field_choice == 'guia_internacional':
                    guia.guia_internacional = scanned_code
                    updated_fields['guia_internacional'] = scanned_code
                elif scan_field_choice == 'both':
                    # Si se elige 'both', la lógica de intuición se aplica
                    if scanned_code.startswith('TBA'):
                        guia.tracking = scanned_code
                        updated_fields['tracking'] = scanned_code
                    elif scanned_code.startswith('BOG'):
                        guia.guia_internacional = scanned_code
                        updated_fields['guia_internacional'] = scanned_code
                    else:
                        # Si no se puede intuir, se actualiza el tracking por defecto
                        guia.tracking = scanned_code
                        updated_fields['tracking'] = scanned_code
                else:
                    # Si no se especifica el campo, aplicar la lógica de intuición
                    if scanned_code.startswith('TBA'):
                        guia.tracking = scanned_code
                        updated_fields['tracking'] = scanned_code
                    elif scanned_code.startswith('BOG'):
                        guia.guia_internacional = scanned_code
                        updated_fields['guia_internacional'] = scanned_code
                    else:
                        guia.tracking = scanned_code  # Por defecto, actualizar tracking
                        updated_fields['tracking'] = scanned_code
            
            # Si no se realizó ninguna actualización, devolver un mensaje
            if not updated_fields:
                return jsonify({
                    'error': 'No se proporcionaron datos válidos para actualizar.'
                }), 400

            db.session.commit()
            
            # Preparar la respuesta con los datos actualizados
            response_data = {
                'success': True,
                'message': 'Cambios guardados exitosamente.',
                'new_status': guia_status.status,
                'tracking': guia.tracking,
                'guia_internacional': guia.guia_internacional
            }
            return jsonify(response_data)
        except Exception as e:
            db.session.rollback() # Revertir cualquier cambio en caso de error
            return jsonify({'error': f'Error interno del servidor: {str(e)}'}), 500

    return render_template('edit_guia_status.html', guia_status=guia_status,
                           guia=guia, current_session=current_session)
