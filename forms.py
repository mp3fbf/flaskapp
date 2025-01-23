from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, FloatField, SelectField, DateField
from wtforms.validators import DataRequired, Length, NumberRange, ValidationError
from datetime import datetime

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[
        DataRequired(),
        Length(min=3, max=80)
    ])
    password = PasswordField('Password', validators=[
        DataRequired(),
        Length(min=6)
    ])

class SubscriptionForm(FlaskForm):
    name = StringField('Nome do Serviço', validators=[
        DataRequired(),
        Length(min=2, max=120)
    ])
    
    amount = FloatField('Valor', validators=[
        DataRequired(),
        NumberRange(min=0.01, message="O valor deve ser maior que zero")
    ])
    
    currency = SelectField('Moeda', validators=[DataRequired()], choices=[
        ('BRL', 'Real (BRL)'),
        ('USD', 'Dólar (USD)'),
        ('EUR', 'Euro (EUR)')
    ])
    
    next_payment = DateField('Próximo Pagamento', validators=[DataRequired()])
    
    recurrence = SelectField('Periodicidade', validators=[DataRequired()], choices=[
        ('mensal', 'Mensal'),
        ('anual', 'Anual'),
        ('semanal', 'Semanal'),
        ('semestral', 'Semestral')
    ])
    
    def validate_next_payment(self, field):
        if field.data < datetime.now().date():
            raise ValidationError('A data de pagamento não pode ser no passado') 