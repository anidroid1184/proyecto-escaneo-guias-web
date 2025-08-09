from flask import Blueprint, redirect, url_for, flash, request, session, g, render_template
from datetime import datetime, date
from models import db, Session, GuiaSessionStatus
from sqlalchemy.orm import joinedload # Importar joinedload


session_bp = Blueprint('session', __name__)


@session_bp.before_app_request
def load_current_session():
    today = date.today()
    # Cargar la sesión actual y eager-load la relación guia_statuses
    g.session = Session.query.options(joinedload(Session.guia_statuses)).filter_by(session_date=today).first() # noqa: E501

    if not g.session:
        # Antes de crear una nueva sesión, obtener el resumen de la última sesión cerrada
        last_closed_session = Session.query.filter_by(is_closed=True) \
            .order_by(Session.session_date.desc()).first()

        # Almacenar el resumen de la última sesión en g para que sea accesible en index.html
        g.last_session_summary = {
            'session_date': last_closed_session.session_date.strftime('%Y-%m-%d') if last_closed_session else 'N/A', # noqa: E501
            'total_scanned_packages': last_closed_session.total_scanned_packages if last_closed_session else 0, # noqa: E501
            'unknown_packages': last_closed_session.unknown_packages if last_closed_session else 0, # noqa: E501
            'missing_packages': last_closed_session.missing_packages if last_closed_session else 0 # noqa: E501
        } if last_closed_session else None

        new_session = Session(session_date=today, is_closed=False)
        db.session.add(new_session)
        db.session.commit()
        # Recargar la sesión recién creada con la relación cargada
        g.session = Session.query.options(joinedload(Session.guia_statuses)).filter_by(id=new_session.id).first() # noqa: E501


@session_bp.route('/end_session', methods=['GET', 'POST'])
def end_session():
    if not g.session:
        flash('No hay una sesión activa para finalizar.', 'danger')
        return redirect(url_for('main.index'))

    if request.method == 'POST':
        confirmation_date_str = request.form.get(
            'confirmation_date', '').strip()
        try:
            confirmation_date = datetime.strptime(confirmation_date_str,
                                                  '%Y-%m-%d').date()
        except ValueError:
            flash('Formato de fecha incorrecto. Use YYYY-MM-DD.', 'danger')
            return render_template('end_session.html',
                                   current_session=g.session)

        if confirmation_date != g.session.session_date:
            flash('La fecha ingresada no coincide con la fecha de la sesión actual.', # noqa: E501
                  'danger')
            return render_template('end_session.html',
                                   current_session=g.session)

        guia_statuses_to_update = GuiaSessionStatus.query.filter_by(
            session_id=g.session.id, status='NO RECIBIDO'
        ).all()

        for gs in guia_statuses_to_update:
            gs.status = 'NO ESCANEADO'
            gs.timestamp_status_change = datetime.utcnow()

        # Calcular el resumen de la sesión
        total_scanned = GuiaSessionStatus.query.filter_by(
            session_id=g.session.id, status='RECIBIDO').count()
        unknown = GuiaSessionStatus.query.filter_by(
            session_id=g.session.id, status='NO ESPERADO').count()
        missing = GuiaSessionStatus.query.filter_by(
            # Guías que no se recibieron
            session_id=g.session.id, status='NO ESCANEADO').count()

        g.session.total_scanned_packages = total_scanned
        g.session.unknown_packages = unknown
        g.session.missing_packages = missing
        g.session.is_closed = True
        db.session.commit()

        session.pop('session_id', None)
        flash((f'Sesión del {g.session.session_date} finalizada exitosamente. ' # noqa: E501
               'Guías no recibidas marcadas como "NO ESCANEADO".'), 'success')

        # Pasar el resumen a la plantilla end_session.html
        return render_template('end_session.html',
                               current_session=g.session,
                               summary={
                                   'total_scanned': total_scanned,
                                   'unknown': unknown,
                                   'missing': missing
                               })

    return render_template('end_session.html', current_session=g.session)
