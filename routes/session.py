from flask import Blueprint, redirect, url_for, flash, request, session, g, render_template
from datetime import datetime, date
from models import db, Session, GuiaSessionStatus


session_bp = Blueprint('session', __name__)


@session_bp.before_app_request
def load_current_session():
    today = date.today()
    g.session = Session.query.filter_by(session_date=today).first()

    if not g.session:
        new_session = Session(session_date=today, is_closed=False)
        db.session.add(new_session)
        db.session.commit()
        g.session = new_session


@session_bp.route('/end_session', methods=['GET', 'POST'])
def end_session():
    if not g.session:
        flash('No hay una sesión activa para finalizar.', 'danger')
        return redirect(url_for('main.index'))

    if request.method == 'POST':
        confirmation_date_str = request.form.get('confirmation_date', '').strip()
        try:
            confirmation_date = datetime.strptime(confirmation_date_str,
                                                  '%Y-%m-%d').date()
        except ValueError:
            flash('Formato de fecha incorrecto. Use YYYY-MM-DD.', 'danger')
            return render_template('end_session.html',
                                   current_session=g.session)

        if confirmation_date != g.session.session_date:
            flash('La fecha ingresada no coincide con la fecha de la sesión actual.',
                  'danger')
            return render_template('end_session.html',
                                   current_session=g.session)

        guia_statuses_to_update = GuiaSessionStatus.query.filter_by(
            session_id=g.session.id, status='NO RECIBIDO'
        ).all()

        for gs in guia_statuses_to_update:
            gs.status = 'NO ESCANEADO'
            gs.timestamp_status_change = datetime.utcnow()

        g.session.is_closed = True
        db.session.commit()

        session.pop('session_id', None)
        flash((f'Sesión del {g.session.session_date} finalizada exitosamente. '
               'Guías no recibidas marcadas como "NO ESCANEADO".'), 'success')
        return redirect(url_for('main.index'))

    return render_template('end_session.html', current_session=g.session)
