from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, current_user, logout_user
from flask_wtf.csrf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
from utils.currency_converter import converter
from forms import LoginForm, SubscriptionForm
from datetime import datetime, timedelta
import os
from collections import defaultdict

load_dotenv()  # Carrega variáveis de ambiente do .env

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-key-change-this')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['WTF_CSRF_TIME_LIMIT'] = 3600  # 1 hora

# Inicialização das extensões
db = SQLAlchemy(app)
csrf = CSRFProtect(app)
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"
)

# Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    subscriptions = db.relationship('Subscription', backref='user', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

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
            return amount_brl / (52/12)  # Corrigido: valor anual dividido por (52/12) semanas
        elif self.recurrence == 'semanal':
            return amount_brl * (52/12)  # Correto: ~4.33 semanas por mês
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
login_manager.login_message = 'Por favor, faça login para acessar esta página.'
login_manager.login_message_category = 'error'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def prepare_chart_data(subscriptions):
    """Prepara os dados para os gráficos."""
    # Distribuição por moeda
    currency_totals = defaultdict(float)
    for sub in subscriptions:
        currency_totals[sub.currency] += sub.amount_brl

    currency_distribution = {
        'labels': list(currency_totals.keys()),
        'values': list(currency_totals.values())
    }

    # Gastos por assinatura (valor mensal)
    subscription_costs = {
        'labels': [],
        'values': []
    }
    
    for sub in subscriptions:
        subscription_costs['labels'].append(sub.name)
        subscription_costs['values'].append(round(sub.monthly_cost, 2))

    # Projeção de gastos para os próximos 12 meses
    today = datetime.now()
    projection_months = []
    projection_values = []
    monthly_total = sum(sub.monthly_cost for sub in subscriptions)

    for i in range(12):
        month = today + timedelta(days=30*i)
        projection_months.append(month.strftime('%b/%Y'))
        projection_values.append(round(monthly_total, 2))

    projection = {
        'labels': projection_months,
        'values': projection_values
    }

    return {
        'currency_distribution': currency_distribution,
        'subscription_costs': subscription_costs,
        'projection': projection
    }

# Rotas
@app.route('/')
def home():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template('login.html', form=LoginForm())  # Renderizar o login diretamente ao invés de redirecionar

@app.route('/login', methods=['GET', 'POST'])
@limiter.limit("5 per minute")
def login():
    # Se já estiver logado, redireciona para o dashboard
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            next_page = request.args.get('next')
            if not next_page or not next_page.startswith('/'):
                next_page = url_for('dashboard')
            return redirect(next_page)
        flash('Usuário ou senha inválidos', 'error')
    return render_template('login.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Você foi desconectado com sucesso.', 'success')
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    try:
        form = SubscriptionForm()
        subscriptions = Subscription.query.filter_by(user_id=current_user.id).all()
        
        # Formatar datas e valores para exibição
        recurrence_map = {
            'monthly': 'Mensal',
            'yearly': 'Anual',
            'weekly': 'Semanal',
            'semiannual': 'Semestral',
            'mensal': 'Mensal',
            'anual': 'Anual',
            'semanal': 'Semanal',
            'semestral': 'Semestral'
        }
        
        # Calcular total mensal usando monthly_cost
        total_mensal = sum(sub.monthly_cost for sub in subscriptions)
        
        # Traduzir recorrência para exibição
        for sub in subscriptions:
            sub.recurrence_label = recurrence_map.get(sub.recurrence, sub.recurrence)
        
        subscription_data = prepare_chart_data(subscriptions)
        
        return render_template('dashboard.html', 
                            subscriptions=subscriptions, 
                            total_mensal=total_mensal,
                            subscription_data=subscription_data,
                            form=form)
    except Exception as e:
        print(f"Erro no dashboard: {e}")
        flash('Erro ao carregar assinaturas. Verifique se a API de conversão está configurada.', 'error')
        return redirect(url_for('login'))

@app.route('/subscription/add', methods=['GET', 'POST'])
@login_required
def add_subscription():
    form = SubscriptionForm()
    if form.validate_on_submit():
        try:
            # Garantir que a recorrência está no formato correto
            recurrence_map = {
                'mensal': 'mensal',
                'anual': 'anual',
                'semanal': 'semanal',
                'semestral': 'semestral'
            }
            
            new_sub = Subscription(
                user_id=current_user.id,
                name=form.name.data,
                amount=form.amount.data,
                currency=form.currency.data,
                next_payment=form.next_payment.data.strftime('%Y-%m-%d'),
                recurrence=recurrence_map.get(form.recurrence.data, 'mensal')  # Valor padrão: mensal
            )
            db.session.add(new_sub)
            db.session.commit()
            flash('Assinatura adicionada com sucesso!', 'success')
            return redirect(url_for('dashboard'))
        except Exception as e:
            print(f"Erro ao adicionar assinatura: {e}")
            flash('Erro ao adicionar assinatura. Verifique os dados e tente novamente.', 'error')
            db.session.rollback()
    return render_template('add_subscription.html', form=form)

@app.route('/subscription/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_subscription(id):
    subscription = Subscription.query.filter_by(id=id, user_id=current_user.id).first_or_404()
    form = SubscriptionForm(obj=subscription)
    
    if form.validate_on_submit():
        try:
            subscription.name = form.name.data
            subscription.amount = form.amount.data
            subscription.currency = form.currency.data
            subscription.next_payment = form.next_payment.data.strftime('%Y-%m-%d')
            subscription.recurrence = form.recurrence.data
            
            db.session.commit()
            flash('Assinatura atualizada com sucesso!', 'success')
            return redirect(url_for('dashboard'))
        except Exception as e:
            print(f"Erro ao atualizar assinatura: {e}")
            flash('Erro ao atualizar assinatura. Verifique os dados e tente novamente.', 'error')
            db.session.rollback()
    
    # Preenche o formulário com os dados atuais
    if request.method == 'GET':
        form.next_payment.data = datetime.strptime(subscription.next_payment, '%Y-%m-%d')
    
    return render_template('edit_subscription.html', form=form, subscription=subscription)

@app.route('/subscription/delete/<int:id>', methods=['POST'])
@login_required
def delete_subscription(id):
    subscription = Subscription.query.filter_by(id=id, user_id=current_user.id).first_or_404()
    try:
        db.session.delete(subscription)
        db.session.commit()
        flash('Assinatura excluída com sucesso!', 'success')
    except Exception as e:
        print(f"Erro ao excluir assinatura: {e}")
        flash('Erro ao excluir assinatura.', 'error')
        db.session.rollback()
    return redirect(url_for('dashboard'))

@app.route('/edit/<int:sub_id>/<field>', methods=['GET', 'POST'])
@login_required
def edit_field(sub_id, field):
    sub = Subscription.query.filter_by(id=sub_id, user_id=current_user.id).first_or_404()
    
    if request.method == 'POST':
        try:
            value = request.form.get(field)
            if field == 'next_payment':
                setattr(sub, field, value)
            elif field == 'amount':
                setattr(sub, field, float(value))
            else:
                setattr(sub, field, value)
            
            db.session.commit()
            return render_template('partials/table_row.html', sub=sub, form=SubscriptionForm())
        except Exception as e:
            print(f"Erro ao atualizar {field}: {e}")
            return "Erro ao atualizar o campo", 400
    
    return render_template('partials/edit_field.html', sub=sub, field=field)

@app.errorhandler(429)
def ratelimit_handler(e):
    flash("Muitas tentativas. Por favor, aguarde alguns minutos.", "error")
    return redirect(url_for('login'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True) 