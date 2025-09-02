import os
import sys
from datetime import datetime, date
from flask import Flask, render_template, redirect, url_for, flash, request, get_flashed_messages, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash, generate_password_hash

# Inicializar extensões
db = SQLAlchemy()
login_manager = LoginManager()

# ===== MODELOS DE BANCO DE DADOS =====
class Usuario(db.Model):
    __tablename__ = 'usuarios'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    nome_completo = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120))
    tipo_usuario = db.Column(db.String(20), nullable=False, default='operador')
    ativo = db.Column(db.Boolean, nullable=False, default=True)
    
    def check_password(self, password):
        try:
            if not self.password_hash:
                return False
            return check_password_hash(self.password_hash, password)
        except Exception as e:
            print(f"Erro ao verificar senha: {e}")
            return False
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    @property
    def is_authenticated(self):
        return True
    
    @property
    def is_active(self):
        return self.ativo
    
    @property
    def is_anonymous(self):
        return False
    
    def get_id(self):
        return str(self.id)

class Paciente(db.Model):
    __tablename__ = 'pacientes'
    
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(120), nullable=False)
    cpf = db.Column(db.String(14), unique=True, nullable=False)
    telefone = db.Column(db.String(15), nullable=False)
    data_nascimento = db.Column(db.Date, nullable=False)
    endereco = db.Column(db.Text, nullable=False)
    cep = db.Column(db.String(9))
    cartao_sus = db.Column(db.String(20))
    observacoes = db.Column(db.Text)
    ativo = db.Column(db.Boolean, nullable=False, default=True)
    data_cadastro = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    # Relacionamentos
    agendamentos = db.relationship('Agendamento', backref='paciente', lazy=True)

class Veiculo(db.Model):
    __tablename__ = 'veiculos'
    
    id = db.Column(db.Integer, primary_key=True)
    placa = db.Column(db.String(8), unique=True, nullable=False)
    marca = db.Column(db.String(50), nullable=False)
    modelo = db.Column(db.String(50), nullable=False)
    ano = db.Column(db.Integer, nullable=False)
    cor = db.Column(db.String(30))
    tipo = db.Column(db.String(30), nullable=False)
    capacidade = db.Column(db.Integer)
    adaptado = db.Column(db.Boolean, nullable=False, default=False)
    observacoes = db.Column(db.Text)
    ativo = db.Column(db.Boolean, nullable=False, default=True)
    data_cadastro = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    # Relacionamentos
    agendamentos = db.relationship('Agendamento', backref='veiculo', lazy=True)

class Motorista(db.Model):
    __tablename__ = 'motoristas'
    
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(120), nullable=False)
    cpf = db.Column(db.String(14), unique=True, nullable=False)
    telefone = db.Column(db.String(15), nullable=False)
    data_nascimento = db.Column(db.Date, nullable=False)
    cnh = db.Column(db.String(20), unique=True, nullable=False)
    categoria_cnh = db.Column(db.String(2), nullable=False)
    vencimento_cnh = db.Column(db.Date, nullable=False)
    endereco = db.Column(db.Text)
    status = db.Column(db.String(20), nullable=False, default='ativo')
    observacoes = db.Column(db.Text)
    data_cadastro = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    # Relacionamentos
    agendamentos = db.relationship('Agendamento', backref='motorista', lazy=True)

class Agendamento(db.Model):
    __tablename__ = 'agendamentos'
    
    id = db.Column(db.Integer, primary_key=True)
    paciente_id = db.Column(db.Integer, db.ForeignKey('pacientes.id'), nullable=False)
    veiculo_id = db.Column(db.Integer, db.ForeignKey('veiculos.id'))
    motorista_id = db.Column(db.Integer, db.ForeignKey('motoristas.id'))
    tipo_transporte = db.Column(db.String(30), nullable=False)
    data = db.Column(db.Date, nullable=False)
    hora = db.Column(db.Time, nullable=False)
    origem = db.Column(db.Text, nullable=False)
    destino = db.Column(db.Text, nullable=False)
    observacoes = db.Column(db.Text)
    status = db.Column(db.String(20), nullable=False, default='agendado')
    data_cadastro = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

@login_manager.user_loader
def load_user(user_id):
    try:
        return Usuario.query.get(int(user_id))
    except:
        return None

def verificar_e_criar_banco():
    """Verifica se o banco existe e cria se necessário"""
    basedir = os.path.abspath(os.path.dirname(__file__))
    db_dir = os.path.join(basedir, 'db')
    db_path = os.path.join(db_dir, 'transporte_pacientes.db')
    
    print(f"🔍 Verificando banco em: {db_path}")
    
    # Criar diretório se não existir
    if not os.path.exists(db_dir):
        print(f"📁 Criando diretório: {db_dir}")
        os.makedirs(db_dir, exist_ok=True)
    
    # Verificar se o banco existe
    if not os.path.exists(db_path):
        print("❌ Banco de dados não encontrado. Criando automaticamente...")
        criar_banco_e_usuario()
    else:
        print(f"✅ Banco de dados encontrado: {db_path}")
        # Verificar se o usuário admin existe e tem hash válido
        verificar_usuario_admin()
    
    return db_path

def criar_banco_e_usuario():
    """Cria o banco e o usuário administrador"""
    try:
        # Criar as tabelas
        db.create_all()
        print("✅ Tabelas criadas no banco de dados")
        
        # Criar usuário admin
        admin = Usuario(
            username='admin',
            nome_completo='Administrador do Sistema',
            email='admin@cosmopolis.sp.gov.br',
            tipo_usuario='administrador',
            ativo=True
        )
        admin.set_password('admin123')
        
        db.session.add(admin)
        db.session.commit()
        print("✅ Usuário administrador criado: admin / admin123")
        
    except Exception as e:
        print(f"❌ Erro ao criar banco: {e}")
        db.session.rollback()

def verificar_usuario_admin():
    """Verifica se o usuário admin existe e tem hash válido"""
    try:
        admin = Usuario.query.filter_by(username='admin').first()
        if not admin:
            print("❌ Usuário admin não encontrado. Criando...")
            criar_banco_e_usuario()
        elif not admin.password_hash or len(admin.password_hash) < 10:
            print("❌ Hash do usuário admin inválido. Corrigindo...")
            admin.set_password('admin123')
            db.session.commit()
            print("✅ Hash do usuário admin corrigido")
        else:
            print("✅ Usuário admin válido encontrado")
    except Exception as e:
        print(f"❌ Erro ao verificar usuário admin: {e}")

def gerar_layout_base(titulo, conteudo, ativo=""):
    """Gera o layout base para todas as páginas"""
    return f'''
    <html>
    <head>
        <title>{titulo} - Sistema de Transporte</title>
        <style>
            :root {{
                /* Paleta de cores do sistema de saúde */
                --color-100: #ffffff;
                --color-95: #ebf9f9;
                --color-90: #d8f3f2;
                --color-85: #c4edec;
                --color-80: #b1e7e5;
                --color-75: #9de1df;
                --color-70: #8adbd8;
                --color-65: #76d5d2;
                --color-60: #63cfcb;
                --color-55: #4fc9c4;
                --color-50: #3cc3bf;
                --color-45: #36b0ac;
                --color-40: #309c98;
                --color-35: #2a8985;
                --color-30: #247572;
                --color-25: #1e625f;
                --color-20: #184e4c;
                --color-15: #123b39;
                --color-10: #0c2726;
                --color-5: #061413;
                --color-0: #000000;
                
                /* Cores do template wt_health_center_free */
                --primary-color: #4fc9c4;
                --primary-dark: #43aca7;
                --primary-hover: #3c9b96;
                --secondary-color: #6d7a8c;
                --text-color: #3f485d;
                --border-color: #e5e5e5;
                --success-color: #79b24a;
                --warning-color: #f2823c;
                --danger-color: #e81d51;
                --info-color: #91ceff;
                --light-color: #2a303b;
                --dark-color: #2a303b;
                --gray-color: #6d7a8c;
                --input-focus: #4fc9c4;
                --input-focus-shadow: rgba(79, 201, 196, 0.25);
            }}
            
            body {{ font-family: Arial, sans-serif; margin: 0; padding: 0; background: var(--color-95); }}
            .header {{ background: linear-gradient(135deg, var(--primary-color), var(--primary-dark)); color: var(--color-100); padding: 1rem 2rem; }}
            .header h1 {{ margin: 0; }}
            .header .user-info {{ float: right; }}
            .nav {{ background: var(--color-100); padding: 0.5rem 2rem; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
            .nav a {{ color: var(--text-color); text-decoration: none; margin-right: 2rem; padding: 0.5rem 1rem; border-radius: 0.25rem; transition: all 0.3s ease; }}
            .nav a:hover {{ background: var(--color-90); color: var(--primary-color); }}
            .nav a.active {{ background: var(--primary-color); color: var(--color-100); }}
            .container {{ padding: 2rem; max-width: 1200px; margin: 0 auto; }}
            .page-header {{ margin-bottom: 2rem; }}
            .page-header h2 {{ color: var(--primary-color); margin: 0 0 0.5rem 0; }}
            .page-header p {{ color: var(--gray-color); margin: 0; }}
            .card {{ background: var(--color-100); padding: 2rem; border-radius: 1rem; box-shadow: 0 0.125rem 0.25rem rgba(0,0,0,0.075); border-left: 4px solid var(--primary-color); margin-bottom: 1rem; }}
            .btn {{ padding: 0.75rem 1.5rem; background: var(--primary-color); color: var(--color-100); border: none; border-radius: 0.5rem; cursor: pointer; text-decoration: none; display: inline-block; transition: background-color 0.3s ease; }}
            .btn:hover {{ background: var(--primary-dark); }}
            .btn-secondary {{ background: var(--secondary-color); }}
            .btn-secondary:hover {{ background: var(--gray-color); }}
            .btn-success {{ background: var(--success-color); }}
            .btn-success:hover {{ background: #6a9d3e; }}
            .btn-warning {{ background: var(--warning-color); }}
            .btn-warning:hover {{ background: #e6762f; }}
            .logout {{ background: var(--danger-color); color: var(--color-100); padding: 0.5rem 1rem; border: none; border-radius: 0.5rem; cursor: pointer; text-decoration: none; transition: background-color 0.3s ease; }}
            .logout:hover {{ background: #c81841; }}
            .coming-soon {{ text-align: center; padding: 4rem 2rem; }}
            .coming-soon .icon {{ font-size: 4rem; margin-bottom: 1rem; color: var(--primary-color); }}
            .coming-soon h3 {{ color: var(--text-color); margin-bottom: 1rem; }}
            .coming-soon p {{ color: var(--gray-color); }}
            .form-group {{ margin-bottom: 1rem; }}
            .form-group label {{ display: block; margin-bottom: 0.5rem; color: var(--text-color); font-weight: 600; }}
            .form-group input, .form-group select, .form-group textarea {{ width: 100%; padding: 0.75rem; border: 2px solid var(--border-color); border-radius: 0.5rem; font-size: 1rem; box-sizing: border-box; }}
            .form-group input:focus, .form-group select:focus, .form-group textarea:focus {{ border-color: var(--input-focus); outline: none; box-shadow: 0 0 0 3px var(--input-focus-shadow); }}
            .form-row {{ display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; }}
            .breadcrumb {{ margin-bottom: 1rem; color: var(--gray-color); }}
            .breadcrumb a {{ color: var(--primary-color); text-decoration: none; }}
            .breadcrumb a:hover {{ text-decoration: underline; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🚑 Sistema de Transporte de Pacientes</h1>
            <div class="user-info">
                Bem-vindo, {current_user.nome_completo}! 
                <a href="{url_for('logout')}" class="logout">Sair</a>
            </div>
            <div style="clear: both;"></div>
        </div>
        
        <div class="nav">
            <a href="{url_for('dashboard')}" class="{'active' if ativo == 'dashboard' else ''}">🏠 Dashboard</a>
            <a href="{url_for('pacientes')}" class="{'active' if ativo == 'pacientes' else ''}">👥 Pacientes</a>
            <a href="{url_for('veiculos')}" class="{'active' if ativo == 'veiculos' else ''}">🚗 Veículos</a>
            <a href="{url_for('motoristas')}" class="{'active' if ativo == 'motoristas' else ''}">👨‍💼 Motoristas</a>
            <a href="{url_for('agendamentos')}" class="{'active' if ativo == 'agendamentos' else ''}">📅 Agendamentos</a>
        </div>
        
        <div class="container">
            {conteudo}
        </div>
    </body>
    </html>
    '''

def _gerar_agendamentos_html(agendamentos_lista):
    """Função auxiliar para gerar HTML dos agendamentos"""
    if not agendamentos_lista:
        return '''
            <div class="text-center py-4">
                <i class="bi bi-calendar-x text-muted" style="font-size: 3rem;"></i>
                <p class="text-muted mt-3 mb-0">Nenhum agendamento para hoje</p>
                <a href="/agendamentos/novo" class="btn btn-primary mt-2">
                    <i class="bi bi-plus-circle me-1"></i>
                    Criar Agendamento
                </a>
            </div>
        '''
    
    html = ""
    for agendamento in agendamentos_lista:
        status_class = {
            'confirmado': 'success',
            'agendado': 'warning', 
            'em_andamento': 'primary',
            'concluido': 'secondary'
        }.get(agendamento.status, 'secondary')
        
        html += f'''
            <div class="schedule-item">
                <div class="row align-items-center">
                    <div class="col-md-2">
                        <div class="schedule-time">{agendamento.hora.strftime('%H:%M')}</div>
                    </div>
                    <div class="col-md-4">
                        <div class="fw-semibold">{agendamento.paciente.nome}</div>
                        <div class="text-muted small">{agendamento.paciente.telefone}</div>
                    </div>
                    <div class="col-md-4">
                        <div class="text-muted small">
                            <strong>Destino:</strong><br>
                            {agendamento.destino[:40]}{'...' if len(agendamento.destino) > 40 else ''}
                        </div>
                    </div>
                    <div class="col-md-2">
                        <span class="badge bg-{status_class}">
                            {agendamento.status.replace('_', ' ').title()}
                        </span>
                    </div>
                </div>
            </div>
        '''
    
    return html

def create_app():
    global app
    app = Flask(__name__)
    
    # Configuração com caminho absoluto
    basedir = os.path.abspath(os.path.dirname(__file__))
    db_path = os.path.join(basedir, 'db', 'transporte_pacientes.db')
    
    app.config['SECRET_KEY'] = 'cosmopolis_sistema_transporte_2024'
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Criar outros diretórios necessários
    for dir_name in ['uploads', 'relatorios', 'static/css', 'static/js', 'static/img']:
        dir_path = os.path.join(basedir, dir_name)
        os.makedirs(dir_path, exist_ok=True)
    
    # Inicializar extensões
    db.init_app(app)
    login_manager.init_app(app)
    
    # Configurar Login Manager
    login_manager.login_view = 'login'
    login_manager.login_message = 'Por favor, faça login para acessar esta página.'
    login_manager.login_message_category = 'info'
    
    # Verificar e criar banco dentro do contexto da aplicação
    with app.app_context():
        verificar_e_criar_banco()
    
    # Rotas
    @app.route('/')
    def index():
        if current_user.is_authenticated:
            return redirect(url_for('dashboard'))
        return redirect(url_for('login'))
    
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == 'POST':
            username = request.form.get('username', '').strip()
            password = request.form.get('password', '')
            
            if not username or not password:
                flash('Por favor, preencha usuário e senha!', 'error')
                return redirect(url_for('login'))
            
            try:
                user = Usuario.query.filter_by(username=username).first()
                print(f"🔍 Usuário encontrado: {user is not None}")
                
                if user:
                    print(f"🔐 Verificando senha para usuário: {user.username}")
                    print(f"🔐 Hash armazenado: {user.password_hash[:20]}..." if user.password_hash else "🔐 Hash vazio!")
                    
                    if user.check_password(password):
                        login_user(user)
                        session.pop('_flashes', None)
                        flash('Login realizado com sucesso!', 'success')
                        print(f"✅ Login bem-sucedido para: {user.username}")
                        return redirect(url_for('dashboard'))
                    else:
                        flash('Senha incorreta!', 'error')
                        print(f"❌ Senha incorreta para: {user.username}")
                else:
                    flash('Usuário não encontrado!', 'error')
                    print(f"❌ Usuário não encontrado: {username}")
                    
            except Exception as e:
                flash(f'Erro ao fazer login: {str(e)}', 'error')
                print(f"❌ Erro de login: {e}")
        
        # Gerar alertas de mensagens flash
        messages_html = ""
        for category, message in get_flashed_messages(with_categories=True):
            alert_class = "alert-error" if category == "error" else "alert-success"
            messages_html += f'<div class="alert {alert_class}">{message}</div>'
        
        return f'''
        <html>
        <head>
            <title>Login - Sistema de Transporte</title>
            <style>
                :root {{
                    --color-100: #ffffff;
                    --color-95: #ebf9f9;
                    --primary-color: #4fc9c4;
                    --primary-dark: #43aca7;
                    --primary-hover: #3c9b96;
                    --text-color: #3f485d;
                    --border-color: #e5e5e5;
                    --success-color: #79b24a;
                    --danger-color: #e81d51;
                    --gray-color: #6d7a8c;
                    --input-focus: #4fc9c4;
                    --input-focus-shadow: rgba(79, 201, 196, 0.25);
                }}
                
                body {{ font-family: Arial, sans-serif; margin: 0; padding: 0; background: linear-gradient(135deg, var(--primary-color), var(--primary-dark)); min-height: 100vh; display: flex; align-items: center; justify-content: center; }}
                .login-container {{ background: var(--color-100); padding: 2rem; border-radius: 1rem; box-shadow: 0 0.5rem 2rem rgba(0,0,0,0.2); max-width: 400px; width: 100%; }}
                .header {{ text-align: center; margin-bottom: 2rem; }}
                .header h1 {{ color: var(--primary-color); margin: 0; }}
                .header p {{ color: var(--gray-color); margin: 0.5rem 0 0 0; }}
                .form-group {{ margin-bottom: 1rem; }}
                .form-group label {{ display: block; margin-bottom: 0.5rem; color: var(--text-color); font-weight: 600; }}
                .form-group input {{ width: 100%; padding: 0.75rem; border: 2px solid var(--border-color); border-radius: 0.5rem; font-size: 1rem; box-sizing: border-box; }}
                .form-group input:focus {{ border-color: var(--input-focus); outline: none; box-shadow: 0 0 0 3px var(--input-focus-shadow); }}
                .btn {{ width: 100%; padding: 0.75rem; background: var(--primary-color); color: var(--color-100); border: none; border-radius: 0.5rem; font-size: 1rem; cursor: pointer; transition: background-color 0.3s ease; }}
                .btn:hover {{ background: var(--primary-dark); }}
                .btn:active {{ background: var(--primary-hover); }}
                .alert {{ padding: 0.75rem; margin-bottom: 1rem; border-radius: 0.5rem; }}
                .alert-error {{ background: rgba(232, 29, 81, 0.1); color: var(--danger-color); border: 1px solid var(--danger-color); }}
                .alert-success {{ background: rgba(121, 178, 74, 0.1); color: var(--success-color); border: 1px solid var(--success-color); }}
                .default-info {{ background: var(--color-95); padding: 1rem; border-radius: 0.5rem; margin-top: 1rem; font-size: 0.875rem; border-left: 4px solid var(--primary-color); }}
            </style>
        </head>
        <body>
            <div class="login-container">
                <div class="header">
                    <h1>🚑 Sistema de Transporte</h1>
                    <p>Prefeitura Municipal de Cosmópolis</p>
                </div>
                
                {messages_html}
                
                <form method="POST">
                    <div class="form-group">
                        <label for="username">Usuário:</label>
                        <input type="text" id="username" name="username" required>
                    </div>
                    
                    <div class="form-group">
                        <label for="password">Senha:</label>
                        <input type="password" id="password" name="password" required>
                    </div>
                    
                    <button type="submit" class="btn">Entrar</button>
                </form>
                
                <div class="default-info">
                    <strong>💡 Acesso Padrão:</strong><br>
                    <strong>Usuário:</strong> admin<br>
                    <strong>Senha:</strong> admin123
                </div>
            </div>
        </body>
        </html>
        '''
    
    # ===== ROTAS DO DASHBOARD =====
    @app.route('/dashboard')
    @login_required
    def dashboard():
        # Buscar dados reais do banco
        hoje = date.today()
        total_pacientes = Paciente.query.filter_by(ativo=True).count()
        total_veiculos = Veiculo.query.filter_by(ativo=True).count()
        total_motoristas = Motorista.query.filter_by(status='ativo').count()
        agendamentos_hoje = Agendamento.query.filter_by(data=hoje).count()
        
        # Agendamentos de hoje para exibir
        agendamentos_lista = Agendamento.query.filter_by(data=hoje).order_by(Agendamento.hora).all()
        
        return f'''
        <!DOCTYPE html>
        <html lang="pt-BR">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Dashboard - Sistema de Transporte</title>
            
            <!-- Bootstrap 5 -->
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
            <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.0/font/bootstrap-icons.css" rel="stylesheet">
            
            <style>
                :root {{
                    --primary-color: #4fc9c4;
                    --primary-dark: #43aca7;
                    --success-color: #28a745;
                    --warning-color: #ffc107;
                    --info-color: #17a2b8;
                    --danger-color: #dc3545;
                }}
                
                body {{
                    background: #f8f9fa;
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                }}
                
                .stats-card {{
                    background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
                    border: none;
                    border-radius: 1rem;
                    box-shadow: 0 0.125rem 0.25rem rgba(0,0,0,0.075);
                    transition: all 0.3s ease;
                    position: relative;
                    overflow: hidden;
                    cursor: pointer;
                }}
                
                .stats-card:hover {{
                    transform: translateY(-5px);
                    box-shadow: 0 0.5rem 1rem rgba(0,0,0,0.15);
                }}
                
                .stats-card::before {{
                    content: '';
                    position: absolute;
                    top: 0;
                    left: 0;
                    right: 0;
                    height: 4px;
                }}
                
                .card-primary::before {{ background: var(--primary-color); }}
                .card-success::before {{ background: var(--success-color); }}
                .card-warning::before {{ background: var(--warning-color); }}
                .card-info::before {{ background: var(--info-color); }}
                
                .stats-icon {{
                    width: 60px;
                    height: 60px;
                    border-radius: 50%;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    font-size: 1.5rem;
                    color: white;
                    margin-bottom: 1rem;
                }}
                
                .icon-primary {{ background: linear-gradient(135deg, var(--primary-color), #4a49c4); }}
                .icon-success {{ background: linear-gradient(135deg, var(--success-color), #1e7e34); }}
                .icon-warning {{ background: linear-gradient(135deg, var(--warning-color), #e0a800); }}
                .icon-info {{ background: linear-gradient(135deg, var(--info-color), #138496); }}
                
                .stats-number {{
                    font-size: 2.5rem;
                    font-weight: 700;
                    color: #333;
                    margin: 0;
                    line-height: 1;
                }}
                
                .stats-label {{
                    color: #6c757d;
                    font-weight: 500;
                    font-size: 0.875rem;
                    margin-bottom: 0.5rem;
                }}
                
                .quick-action {{
                    background: white;
                    border: 2px solid #e9ecef;
                    border-radius: 0.75rem;
                    padding: 1.5rem;
                    text-decoration: none;
                    color: #333;
                    transition: all 0.3s ease;
                    display: block;
                    text-align: center;
                }}
                
                .quick-action:hover {{
                    border-color: var(--primary-color);
                    transform: translateY(-3px);
                    box-shadow: 0 0.25rem 0.5rem rgba(0,0,0,0.1);
                    color: var(--primary-color);
                    text-decoration: none;
                }}
                
                .quick-action i {{
                    font-size: 2rem;
                    margin-bottom: 0.5rem;
                    display: block;
                    color: var(--primary-color);
                }}
                
                .welcome-banner {{
                    background: linear-gradient(135deg, var(--primary-color), #4a49c4);
                    color: white;
                    border-radius: 1rem;
                    padding: 2rem;
                    margin-bottom: 2rem;
                    position: relative;
                    overflow: hidden;
                }}
                
                .schedule-item {{
                    border: 1px solid #dee2e6;
                    border-radius: 0.5rem;
                    padding: 1rem;
                    margin-bottom: 0.75rem;
                    background: white;
                    transition: all 0.3s ease;
                }}
                
                .schedule-item:hover {{
                    border-color: var(--primary-color);
                    box-shadow: 0 0.125rem 0.25rem rgba(0,0,0,0.075);
                }}
                
                .schedule-time {{
                    font-weight: 600;
                    color: var(--primary-color);
                    font-size: 1.1rem;
                }}
                
                .navbar {{
                    background: linear-gradient(135deg, var(--primary-color), var(--primary-dark));
                    border: none;
                }}
                
                .navbar-brand, .nav-link {{
                    color: white !important;
                }}
                
                .fade-in-up {{
                    animation: fadeInUp 0.6s ease-out;
                }}
                
                @keyframes fadeInUp {{
                    from {{
                        opacity: 0;
                        transform: translateY(20px);
                    }}
                    to {{
                        opacity: 1;
                        transform: translateY(0);
                    }}
                }}
                
                @media (max-width: 768px) {{
                    .stats-number {{ font-size: 2rem; }}
                    .stats-icon {{ width: 50px; height: 50px; font-size: 1.25rem; }}
                    .welcome-banner {{ padding: 1.5rem; }}
                }}
            </style>
        </head>
        <body>
            
            <!-- Navbar -->
            <nav class="navbar navbar-expand-lg">
                <div class="container-fluid">
                    <span class="navbar-brand">🚑 Sistema de Transporte de Pacientes</span>
                    <div class="d-flex align-items-center text-white">
                        <span class="me-3">Bem-vindo, {current_user.nome_completo}!</span>
                        <a href="{url_for('logout')}" class="btn btn-outline-light btn-sm">Sair</a>
                    </div>
                </div>
            </nav>
            
            <div class="container-fluid mt-4">
                
                <!-- Welcome Banner -->
                <div class="welcome-banner fade-in-up">
                    <div class="row align-items-center">
                        <div class="col-md-8">
                            <h1 class="h3 mb-2">Bom dia! 🌅</h1>
                            <p class="mb-0 opacity-90">Sistema de Transporte de Pacientes - Cosmópolis/SP</p>
                        </div>
                        <div class="col-md-4 text-end">
                            <span class="h4" id="currentTime">{datetime.now().strftime('%H:%M')}</span>
                            <br><small class="opacity-75">Última atualização</small>
                        </div>
                    </div>
                </div>
                
                <!-- Statistics Cards -->
                <div class="row g-4 mb-4">
                    <div class="col-xl-3 col-md-6">
                        <div class="card stats-card card-primary fade-in-up" onclick="window.location.href='{url_for('agendamentos')}'">
                            <div class="card-body">
                                <div class="d-flex align-items-center">
                                    <div class="stats-icon icon-primary">
                                        <i class="bi bi-calendar-check"></i>
                                    </div>
                                    <div class="flex-grow-1">
                                        <div class="stats-label">Agendamentos Hoje</div>
                                        <div class="stats-number" id="agendamentosHoje">{agendamentos_hoje}</div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="col-xl-3 col-md-6">
                        <div class="card stats-card card-success fade-in-up" onclick="window.location.href='{url_for('pacientes')}'" style="animation-delay: 0.1s">
                            <div class="card-body">
                                <div class="d-flex align-items-center">
                                    <div class="stats-icon icon-success">
                                        <i class="bi bi-people"></i>
                                    </div>
                                    <div class="flex-grow-1">
                                        <div class="stats-label">Pacientes Ativos</div>
                                        <div class="stats-number" id="pacientesAtivos">{total_pacientes}</div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="col-xl-3 col-md-6">
                        <div class="card stats-card card-info fade-in-up" onclick="window.location.href='{url_for('motoristas')}'" style="animation-delay: 0.2s">
                            <div class="card-body">
                                <div class="d-flex align-items-center">
                                    <div class="stats-icon icon-info">
                                        <i class="bi bi-person-badge"></i>
                                    </div>
                                    <div class="flex-grow-1">
                                        <div class="stats-label">Motoristas Disponíveis</div>
                                        <div class="stats-number" id="motoristasDisponiveis">{total_motoristas}</div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="col-xl-3 col-md-6">
                        <div class="card stats-card card-warning fade-in-up" onclick="window.location.href='{url_for('veiculos')}'" style="animation-delay: 0.3s">
                            <div class="card-body">
                                <div class="d-flex align-items-center">
                                    <div class="stats-icon icon-warning">
                                        <i class="bi bi-truck"></i>
                                    </div>
                                    <div class="flex-grow-1">
                                        <div class="stats-label">Veículos Disponíveis</div>
                                        <div class="stats-number" id="veiculosDisponiveis">{total_veiculos}</div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="row g-4">
                    <!-- Main Content -->
                    <div class="col-xl-8">
                        
                        <!-- Quick Actions -->
                        <div class="card mb-4 fade-in-up" style="animation-delay: 0.4s">
                            <div class="card-header">
                                <h5 class="card-title mb-0">
                                    <i class="bi bi-lightning-fill me-2"></i>
                                    Ações Rápidas
                                </h5>
                            </div>
                            <div class="card-body">
                                <div class="row g-3">
                                    <div class="col-md-3 col-6">
                                        <a href="{url_for('agendamentos_novo')}" class="quick-action">
                                            <i class="bi bi-plus-circle"></i>
                                            <div class="fw-semibold">Novo Agendamento</div>
                                        </a>
                                    </div>
                                    <div class="col-md-3 col-6">
                                        <a href="{url_for('pacientes_cadastrar')}" class="quick-action">
                                            <i class="bi bi-person-plus"></i>
                                            <div class="fw-semibold">Novo Paciente</div>
                                        </a>
                                    </div>
                                    <div class="col-md-3 col-6">
                                        <a href="{url_for('agendamentos')}" class="quick-action">
                                            <i class="bi bi-calendar3"></i>
                                            <div class="fw-semibold">Ver Agenda</div>
                                        </a>
                                    </div>
                                    <div class="col-md-3 col-6">
                                        <a href="#" class="quick-action" onclick="refreshDashboard()">
                                            <i class="bi bi-arrow-clockwise"></i>
                                            <div class="fw-semibold">Atualizar</div>
                                        </a>
                                    </div>
                                </div>
                            </div>
                        </div>
                        
                        <!-- Today's Schedule -->
                        <div class="card fade-in-up" style="animation-delay: 0.5s">
                            <div class="card-header d-flex justify-content-between align-items-center">
                                <h5 class="card-title mb-0">
                                    <i class="bi bi-calendar-day me-2"></i>
                                    Agendamentos de Hoje
                                </h5>
                                <a href="{url_for('agendamentos')}" class="btn btn-sm btn-outline-primary">Ver Todos</a>
                            </div>
                            <div class="card-body">
                                <div id="todaySchedule">
                                    {_gerar_agendamentos_html(agendamentos_lista)}
                                </div>
                            </div>
                        </div>
                        
                    </div>
                    
                    <!-- Sidebar -->
                    <div class="col-xl-4">
                        
                        <!-- Navigation Menu -->
                        <div class="card mb-4 fade-in-up" style="animation-delay: 0.6s">
                            <div class="card-header">
                                <h5 class="card-title mb-0">
                                    <i class="bi bi-list me-2"></i>
                                    Menu Principal
                                </h5>
                            </div>
                            <div class="list-group list-group-flush">
                                <a href="{url_for('pacientes')}" class="list-group-item list-group-item-action">
                                    <i class="bi bi-people me-2"></i>Pacientes
                                </a>
                                <a href="{url_for('veiculos')}" class="list-group-item list-group-item-action">
                                    <i class="bi bi-truck me-2"></i>Veículos
                                </a>
                                <a href="{url_for('motoristas')}" class="list-group-item list-group-item-action">
                                    <i class="bi bi-person-badge me-2"></i>Motoristas
                                </a>
                                <a href="{url_for('agendamentos')}" class="list-group-item list-group-item-action">
                                    <i class="bi bi-calendar-event me-2"></i>Agendamentos
                                </a>
                            </div>
                        </div>
                        
                        <!-- System Status -->
                        <div class="card fade-in-up" style="animation-delay: 0.7s">
                            <div class="card-header">
                                <h5 class="card-title mb-0">
                                    <i class="bi bi-info-circle me-2"></i>
                                    Status do Sistema
                                </h5>
                            </div>
                            <div class="card-body">
                                <div class="d-flex justify-content-between align-items-center mb-2">
                                    <span>Sistema:</span>
                                    <span class="badge bg-success">Online</span>
                                </div>
                                <div class="d-flex justify-content-between align-items-center mb-2">
                                    <span>Banco de Dados:</span>
                                    <span class="badge bg-success">Conectado</span>
                                </div>
                                <div class="d-flex justify-content-between align-items-center">
                                    <span>Última Atualização:</span>
                                    <span class="text-muted small" id="lastUpdate">{datetime.now().strftime('%H:%M:%S')}</span>
                                </div>
                            </div>
                        </div>
                        
                    </div>
                </div>
                
            </div>
            
            <!-- Scripts -->
            <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
            <script>
                // Atualizar relógio
                function updateTime() {{
                    const now = new Date();
                    const timeString = now.toLocaleTimeString('pt-BR', {{ 
                        hour: '2-digit', 
                        minute: '2-digit' 
                    }});
                    document.getElementById('currentTime').textContent = timeString;
                    document.getElementById('lastUpdate').textContent = now.toLocaleTimeString('pt-BR');
                }}
                
                // Refresh automático dos dados
                function refreshDashboard() {{
                    fetch('/dashboard_api')
                        .then(response => response.json())
                        .then(data => {{
                            // Atualizar contadores
                            document.getElementById('agendamentosHoje').textContent = data.stats.agendamentos_hoje;
                            document.getElementById('pacientesAtivos').textContent = data.stats.pacientes_ativos;
                            document.getElementById('motoristasDisponiveis').textContent = data.stats.motoristas_disponiveis;
                            document.getElementById('veiculosDisponiveis').textContent = data.stats.veiculos_disponiveis;
                            
                            // Atualizar agendamentos
                            updateTodaySchedule(data.agendamentos_hoje);
                            
                            // Atualizar timestamp
                            updateTime();
                        }})
                        .catch(error => console.error('Erro ao atualizar:', error));
                }}
                
                function updateTodaySchedule(agendamentos) {{
                    const container = document.getElementById('todaySchedule');
                    if (!agendamentos || agendamentos.length === 0) {{
                        container.innerHTML = `
                            <div class="text-center py-4">
                                <i class="bi bi-calendar-x text-muted" style="font-size: 3rem;"></i>
                                <p class="text-muted mt-3 mb-0">Nenhum agendamento para hoje</p>
                            </div>
                        `;
                        return;
                    }}
                    
                    let html = '';
                    agendamentos.forEach(ag => {{
                        const statusClass = {{
                            'confirmado': 'success',
                            'agendado': 'warning',
                            'em_andamento': 'primary',
                            'concluido': 'secondary'
                        }}[ag.status] || 'secondary';
                        
                        html += `
                            <div class="schedule-item">
                                <div class="row align-items-center">
                                    <div class="col-md-2">
                                        <div class="schedule-time">${{ag.horario_saida}}</div>
                                    </div>
                                    <div class="col-md-4">
                                        <div class="fw-semibold">${{ag.paciente_nome}}</div>
                                        <div class="text-muted small">${{ag.paciente_telefone}}</div>
                                    </div>
                                    <div class="col-md-4">
                                        <div class="text-muted small">
                                            <strong>Destino:</strong><br>
                                            ${{ag.destino_nome}}
                                        </div>
                                    </div>
                                    <div class="col-md-2">
                                        <span class="badge bg-${{statusClass}}">
                                            ${{ag.status_nome}}
                                        </span>
                                    </div>
                                </div>
                            </div>
                        `;
                    }});
                    
                    container.innerHTML = html;
                }}
                
                // Atualizar a cada minuto
                updateTime();
                setInterval(updateTime, 60000);
                
                // Refresh automático a cada 5 minutos
                setInterval(refreshDashboard, 5 * 60 * 1000);
            </script>
            
        </body>
        </html>
        '''
    
    @app.route('/dashboard_api')
    @login_required
    def dashboard_api():
        # Buscar dados reais do banco
        hoje = date.today()
        
        stats = {
            'agendamentos_hoje': Agendamento.query.filter_by(data=hoje).count(),
            'pacientes_ativos': Paciente.query.filter_by(ativo=True).count(),
            'motoristas_disponiveis': Motorista.query.filter_by(status='ativo').count(),
            'veiculos_disponiveis': Veiculo.query.filter_by(ativo=True).count()
        }
        
        # Agendamentos de hoje
        agendamentos_hoje = []
        agendamentos = Agendamento.query.filter_by(data=hoje).order_by(Agendamento.hora).all()
        
        for ag in agendamentos:
            agendamentos_hoje.append({
                'id': ag.id,
                'horario_saida': ag.hora.strftime('%H:%M'),
                'paciente_nome': ag.paciente.nome,
                'paciente_telefone': ag.paciente.telefone,
                'destino_nome': ag.destino[:50],
                'status': ag.status,
                'status_nome': ag.status.replace('_', ' ').title()
            })
        
        return jsonify({
            'stats': stats,
            'agendamentos_hoje': agendamentos_hoje
        })
    
    # ===== ROTAS DE PACIENTES =====
    @app.route('/pacientes')
    @login_required
    def pacientes():
        conteudo = '''
        <div class="page-header">
            <h2>👥 Gerenciamento de Pacientes</h2>
            <p>Cadastro e controle de pacientes do sistema de transporte</p>
        </div>
        
        <div class="card">
            <div class="coming-soon">
                <div class="icon">👥</div>
                <h3>Módulo de Pacientes</h3>
                <p>Este módulo está em desenvolvimento e incluirá:</p>
                <ul style="text-align: left; display: inline-block; margin-top: 1rem;">
                    <li>✅ Cadastro de pacientes</li>
                    <li>✅ Histórico médico</li>
                    <li>✅ Dados de contato</li>
                    <li>✅ Necessidades especiais</li>
                    <li>✅ Relatórios de atendimento</li>
                </ul>
                <div style="margin-top: 2rem;">
                    <a href="''' + url_for('dashboard') + '''" class="btn">← Voltar ao Dashboard</a>
                    <a href="''' + url_for('pacientes_cadastrar') + '''" class="btn btn-secondary" style="margin-left: 1rem;">📋 Cadastrar Paciente</a>
                </div>
            </div>
        </div>
        '''
        return gerar_layout_base("Pacientes", conteudo, "pacientes")
    
    @app.route('/pacientes/cadastrar', methods=['GET', 'POST'])
    @login_required
    def pacientes_cadastrar():
        if request.method == 'POST':
            flash('Funcionalidade em desenvolvimento! Cadastro será implementado em breve.', 'warning')
            return redirect(url_for('pacientes'))
        
        conteudo = '''
        <div class="breadcrumb">
            <a href="''' + url_for('dashboard') + '''">Dashboard</a> > 
            <a href="''' + url_for('pacientes') + '''">Pacientes</a> > 
            Cadastrar Novo Paciente
        </div>
        
        <div class="page-header">
            <h2>📋 Cadastrar Novo Paciente</h2>
            <p>Preencha os dados do paciente que será atendido pelo sistema de transporte</p>
        </div>
        
        <div class="card">
            <form method="POST">
                <div class="form-row">
                    <div class="form-group">
                        <label for="nome">Nome Completo *</label>
                        <input type="text" id="nome" name="nome" required>
                    </div>
                    <div class="form-group">
                        <label for="cpf">CPF *</label>
                        <input type="text" id="cpf" name="cpf" required>
                    </div>
                </div>
                
                <div class="form-row">
                    <div class="form-group">
                        <label for="telefone">Telefone *</label>
                        <input type="tel" id="telefone" name="telefone" required>
                    </div>
                    <div class="form-group">
                        <label for="data_nascimento">Data de Nascimento *</label>
                        <input type="date" id="data_nascimento" name="data_nascimento" required>
                    </div>
                </div>
                
                <div class="form-group">
                    <label for="endereco">Endereço Completo *</label>
                    <input type="text" id="endereco" name="endereco" required>
                </div>
                
                <div class="form-row">
                    <div class="form-group">
                        <label for="cep">CEP</label>
                        <input type="text" id="cep" name="cep">
                    </div>
                    <div class="form-group">
                        <label for="cartao_sus">Cartão SUS</label>
                        <input type="text" id="cartao_sus" name="cartao_sus">
                    </div>
                </div>
                
                <div class="form-group">
                    <label for="observacoes">Necessidades Especiais / Observações</label>
                    <textarea id="observacoes" name="observacoes" rows="4" placeholder="Ex: Cadeirante, necessita maca, acompanhante, etc."></textarea>
                </div>
                
                <div style="margin-top: 2rem;">
                    <button type="submit" class="btn btn-success">💾 Salvar Paciente</button>
                    <a href="''' + url_for('pacientes') + '''" class="btn btn-secondary" style="margin-left: 1rem;">❌ Cancelar</a>
                </div>
            </form>
        </div>
        '''
        return gerar_layout_base("Cadastrar Paciente", conteudo, "pacientes")
    
    # ===== ROTAS DE VEÍCULOS =====
    @app.route('/veiculos')
    @login_required
    def veiculos():
        conteudo = '''
        <div class="page-header">
            <h2>🚗 Gerenciamento de Veículos</h2>
            <p>Controle da frota municipal de transporte de pacientes</p>
        </div>
        
        <div class="card">
            <div class="coming-soon">
                <div class="icon">🚗</div>
                <h3>Módulo de Veículos</h3>
                <p>Este módulo está em desenvolvimento e incluirá:</p>
                <ul style="text-align: left; display: inline-block; margin-top: 1rem;">
                    <li>✅ Cadastro de veículos</li>
                    <li>✅ Controle de manutenção</li>
                    <li>✅ Documentação</li>
                    <li>✅ Quilometragem</li>
                    <li>✅ Agendamento de uso</li>
                </ul>
                <div style="margin-top: 2rem;">
                    <a href="''' + url_for('dashboard') + '''" class="btn">← Voltar ao Dashboard</a>
                    <a href="''' + url_for('veiculos_cadastrar') + '''" class="btn btn-secondary" style="margin-left: 1rem;">🚗 Cadastrar Veículo</a>
                </div>
            </div>
        </div>
        '''
        return gerar_layout_base("Veículos", conteudo, "veiculos")
    
    @app.route('/veiculos/cadastrar', methods=['GET', 'POST'])
    @login_required
    def veiculos_cadastrar():
        if request.method == 'POST':
            flash('Funcionalidade em desenvolvimento! Cadastro será implementado em breve.', 'warning')
            return redirect(url_for('veiculos'))
        
        conteudo = '''
        <div class="breadcrumb">
            <a href="''' + url_for('dashboard') + '''">Dashboard</a> > 
            <a href="''' + url_for('veiculos') + '''">Veículos</a> > 
            Cadastrar Novo Veículo
        </div>
        
        <div class="page-header">
            <h2>🚗 Cadastrar Novo Veículo</h2>
            <p>Registre um novo veículo na frota municipal</p>
        </div>
        
        <div class="card">
            <form method="POST">
                <div class="form-row">
                    <div class="form-group">
                        <label for="placa">Placa *</label>
                        <input type="text" id="placa" name="placa" placeholder="ABC-1234" required>
                    </div>
                    <div class="form-group">
                        <label for="marca">Marca *</label>
                        <input type="text" id="marca" name="marca" required>
                    </div>
                </div>
                
                <div class="form-row">
                    <div class="form-group">
                        <label for="modelo">Modelo *</label>
                        <input type="text" id="modelo" name="modelo" required>
                    </div>
                    <div class="form-group">
                        <label for="ano">Ano *</label>
                        <input type="number" id="ano" name="ano" min="1980" max="2030" required>
                    </div>
                </div>
                
                <div class="form-row">
                    <div class="form-group">
                        <label for="cor">Cor</label>
                        <input type="text" id="cor" name="cor">
                    </div>
                    <div class="form-group">
                        <label for="tipo">Tipo de Veículo *</label>
                        <select id="tipo" name="tipo" required>
                            <option value="">Selecione...</option>
                            <option value="ambulancia">Ambulância</option>
                            <option value="van">Van</option>
                            <option value="micro_onibus">Micro-ônibus</option>
                            <option value="carro">Carro</option>
                        </select>
                    </div>
                </div>
                
                <div class="form-row">
                    <div class="form-group">
                        <label for="capacidade">Capacidade de Passageiros</label>
                        <input type="number" id="capacidade" name="capacidade" min="1" max="50">
                    </div>
                    <div class="form-group">
                        <label for="adaptado">Adaptado para PCD</label>
                        <select id="adaptado" name="adaptado">
                            <option value="nao">Não</option>
                            <option value="sim">Sim</option>
                        </select>
                    </div>
                </div>
                
                <div class="form-group">
                    <label for="observacoes">Observações</label>
                    <textarea id="observacoes" name="observacoes" rows="3" placeholder="Equipamentos especiais, restrições, etc."></textarea>
                </div>
                
                <div style="margin-top: 2rem;">
                    <button type="submit" class="btn btn-success">💾 Salvar Veículo</button>
                    <a href="''' + url_for('veiculos') + '''" class="btn btn-secondary" style="margin-left: 1rem;">❌ Cancelar</a>
                </div>
            </form>
        </div>
        '''
        return gerar_layout_base("Cadastrar Veículo", conteudo, "veiculos")
    
    # ===== ROTAS DE MOTORISTAS =====
    @app.route('/motoristas')
    @login_required
    def motoristas():
        conteudo = '''
        <div class="page-header">
            <h2>👨‍💼 Gerenciamento de Motoristas</h2>
            <p>Cadastro e controle dos motoristas do sistema</p>
        </div>
        
        <div class="card">
            <div class="coming-soon">
                <div class="icon">👨‍💼</div>
                <h3>Módulo de Motoristas</h3>
                <p>Este módulo está em desenvolvimento e incluirá:</p>
                <ul style="text-align: left; display: inline-block; margin-top: 1rem;">
                    <li>✅ Cadastro de motoristas</li>
                    <li>✅ Controle de CNH</li>
                    <li>✅ Escalas de trabalho</li>
                    <li>✅ Histórico de viagens</li>
                    <li>✅ Avaliações</li>
                </ul>
                <div style="margin-top: 2rem;">
                    <a href="''' + url_for('dashboard') + '''" class="btn">← Voltar ao Dashboard</a>
                    <a href="''' + url_for('motoristas_cadastrar') + '''" class="btn btn-secondary" style="margin-left: 1rem;">👨‍💼 Cadastrar Motorista</a>
                </div>
            </div>
        </div>
        '''
        return gerar_layout_base("Motoristas", conteudo, "motoristas")
    
    @app.route('/motoristas/cadastrar', methods=['GET', 'POST'])
    @login_required
    def motoristas_cadastrar():
        if request.method == 'POST':
            flash('Funcionalidade em desenvolvimento! Cadastro será implementado em breve.', 'warning')
            return redirect(url_for('motoristas'))
        
        conteudo = '''
        <div class="breadcrumb">
            <a href="''' + url_for('dashboard') + '''">Dashboard</a> > 
            <a href="''' + url_for('motoristas') + '''">Motoristas</a> > 
            Cadastrar Novo Motorista
        </div>
        
        <div class="page-header">
            <h2>👨‍💼 Cadastrar Novo Motorista</h2>
            <p>Registre um novo motorista no sistema</p>
        </div>
        
        <div class="card">
            <form method="POST">
                <div class="form-row">
                    <div class="form-group">
                        <label for="nome">Nome Completo *</label>
                        <input type="text" id="nome" name="nome" required>
                    </div>
                    <div class="form-group">
                        <label for="cpf">CPF *</label>
                        <input type="text" id="cpf" name="cpf" required>
                    </div>
                </div>
                
                <div class="form-row">
                    <div class="form-group">
                        <label for="telefone">Telefone *</label>
                        <input type="tel" id="telefone" name="telefone" required>
                    </div>
                    <div class="form-group">
                        <label for="data_nascimento">Data de Nascimento *</label>
                        <input type="date" id="data_nascimento" name="data_nascimento" required>
                    </div>
                </div>
                
                <div class="form-row">
                    <div class="form-group">
                        <label for="cnh">Número da CNH *</label>
                        <input type="text" id="cnh" name="cnh" required>
                    </div>
                    <div class="form-group">
                        <label for="categoria_cnh">Categoria CNH *</label>
                        <select id="categoria_cnh" name="categoria_cnh" required>
                            <option value="">Selecione...</option>
                            <option value="A">A - Motocicleta</option>
                            <option value="B">B - Carro</option>
                            <option value="C">C - Caminhão</option>
                            <option value="D">D - Ônibus</option>
                            <option value="E">E - Carreta</option>
                        </select>
                    </div>
                </div>
                
                <div class="form-row">
                    <div class="form-group">
                        <label for="vencimento_cnh">Vencimento da CNH *</label>
                        <input type="date" id="vencimento_cnh" name="vencimento_cnh" required>
                    </div>
                    <div class="form-group">
                        <label for="status">Status *</label>
                        <select id="status" name="status" required>
                            <option value="ativo">Ativo</option>
                            <option value="inativo">Inativo</option>
                            <option value="ferias">Férias</option>
                            <option value="licenca">Licença</option>
                        </select>
                    </div>
                </div>
                
                <div class="form-group">
                    <label for="endereco">Endereço Completo</label>
                    <input type="text" id="endereco" name="endereco">
                </div>
                
                <div class="form-group">
                    <label for="observacoes">Observações</label>
                    <textarea id="observacoes" name="observacoes" rows="3" placeholder="Especializações, restrições, etc."></textarea>
                </div>
                
                <div style="margin-top: 2rem;">
                    <button type="submit" class="btn btn-success">💾 Salvar Motorista</button>
                    <a href="''' + url_for('motoristas') + '''" class="btn btn-secondary" style="margin-left: 1rem;">❌ Cancelar</a>
                </div>
            </form>
        </div>
        '''
        return gerar_layout_base("Cadastrar Motorista", conteudo, "motoristas")
    
    # ===== ROTAS DE AGENDAMENTOS =====
    @app.route('/agendamentos')
    @login_required
    def agendamentos():
        conteudo = '''
        <div class="page-header">
            <h2>📅 Gerenciamento de Agendamentos</h2>
            <p>Programação e controle de transportes de pacientes</p>
        </div>
        
        <div class="card">
            <div class="coming-soon">
                <div class="icon">📅</div>
                <h3>Módulo de Agendamentos</h3>
                <p>Este módulo está em desenvolvimento e incluirá:</p>
                <ul style="text-align: left; display: inline-block; margin-top: 1rem;">
                    <li>✅ Agendamento de transportes</li>
                    <li>✅ Calendário de viagens</li>
                    <li>✅ Notificações</li>
                    <li>✅ Status em tempo real</li>
                    <li>✅ Relatórios de uso</li>
                </ul>
                <div style="margin-top: 2rem;">
                    <a href="''' + url_for('dashboard') + '''" class="btn">← Voltar ao Dashboard</a>
                    <a href="''' + url_for('agendamentos_novo') + '''" class="btn btn-secondary" style="margin-left: 1rem;">📅 Novo Agendamento</a>
                </div>
            </div>
        </div>
        '''
        return gerar_layout_base("Agendamentos", conteudo, "agendamentos")
    
    @app.route('/agendamentos/novo', methods=['GET', 'POST'])
    @login_required
    def agendamentos_novo():
        if request.method == 'POST':
            flash('Funcionalidade em desenvolvimento! Agendamento será implementado em breve.', 'warning')
            return redirect(url_for('agendamentos'))
        
        conteudo = '''
        <div class="breadcrumb">
            <a href="''' + url_for('dashboard') + '''">Dashboard</a> > 
            <a href="''' + url_for('agendamentos') + '''">Agendamentos</a> > 
            Novo Agendamento
        </div>
        
        <div class="page-header">
            <h2>📅 Novo Agendamento</h2>
            <p>Agende um novo transporte de paciente</p>
        </div>
        
        <div class="card">
            <form method="POST">
                <div class="form-row">
                    <div class="form-group">
                        <label for="paciente">Paciente *</label>
                        <select id="paciente" name="paciente" required>
                            <option value="">Selecione o paciente...</option>
                            <option value="1">João Silva - CPF: 123.456.789-00</option>
                            <option value="2">Maria Santos - CPF: 987.654.321-00</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label for="tipo_transporte">Tipo de Transporte *</label>
                        <select id="tipo_transporte" name="tipo_transporte" required>
                            <option value="">Selecione...</option>
                            <option value="consulta">Consulta Médica</option>
                            <option value="exame">Exame</option>
                            <option value="cirurgia">Cirurgia</option>
                            <option value="tratamento">Tratamento</option>
                            <option value="emergencia">Emergência</option>
                        </select>
                    </div>
                </div>
                
                <div class="form-row">
                    <div class="form-group">
                        <label for="data">Data *</label>
                        <input type="date" id="data" name="data" required>
                    </div>
                    <div class="form-group">
                        <label for="hora">Hora *</label>
                        <input type="time" id="hora" name="hora" required>
                    </div>
                </div>
                
                <div class="form-group">
                    <label for="origem">Endereço de Origem *</label>
                    <input type="text" id="origem" name="origem" placeholder="De onde o paciente será buscado" required>
                </div>
                
                <div class="form-group">
                    <label for="destino">Endereço de Destino *</label>
                    <input type="text" id="destino" name="destino" placeholder="Para onde o paciente será levado" required>
                </div>
                
                <div class="form-row">
                    <div class="form-group">
                        <label for="veiculo">Veículo</label>
                        <select id="veiculo" name="veiculo">
                            <option value="">Sistema escolherá automaticamente</option>
                            <option value="1">Ambulância - ABC-1234</option>
                            <option value="2">Van - XYZ-5678</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label for="motorista">Motorista</label>
                        <select id="motorista" name="motorista">
                            <option value="">Sistema escolherá automaticamente</option>
                            <option value="1">João Motorista</option>
                            <option value="2">Maria Motorista</option>
                        </select>
                    </div>
                </div>
                
                <div class="form-group">
                    <label for="observacoes">Observações</label>
                    <textarea id="observacoes" name="observacoes" rows="3" placeholder="Informações adicionais sobre o transporte"></textarea>
                </div>
                
                <div style="margin-top: 2rem;">
                    <button type="submit" class="btn btn-success">📅 Agendar Transporte</button>
                    <a href="''' + url_for('agendamentos') + '''" class="btn btn-secondary" style="margin-left: 1rem;">❌ Cancelar</a>
                </div>
            </form>
        </div>
        '''
        return gerar_layout_base("Novo Agendamento", conteudo, "agendamentos")
    
    @app.route('/logout')
    @login_required
    def logout():
        logout_user()
        session.pop('_flashes', None)
        flash('Logout realizado com sucesso!', 'success')
        return redirect(url_for('login'))
    
    return app

if __name__ == '__main__':
    print("🚀 Iniciando Sistema de Transporte de Pacientes...")
    
    try:
        app = create_app()
        print("📱 Acesse: http://localhost:5010")
        print("🏥 Prefeitura Municipal de Cosmópolis")
        print("👤 Login: admin / admin123")
        app.run(debug=True, host='0.0.0.0', port=5010)
    except Exception as e:
        print(f"❌ Erro ao iniciar aplicação: {e}")
        sys.exit(1)