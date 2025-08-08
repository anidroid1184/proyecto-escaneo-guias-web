from flask import Blueprint, request, jsonify, g
from datetime import datetime
from models import db, Guia, Registro, GuiaSessionStatus
from utils import sanitize_string


scan_bp = Blueprint('scan', __name__)


@scan_bp.route('/scan', methods=['POST'])
def scan():
    if not g.session:
        return jsonify({'error': 'No hay una sesión activa. '  # noqa: E501
                                 'Por favor, inicie una sesión primero.'}), 400

    data = request.get_json()
    scanned_code = data.get('code', '').strip()
    scanned_code = sanitize_string(scanned_code)

    if not scanned_code:
        return jsonify({'error': 'No se proporcionó ningún código para escanear.'}), 400

    guia = Guia.query.filter(
        (Guia.tracking == scanned_code) |
        (Guia.guia_internacional == scanned_code)
    ).first()

    guia_session_status = None
    if guia:
        guia_session_status = GuiaSessionStatus.query.filter_by(
            session_id=g.session.id, guia_id=guia.id).first()
        print(f"DEBUG: Guia encontrada: {guia.tracking or guia.guia_internacional}, "
              f"Status en sesión: {guia_session_status.status if guia_session_status else 'No asociado a sesión'}")

    # Función auxiliar para obtener los conteos actualizados
    def get_updated_counts():
        total_pending = GuiaSessionStatus.query.filter_by(
            session_id=g.session.id).count()
        not_registered = GuiaSessionStatus.query.filter_by(
            session_id=g.session.id, status='NO ESPERADO').count()
        missing_to_scan = GuiaSessionStatus.query.filter_by(
            session_id=g.session.id, status='NO RECIBIDO').count()
        return {
            'total_pending_packages': total_pending,
            'not_registered_packages': not_registered,
            'missing_to_scan_packages': missing_to_scan
        }

    if not guia or not guia_session_status:
        # No registrar la guía ni el status inmediatamente,
        # solo indicar que es desconocido
        message = (f'El código "{scanned_code}" no corresponde a una guía '  # noqa: E501
                   'conocida o esperada en esta sesión.')
        return jsonify({
            'error': 'unknown_package_detected',
            'code': scanned_code,
            'message': message
        })

    if guia_session_status.status == 'NO RECIBIDO':
        guia_session_status.status = 'RECIBIDO'
        guia_session_status.timestamp_status_change = datetime.utcnow()
        db.session.commit()

        registro = Registro(guia_id=guia.id, session_id=g.session.id,
                            tipo='entrada')
        db.session.add(registro)
        db.session.commit()

        response_data = {
            'tracking': guia.tracking,
            'guia_internacional': guia.guia_internacional,
            'fecha_recibido': (guia.fecha_recibido.strftime('%Y-%m-%d %H:%M:%S')  # noqa: E501
                               if guia.fecha_recibido else ''),
            'tipo': 'entrada',
            'timestamp': registro.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            'status': 'RECIBIDO',
            'message': (f'Guía {guia.guia_internacional or guia.tracking} '  # noqa: E501
                        'registrada exitosamente.')
        }
        response_data.update(get_updated_counts())
        return jsonify(response_data)

    elif guia_session_status.status == 'RECIBIDO':
        response_data = {
            'tracking': guia.tracking,
            'guia_internacional': guia.guia_internacional,
            'fecha_recibido': (guia.fecha_recibido.strftime('%Y-%m-%d %H:%M:%S')  # noqa: E501
                               if guia.fecha_recibido else ''),
            'tipo': 'entrada',
            'timestamp': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'),
            'status': 'YA RECIBIDO',
            'message': (f'La guía {guia.guia_internacional or guia.tracking} ya '  # noqa: E501
                        'fue marcada como RECIBIDO en esta sesión.')
        }
        response_data.update(get_updated_counts())
        return jsonify(response_data)
    else:
        response_data = {
            'tracking': guia.tracking,
            'guia_internacional': guia.guia_internacional,
            'fecha_recibido': (guia.fecha_recibido.strftime('%Y-%m-%d %H:%M:%S')  # noqa: E501
                               if guia.fecha_recibido else ''),
            'tipo': 'entrada',
            'timestamp': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'),
            'status': guia_session_status.status,
            'message': (f'Estado actual de la guía {guia.guia_internacional or guia.tracking}: '  # noqa: E501
                        f'{guia_session_status.status}.')
        }
        response_data.update(get_updated_counts())
        return jsonify(response_data)


@scan_bp.route('/register_unknown', methods=['POST'])
def register_unknown():
    if not g.session:
        return jsonify({'error': 'No hay una sesión activa. '
                                 'Por favor, inicie una sesión primero.'}), 400

    data = request.get_json()
    scanned_code = data.get('code', '').strip()
    scanned_code = sanitize_string(scanned_code)

    if not scanned_code:
        return jsonify({'error': 'No se proporcionó ningún código para registrar.'}), 400

    # Verificar si la guía ya existe (podría haber sido creada por otro escaneo concurrente)
    guia = Guia.query.filter(
        (Guia.tracking == scanned_code) |
        (Guia.guia_internacional == scanned_code)
    ).first()

    if not guia:
        guia = Guia(tracking=scanned_code,
                    guia_internacional=None,  # Asumimos que es tracking si es desconocido  # noqa: E501
                    fecha_recibido=datetime.utcnow())
        db.session.add(guia)
        db.session.flush()  # Para obtener el ID de la guía antes de commitear  # noqa: E501

    guia_session_status = GuiaSessionStatus.query.filter_by(
        session_id=g.session.id, guia_id=guia.id).first()

    if not guia_session_status:
        guia_status = GuiaSessionStatus(session_id=g.session.id,
                                        guia_id=guia.id,
                                        status='NO ESPERADO')
        db.session.add(guia_status)
        db.session.commit()
    else:
        # Si ya existe, y su estado no es 'NO ESPERADO', lo actualizamos
        if guia_session_status.status != 'NO ESPERADO':
            guia_session_status.status = 'NO ESPERADO'
            guia_session_status.timestamp_status_change = datetime.utcnow()
            db.session.commit()

    registro = Registro(guia_id=guia.id, session_id=g.session.id,
                        tipo='entrada')
    db.session.add(registro)
    db.session.commit()

    # Función auxiliar para obtener los conteos actualizados
    def get_updated_counts():
        total_pending = GuiaSessionStatus.query.filter_by(
            session_id=g.session.id).count()
        not_registered = GuiaSessionStatus.query.filter_by(
            session_id=g.session.id, status='NO ESPERADO').count()
        missing_to_scan = GuiaSessionStatus.query.filter_by(
            session_id=g.session.id, status='NO RECIBIDO').count()
        return {
            'total_pending_packages': total_pending,
            'not_registered_packages': not_registered,
            'missing_to_scan_packages': missing_to_scan
        }

    response_data = {
        'message': (f'Paquete desconocido "{scanned_code}" '  # noqa: E501
                    'registrado como NO ESPERADO.'),
        'tracking': guia.tracking,
        'guia_internacional': guia.guia_internacional
    }
    response_data.update(get_updated_counts())
    return jsonify(response_data)
