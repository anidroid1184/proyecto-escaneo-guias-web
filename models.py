from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date  # noqa: F401

db = SQLAlchemy()


class Guia(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tracking = db.Column(db.String(120), unique=False, nullable=True) # noqa: E501
    guia_internacional = db.Column(db.String(50), unique=False, nullable=True) # noqa: E501
    fecha_recibido = db.Column(db.DateTime, default=datetime.utcnow)

    # Añadir una restricción para asegurar que al menos uno de los dos campos
    # no sea nulo. Esto se manejará a nivel de aplicación/formulario,
    # pero es una buena práctica tenerlo en cuenta.
    # Para la base de datos, permitimos nulos para flexibilidad.
    # __table_args__ = (db.CheckConstraint('tracking IS NOT NULL OR
    # guia_internacional IS NOT NULL', name='check_tracking_or_guia'),)


class Session(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    session_date = db.Column(db.Date, unique=True, nullable=False)
    is_closed = db.Column(db.Boolean, default=False, nullable=False)
    total_scanned_packages = db.Column(db.Integer, default=0, nullable=False)
    unknown_packages = db.Column(db.Integer, default=0, nullable=False)
    missing_packages = db.Column(db.Integer, default=0, nullable=False)


class GuiaSessionStatus(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('session.id'),
                           nullable=False)
    guia_id = db.Column(db.Integer, db.ForeignKey('guia.id'), nullable=False)
    status = db.Column(db.String(20), nullable=False) # noqa: E501
    # 'RECIBIDO', 'NO RECIBIDO', 'NO ESPERADO', 'NO ESCANEADO'
    timestamp_status_change = db.Column(db.DateTime, default=datetime.utcnow,
                                        nullable=False)

    session = db.relationship('Session', backref='guia_statuses')
    guia = db.relationship('Guia', backref='session_statuses')

    __table_args__ = (db.UniqueConstraint('session_id', 'guia_id',
                                          name='_session_guia_uc'),)


class Registro(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    guia_id = db.Column(db.Integer, db.ForeignKey('guia.id'), nullable=False)
    session_id = db.Column(db.Integer, db.ForeignKey('session.id'),
                           nullable=False)
    tipo = db.Column(db.String(10), nullable=False)  # 'entrada' o 'salida'
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    guia = db.relationship('Guia', backref='registros')
    session = db.relationship('Session', backref='registros')
