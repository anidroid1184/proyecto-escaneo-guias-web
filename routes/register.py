from flask import Blueprint, render_template, request, redirect, url_for, flash, g
from datetime import datetime
from models import db, Guia, Registro, GuiaSessionStatus
from forms import GuiaForm
from utils import sanitize_string


register_bp = Blueprint('register', __name__)


@register_bp.route('/register', methods=['GET', 'POST'])
def register():
    if not g.session:
        flash('No hay una sesión activa. Por favor, inicie una sesión primero.',
              'warning')
        return redirect(url_for('main.index'))

    form = GuiaForm()
    if request.method == 'GET':
        tracking_arg = request.args.get('tracking')
        guia_internacional_arg = request.args.get('guia_internacional')

        if tracking_arg:
            form.tracking.data = sanitize_string(tracking_arg)
        if guia_internacional_arg:
            form.guia_internacional.data = sanitize_string(guia_internacional_arg)

        # Lógica de intuición si solo se proporciona un código
        if tracking_arg and not guia_internacional_arg:
            if tracking_arg.startswith('BOG'):
                form.guia_internacional.data = sanitize_string(tracking_arg)
                form.tracking.data = None # Limpiar tracking si se intuye que es guia_internacional
        elif guia_internacional_arg and not tracking_arg:
            if guia_internacional_arg.startswith('TBA'):
                form.tracking.data = sanitize_string(guia_internacional_arg)
                form.guia_internacional.data = None # Limpiar guia_internacional si se intuye que es tracking

    if request.method == 'POST' and form.validate():
        tracking = (sanitize_string(form.tracking.data.strip())
                    if form.tracking.data else None)
        guia_internacional = (sanitize_string(form.guia_internacional.data.strip())
                              if form.guia_internacional.data else None)

        if not (tracking or guia_internacional):
            flash('Debe proporcionar al menos el Tracking o la Guía Internacional.',
                  'danger')
            return render_template('register.html', form=form)

        existing_guia = None
        if tracking:
            existing_guia = Guia.query.filter_by(tracking=tracking).first()
        if not existing_guia and guia_internacional:
            existing_guia = Guia.query.filter_by(
                guia_internacional=guia_internacional).first()

        if existing_guia:
            flash((f'La guía con Tracking "{existing_guia.tracking or "N/A"}" o '
                   f'Guía Internacional "{existing_guia.guia_internacional or "N/A"}" '
                   'ya está registrada globalmente. Por favor, use la función de escaneo en la página principal para procesarla.'), 'danger')
            return render_template('register.html', form=form)

        guia = Guia(
            tracking=tracking,
            guia_internacional=guia_internacional,
            fecha_recibido=datetime.utcnow()
        )
        db.session.add(guia)
        db.session.flush()

        guia_status = GuiaSessionStatus(session_id=g.session.id,
                                        guia_id=guia.id,
                                        status='NO ESPERADO')
        db.session.add(guia_status)

        registro = Registro(guia_id=guia.id, session_id=g.session.id,
                            tipo='entrada')
        db.session.add(registro)
        db.session.commit()

        flash('Guía registrada y entrada registrada exitosamente.', 'success')
        return redirect(url_for('main.index'))
    return render_template('register.html', form=form)
