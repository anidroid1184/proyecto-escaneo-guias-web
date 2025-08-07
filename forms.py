from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired, Length


class PersonaForm(FlaskForm):
    nombre = StringField('Nombre', validators=[
                         DataRequired(), Length(max=120)])
    documento = StringField('Documento', validators=[
                            DataRequired(), Length(max=50)])
    codigo_barras = StringField('Código de Barras', validators=[
                                DataRequired(), Length(max=100)])
    submit = SubmitField('Guardar y registrar entrada')
