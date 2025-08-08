from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import Length, ValidationError


class GuiaForm(FlaskForm):
    tracking = StringField('Tracking', validators=[Length(max=120)])
    guia_internacional = StringField('Guía Internacional', validators=[Length(max=50)])
    submit = SubmitField('Guardar y registrar entrada')

    def validate(self):
        if not super().validate():
            return False
        if not (self.tracking.data or self.guia_internacional.data):
            self.tracking.errors.append('Debe proporcionar al menos el Tracking o la Guía Internacional.')
            self.guia_internacional.errors.append('Debe proporcionar al menos el Tracking o la Guía Internacional.')
            return False
        return True
