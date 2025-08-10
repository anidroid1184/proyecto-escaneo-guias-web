from flask import Blueprint, redirect, url_for, flash, request, session, g, render_template
from datetime import datetime, date
from models import db, Session, GuiaSessionStatus
from sqlalchemy.orm import joinedload # Importar joinedload


session_bp = Blueprint('session', __name__)


@session_bp.before_app_request
def load_current_session():
    # Siempre tener una sesión abierta (la de hoy, o crearla si no existe)
    today = date.today()
    session = Session.query.filter_by(session_date=today).first()
    if not session:
        session = Session(session_date=today, is_closed=False)
        db.session.add(session)
        db.session.commit()
    # Si la sesión está cerrada, la reabrimos automáticamente
    if session.is_closed:
        session.is_closed = False
        db.session.commit()
    g.session = session


@session_bp.route('/end_session', methods=['GET', 'POST'])
def end_session():
    if not g.session:
        flash('No hay una sesión activa para finalizar.', 'danger')
        return redirect(url_for('main.index'))

    if request.method == 'POST':
        confirmation_date_str = request.form.get('confirmation_date', '').strip()
        try:
            confirmation_date = datetime.strptime(confirmation_date_str, '%Y-%m-%d').date()
        except ValueError:
            flash('Formato de fecha incorrecto. Use YYYY-MM-DD.', 'danger')
            return render_template('end_session.html', current_session=g.session)

        if confirmation_date != g.session.session_date:
            flash('La fecha ingresada no coincide con la fecha de la sesión actual.', 'danger')
            return render_template('end_session.html', current_session=g.session)

        # Actualizar todos los estados 'NO RECIBIDO' a 'NO ESCANEADO' en la base de datos
        guia_statuses = GuiaSessionStatus.query.filter_by(session_id=g.session.id, status='NO RECIBIDO').all()
        for gs in guia_statuses:
            gs.status = 'NO ESCANEADO'
            gs.timestamp_status_change = datetime.utcnow()

        # Calcular el resumen de la sesión
        total_scanned = GuiaSessionStatus.query.filter_by(session_id=g.session.id, status='RECIBIDO').count()
        unknown = GuiaSessionStatus.query.filter_by(session_id=g.session.id, status='NO ESPERADO').count()
        missing = GuiaSessionStatus.query.filter_by(session_id=g.session.id, status='NO ESCANEADO').count()

        g.session.total_scanned_packages = total_scanned
        g.session.unknown_packages = unknown
        g.session.missing_packages = missing
        g.session.is_closed = True
        db.session.commit()

        session.pop('session_id', None)
        flash((f'Sesión del {g.session.session_date} finalizada exitosamente. '
               'Guías no recibidas marcadas como "NO ESCANEADO".'), 'success')
        return redirect(url_for('records.registros'))

    # GET: mostrar confirmación
    return render_template('end_session.html', current_session=g.session)
