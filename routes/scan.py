from flask import Blueprint, request, jsonify, g
from datetime import datetime
from models import db, Guia, Registro, GuiaSessionStatus
from utils import sanitize_string


scan_bp = Blueprint('scan', __name__)


@scan_bp.route('/scan', methods=['POST'])
def scan():
    if not g.session:
        return jsonify({'error': 'No hay una sesión activa. '
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

    if not guia:
        guia = Guia(tracking=scanned_code,
                    guia_internacional=None,
                    fecha_recibido=datetime.utcnow())
        db.session.add(guia)
        db.session.flush()

        guia_status = GuiaSessionStatus(session_id=g.session.id,
                                        guia_id=guia.id,
                                        status='NO ESPERADO')
        db.session.add(guia_status)
        db.session.commit()

        registro = Registro(guia_id=guia.id, session_id=g.session.id,
                            tipo='entrada')
        db.session.add(registro)
        db.session.commit()

        return jsonify({
            'error': 'guia_no_existente',
            'tracking': scanned_code,
            'guia_internacional': None,
            'status': 'NO ESPERADO',
            'message': (f'La guía con código "{scanned_code}" no existe en el '
                        'sistema. Puedes registrarla como nueva.')
        })

    elif not guia_session_status:
        guia_status = GuiaSessionStatus(session_id=g.session.id,
                                        guia_id=guia.id,
                                        status='NO ESPERADO')
        db.session.add(guia_status)
        db.session.commit()

        registro = Registro(guia_id=guia.id, session_id=g.session.id,
                            tipo='entrada')
        db.session.add(registro)
        db.session.commit()

        return jsonify({
            'error': 'guia_no_esperada_en_sesion',
            'tracking': guia.tracking,
            'guia_internacional': guia.guia_internacional,
            'status': 'NO ESPERADO',
            'message': (f'La guía {guia.guia_internacional or guia.tracking} no '
                        'estaba en la lista de guías esperadas para esta sesión.')
        })

    if guia_session_status.status == 'NO RECIBIDO':
        guia_session_status.status = 'RECIBIDO'
        guia_session_status.timestamp_status_change = datetime.utcnow()
        db.session.commit()

        registro = Registro(guia_id=guia.id, session_id=g.session.id,
                            tipo='entrada')
        db.session.add(registro)
        db.session.commit()

        return jsonify({
            'tracking': guia.tracking,
            'guia_internacional': guia.guia_internacional,
            'fecha_recibido': (guia.fecha_recibido.strftime('%Y-%m-%d %H:%M:%S')
                               if guia.fecha_recibido else ''),
            'tipo': 'entrada',
            'timestamp': registro.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            'status': 'RECIBIDO',
            'message': (f'Guía {guia.guia_internacional or guia.tracking} '
                        'registrada exitosamente.')
        })
    elif guia_session_status.status == 'RECIBIDO':
        return jsonify({
            'tracking': guia.tracking,
            'guia_internacional': guia.guia_internacional,
            'fecha_recibido': (guia.fecha_recibido.strftime('%Y-%m-%d %H:%M:%S')
                               if guia.fecha_recibido else ''),
            'tipo': 'entrada',
            'timestamp': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'),
            'status': 'YA RECIBIDO',
            'message': (f'La guía {guia.guia_internacional or guia.tracking} ya '
                        'fue marcada como RECIBIDO en esta sesión.')
        })
    else:
        return jsonify({
            'tracking': guia.tracking,
            'guia_internacional': guia.guia_internacional,
            'fecha_recibido': (guia.fecha_recibido.strftime('%Y-%m-%d %H:%M:%S')
                               if guia.fecha_recibido else ''),
            'tipo': 'entrada',
            'timestamp': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'),
            'status': guia_session_status.status,
            'message': (f'Estado actual de la guía {guia.guia_internacional or guia.tracking}: '
                        f'{guia_session_status.status}.')
        })
