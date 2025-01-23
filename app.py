from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, current_user, logout_user
from dotenv import load_dotenv
from utils.currency_converter import converter
import os

load_dotenv()  # Carrega variáveis de ambiente do .env

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-key-change-this')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(80), nullable=False)
    subscriptions = db.relationship('Subscription', backref='user', lazy=True)

class Subscription(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(120), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    currency = db.Column(db.String(3), nullable=False)
    next_payment = db.Column(db.String(10), nullable=False)  # Formato: DD/MM/YYYY
    recurrence = db.Column(db.String(20), nullable=False)    # mensal, anual, semanal

    @property
    def amount_brl(self):
        """Retorna o valor convertido para BRL."""
        if self.currency == 'BRL':
            return self.amount
        converted = converter.convert(self.amount, self.currency, 'BRL')
        if converted is None:  # Se a conversão falhar
            return self.amount
        return converted

    @property
    def monthly_cost(self):
        """Retorna o custo mensal em BRL."""
        amount_brl = self.amount_brl
        if self.recurrence == 'anual':
            return amount_brl / 12
        elif self.recurrence == 'semanal':
            # Considerando média de 52 semanas por ano dividido por 12 meses
            return amount_brl * (52/12)  # Aproximadamente 4.33 semanas por mês
        elif self.recurrence == 'semestral':
            return amount_brl / 6
        else:  # mensal
            return amount_brl

    @property
    def annual_cost(self):
        """Retorna o custo anual em BRL."""
        amount_brl = self.amount_brl
        if self.recurrence == 'mensal':
            return amount_brl * 12
        elif self.recurrence == 'semanal':
            return amount_brl * 52
        elif self.recurrence == 'semestral':
            return amount_brl * 2
        else:  # anual
            return amount_brl

# Configuração do Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Rotas
@app.route('/')
def home():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
        
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and user.password == password:  # Em produção, use hash de senha!
            login_user(user)
            return redirect(url_for('dashboard'))
        flash('Usuário ou senha inválidos')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    try:
        subscriptions = Subscription.query.filter_by(user_id=current_user.id).all()
        total_mensal = sum(sub.monthly_cost for sub in subscriptions)
        return render_template('dashboard.html', 
                            subscriptions=subscriptions, 
                            total_mensal=total_mensal,
                            converter=converter)
    except Exception as e:
        print(f"Erro no dashboard: {e}")
        flash('Erro ao carregar assinaturas. Verifique se a API de conversão está configurada.')
        return redirect(url_for('login'))

@app.route('/subscription/add', methods=['GET', 'POST'])
@login_required
def add_subscription():
    if request.method == 'POST':
        try:
            new_sub = Subscription(
                user_id=current_user.id,
                name=request.form['name'],
                amount=float(request.form['amount']),
                currency=request.form['currency'],
                next_payment=request.form['next_payment'],
                recurrence=request.form['recurrence']
            )
            db.session.add(new_sub)
            db.session.commit()
            return redirect(url_for('dashboard'))
        except Exception as e:
            print(f"Erro ao adicionar assinatura: {e}")
            flash('Erro ao adicionar assinatura. Verifique os dados e tente novamente.')
            return redirect(url_for('add_subscription'))
    return render_template('add_subscription.html')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True) 