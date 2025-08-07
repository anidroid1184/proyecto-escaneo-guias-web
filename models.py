from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()


class Persona(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(120), nullable=False)
    documento = db.Column(db.String(50), unique=True, nullable=False)
    codigo_barras = db.Column(db.String(100), unique=True, nullable=False)


class Registro(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    persona_id = db.Column(db.Integer, db.ForeignKey(
        'persona.id'), nullable=False)
    tipo = db.Column(db.String(10), nullable=False)  # 'entrada' o 'salida'
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    persona = db.relationship('Persona', backref='registros')
