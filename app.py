import os
import sys
from datetime import datetime, date, timedelta
from flask import Flask, render_template, redirect, url_for, flash, request, get_flashed_messages, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash, generate_password_hash
import json
from functools import wraps

# 🆕 DECORADORES DE PERMISSÃO
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin():
            flash('Acesso negado! Apenas administradores podem acessar esta página.', 'error')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

def supervisor_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_supervisor():
            flash('Acesso negado! Permissão insuficiente.', 'error')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

def edit_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.can_edit():
            flash('Acesso negado! Você não tem permissão para editar.', 'error')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

def delete_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.can_delete():
            flash('Acesso negado! Apenas administradores podem excluir.', 'error')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function


# ===== FUNÇÕES DE SAUDAÇÃO =====
def obter_saudacao():
    """Retorna a saudação apropriada baseada no horário atual"""
    agora = datetime.now()
    hora = agora.hour
    
    if 5 <= hora < 12:
        return "Bom dia! 🌅"
    elif 12 <= hora < 18:
        return "Boa tarde! ☀️"
    else:
        return "Boa noite! 🌙"

def obter_emoji_horario():
    """Retorna o emoji apropriado para o horário"""
    agora = datetime.now()
    hora = agora.hour
    
    if 5 <= hora < 12:
        return "🌅"
    elif 12 <= hora < 18:
        return "☀️"
    else:
        return "🌙"

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
    tipo_usuario = db.Column(db.String(20), nullable=False, default='atendente')  # 🆕 MUDANÇA
    ativo = db.Column(db.Boolean, nullable=False, default=True)
    data_cadastro = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)  # 🆕 NOVO
    
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
    
    # 🆕 NOVOS MÉTODOS DE PERMISSÃO
    def is_admin(self):
        return self.tipo_usuario == 'administrador'
    
    def is_supervisor(self):
        return self.tipo_usuario in ['administrador', 'supervisor']
    
    def can_edit(self):
        return self.tipo_usuario in ['administrador', 'supervisor']
    
    def can_delete(self):
        return self.tipo_usuario == 'administrador'
    
    def can_manage_users(self):
        return self.tipo_usuario == 'administrador'
    
    # Métodos exigidos pelo Flask-Login
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
    
    # 🆕 ENDEREÇO ESTRUTURADO
    cep = db.Column(db.String(9), nullable=False)
    logradouro = db.Column(db.String(200), nullable=False)  # Rua/Avenida
    numero = db.Column(db.String(10), nullable=False)       # Número da casa
    complemento = db.Column(db.String(100))                 # Apto, casa, etc
    bairro = db.Column(db.String(100), nullable=False)
    cidade = db.Column(db.String(100), nullable=False)
    uf = db.Column(db.String(2), nullable=False)
    
    # Campo antigo (mantido apenas por compatibilidade temporária)
    endereco = db.Column(db.Text)  # Será removido após migração
    
    cartao_sus = db.Column(db.String(20))
    observacoes = db.Column(db.Text)
    ativo = db.Column(db.Boolean, nullable=False, default=True)
    data_cadastro = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    # Relacionamentos
    agendamentos = db.relationship('Agendamento', backref='paciente', lazy=True)
    
    @property
    def endereco_completo(self):
        """Retorna o endereço completo formatado"""
        endereco = f"{self.logradouro}, {self.numero}"
        if self.complemento:
            endereco += f", {self.complemento}"
        endereco += f" - {self.bairro}, {self.cidade}/{self.uf}"
        endereco += f" - CEP: {self.cep}"
        return endereco

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
    especialidade = db.Column(db.String(100))  # 🆕 NOVO CAMPO
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
        
        # Criar tabelas
        db.create_all()
        print("✅ Tabelas criadas no banco de dados")
        
        # 🆕 MIGRAÇÃO DE ENDEREÇOS
        migrar_enderecos_pacientes()
    else:
        print(f"✅ Banco de dados encontrado: {db_path}")
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
        else:
            if not admin.check_password('admin123'):
                print("❌ Hash do usuário admin inválido. Resetando senha...")
                admin.set_password('admin123')
                db.session.commit()
                print("✅ Senha do usuário admin resetada para: admin123")
            else:
                print("✅ Usuário admin válido encontrado")
    except Exception as e:
        print(f"❌ Erro ao verificar usuário admin: {e}")

# Função para escapar strings para JavaScript
def escape_js_string(s):
    """Escapa uma string para uso seguro em JavaScript"""
    if s is None:
        return ''
    return str(s).replace('\\', '\\\\').replace('"', '\\"').replace("'", "\\'").replace('\n', '\\n').replace('\r', '\\r')


def gerar_layout_base(titulo, conteudo, ativo=""):
    """Gera o layout base para todas as páginas"""
    
    # 🔍 DEBUG TEMPORÁRIO
    if current_user.is_authenticated:
        print(f"🔍 DEBUG - Usuario: {current_user.nome_completo}")
        print(f"🔍 DEBUG - Tipo: {current_user.tipo_usuario}")
        if hasattr(current_user, "is_admin"):
            print(f"🔍 DEBUG - is_admin(): {current_user.is_admin()}")
        else:
            print("⚠️ DEBUG - current_user não tem método is_admin()")
    
    # Badge do tipo de usuário
    badge_html = ""
    if current_user.is_authenticated:
        badge_html = f'<span style="background: var(--primary-color); color: white; padding: 0.25rem 0.5rem; border-radius: 0.25rem; font-size: 0.75rem; margin-left: 0.5rem;">{current_user.tipo_usuario.upper()}</span>'
    
    # Menu de usuários apenas para administradores
    menu_usuarios_html = ""
    if current_user.is_authenticated and hasattr(current_user, "is_admin") and current_user.is_admin():
        active_class = "active" if ativo == "usuarios" else ""
        menu_usuarios_html = f'<a href="/usuarios" class="{active_class}">👥 Usuários</a>'
        print("✅ DEBUG - Menu usuarios ADICIONADO!")
    else:
        print("❌ DEBUG - Menu usuarios NAO adicionado")
    
    return f'''
    <html>
    <head>
        <title>{titulo} - Sistema de Transporte</title>
        <style>
            :root {{
                --color-100: #ffffff;
                --color-95: #ebf9f9;
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
            .nav a:hover {{ background: var(--color-95); color: var(--primary-color); }}
            .nav a.active {{ background: var(--primary-color); color: var(--color-100); }}
            .container {{ padding: 2rem; max-width: 1400px; margin: 0 auto; }}
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
            .alert {{ padding: 0.75rem; margin-bottom: 1rem; border-radius: 0.5rem; }}
            .alert-error {{ background: rgba(232, 29, 81, 0.1); color: var(--danger-color); border: 1px solid var(--danger-color); }}
            .alert-success {{ background: rgba(121, 178, 74, 0.1); color: var(--success-color); border: 1px solid var(--success-color); }}
            .alert-warning {{ background: rgba(242, 130, 60, 0.1); color: var(--warning-color); border: 1px solid var(--warning-color); }}
            
            /* Estilos para relatórios */
            .tabs {{ display: flex; border-bottom: 2px solid var(--border-color); margin-bottom: 2rem; }}
            .tab {{ padding: 1rem 2rem; background: transparent; border: none; cursor: pointer; color: var(--gray-color); font-weight: 600; transition: all 0.3s ease; }}
            .tab.active {{ color: var(--primary-color); border-bottom: 2px solid var(--primary-color); }}
            .tab:hover {{ color: var(--primary-color); }}
            .tab-content {{ display: none; }}
            .tab-content.active {{ display: block; }}
            .filters {{ background: var(--color-95); padding: 1.5rem; border-radius: 0.5rem; margin-bottom: 2rem; }}
            .filters-row {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; align-items: end; }}
            .table-container {{ overflow-x: auto; }}
            .report-table {{ width: 100%; border-collapse: collapse; margin-bottom: 2rem; }}
            .report-table th {{ background: var(--primary-color); color: var(--color-100); padding: 1rem; text-align: left; }}
            .report-table td {{ padding: 0.75rem; border-bottom: 1px solid var(--border-color); }}
            .report-table tr:hover {{ background: var(--color-95); }}
            .print-btn {{ background: var(--info-color); }}
            .print-btn:hover {{ background: #7bb8ff; }}
            
            @media print {{
                .no-print {{ display: none !important; }}
                .page-header, .nav, .header, .filters {{ display: none !important; }}
                .container {{ padding: 0; max-width: none; }}
            }}
        </style>
    </head>
    <body>
        <div class="header no-print">
            <h1>🚑 Sistema de Transporte de Pacientes</h1>
            <div class="user-info">
                Bem-vindo, {current_user.nome_completo}! 
                {badge_html}
                <a href="{url_for('logout')}" class="logout">Sair</a>
            </div>
            <div style="clear: both;"></div>
        </div>
        
        <div class="nav no-print">
            <a href="{url_for('dashboard')}" class="{'active' if ativo == 'dashboard' else ''}">🏠 Dashboard</a>
            <a href="{url_for('pacientes')}" class="{'active' if ativo == 'pacientes' else ''}">👥 Pacientes</a>
            <a href="{url_for('veiculos')}" class="{'active' if ativo == 'veiculos' else ''}">🚗 Veículos</a>
            <a href="{url_for('motoristas')}" class="{'active' if ativo == 'motoristas' else ''}">👨‍💼 Motoristas</a>
            <a href="{url_for('agendamentos')}" class="{'active' if ativo == 'agendamentos' else ''}">📅 Agendamentos</a>
            <a href="{url_for('relatorios')}" class="{'active' if ativo == 'relatorios' else ''}">📊 Relatórios</a>
            {menu_usuarios_html}
        </div>
        
        <div class="container">
            {conteudo}
        </div>
    </body>
    </html>
    '''

def migrar_enderecos_pacientes():
    """Migra endereços antigos para nova estrutura"""
    try:
        pacientes = Paciente.query.filter(
            db.and_(
                Paciente.endereco.isnot(None),
                db.or_(
                    Paciente.logradouro.is_(None),
                    Paciente.cep.is_(None)
                )
            )
        ).all()
        
        for paciente in pacientes:
            if not paciente.cep:
                # Endereço padrão para migração
                paciente.cep = "13150000"
                paciente.logradouro = paciente.endereco or "Endereço não informado"
                paciente.numero = "S/N"
                paciente.bairro = "Centro"
                paciente.cidade = "Cosmópolis"
                paciente.uf = "SP"
        
        db.session.commit()
        print(f"✅ Migração de endereços concluída: {len(pacientes)} pacientes atualizados")
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ Erro na migração de endereços: {e}")

# 🏠 VALIDAÇÃO DE CEP E ENDEREÇO
import re

def validar_cep(cep):
    """Valida formato de CEP brasileiro"""
    if not cep:
        return False, "CEP é obrigatório"
    
    # Remove caracteres não numéricos
    cep_numerico = re.sub(r'\D', '', cep)
    
    # Deve ter exatamente 8 dígitos
    if len(cep_numerico) != 8:
        return False, "CEP deve ter 8 dígitos"
    
    # Não pode ser sequencial (00000000, 11111111, etc.)
    if re.match(r'^(\d)\1{7}$', cep_numerico):
        return False, "CEP não pode ser sequencial"
    
    # CEP não pode começar com 0 (exceto algumas regiões válidas)
    prefixos_validos = ['01000', '02000', '03000', '04000', '05000', '08000', '09000']
    if cep_numerico.startswith('0') and not any(cep_numerico.startswith(p) for p in prefixos_validos):
        return False, "CEP com formato inválido"
    
    return True, "CEP válido"

def validar_endereco_completo(cep, logradouro, numero, bairro, cidade, uf):
    """Valida todos os campos obrigatórios do endereço"""
    erros = []
    
    # Validar CEP
    cep_valido, msg_cep = validar_cep(cep)
    if not cep_valido:
        erros.append(msg_cep)
    
    # Validar campos obrigatórios
    if not logradouro or len(logradouro.strip()) < 3:
        erros.append("Logradouro deve ter pelo menos 3 caracteres")
    
    if not numero or len(numero.strip()) < 1:
        erros.append("Número é obrigatório")
    
    if not bairro or len(bairro.strip()) < 2:
        erros.append("Bairro deve ter pelo menos 2 caracteres")
    
    if not cidade or len(cidade.strip()) < 2:
        erros.append("Cidade deve ter pelo menos 2 caracteres")
    
    if not uf or len(uf.strip()) != 2:
        erros.append("UF deve ter exatamente 2 caracteres")
    
    return len(erros) == 0, erros

def formatar_cep(cep):
    """Formata CEP no padrão 00000-000"""
    if not cep:
        return ""
    
    cep_numerico = re.sub(r'\D', '', cep)
    if len(cep_numerico) == 8:
        return f"{cep_numerico[:5]}-{cep_numerico[5:]}"
    
    return cep



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
    
    # ===== ROTAS =====
    
    # 🆕 GERENCIAMENTO DE USUÁRIOS
    @app.route('/usuarios')
    @admin_required
    def usuarios():
        usuarios_lista = Usuario.query.order_by(Usuario.data_cadastro.desc()).all()
        
        usuarios_html = ""
        if usuarios_lista:
            usuarios_html = '''
            <div class="card">
                <h3 style="color: var(--primary-color); margin-bottom: 1rem;">👥 Usuários do Sistema</h3>
                <div style="overflow-x: auto;">
                    <table style="width: 100%; border-collapse: collapse;">
                        <thead>
                            <tr style="background: var(--color-95);">
                                <th style="padding: 0.75rem; text-align: left; border-bottom: 2px solid var(--primary-color);">Nome</th>
                                <th style="padding: 0.75rem; text-align: left; border-bottom: 2px solid var(--primary-color);">Username</th>
                                <th style="padding: 0.75rem; text-align: left; border-bottom: 2px solid var(--primary-color);">Tipo</th>
                                <th style="padding: 0.75rem; text-align: left; border-bottom: 2px solid var(--primary-color);">Status</th>
                                <th style="padding: 0.75rem; text-align: left; border-bottom: 2px solid var(--primary-color);">Data Cadastro</th>
                                <th style="padding: 0.75rem; text-align: left; border-bottom: 2px solid var(--primary-color);">Ações</th>
                            </tr>
                        </thead>
                        <tbody>
            '''
            for usuario in usuarios_lista:
                status_color = 'color: var(--success-color);' if usuario.ativo else 'color: var(--danger-color);'
                tipo_color = {
                    'administrador': 'color: var(--danger-color); font-weight: bold;',
                    'supervisor': 'color: var(--warning-color); font-weight: bold;',
                    'atendente': 'color: var(--info-color);'
                }.get(usuario.tipo_usuario, '')
                
                usuarios_html += f'''
                            <tr>
                                <td style="padding: 0.75rem; border-bottom: 1px solid var(--border-color);">{usuario.nome_completo}</td>
                                <td style="padding: 0.75rem; border-bottom: 1px solid var(--border-color);"><strong>{usuario.username}</strong></td>
                                <td style="padding: 0.75rem; border-bottom: 1px solid var(--border-color); {tipo_color}">{usuario.tipo_usuario.title()}</td>
                                <td style="padding: 0.75rem; border-bottom: 1px solid var(--border-color); {status_color}">{'Ativo' if usuario.ativo else 'Inativo'}</td>
                                <td style="padding: 0.75rem; border-bottom: 1px solid var(--border-color);">{usuario.data_cadastro.strftime('%d/%m/%Y') if usuario.data_cadastro else 'N/A'}</td>
                                <td style="padding: 0.75rem; border-bottom: 1px solid var(--border-color);">
                                    <a href="/usuarios/editar/{usuario.id}" class="btn btn-warning" style="padding: 0.25rem 0.5rem; font-size: 0.875rem; margin-right: 0.25rem;">✏️ Editar</a>
                                    {'<a href="/usuarios/excluir/' + str(usuario.id) + '" class="btn" style="background: var(--danger-color); color: white; padding: 0.25rem 0.5rem; font-size: 0.875rem;" onclick="return confirm(\'Tem certeza que deseja excluir?\')">🗑️ Excluir</a>' if usuario.id != current_user.id else '<span style="color: var(--gray-color); font-size: 0.875rem;">Usuário atual</span>'}
                                </td>
                            </tr>
                '''
            usuarios_html += '''
                        </tbody>
                    </table>
                </div>
            </div>
            '''
        
        conteudo = f'''
        <div class="page-header">
            <h2>👥 Gerenciamento de Usuários</h2>
            <p>Controle de acesso e permissões do sistema</p>
            <div style="margin-top: 1rem;">
                <a href="/usuarios/novo" class="btn">👤 Cadastrar Novo Usuário</a>
            </div>
        </div>
        
        {usuarios_html}
        
        {f'<div class="card"><div class="coming-soon"><div class="icon">👥</div><h3>Nenhum usuário encontrado</h3><p>Comece cadastrando o primeiro usuário!</p></div></div>' if not usuarios_lista else ''}
        '''
        return gerar_layout_base("Usuários", conteudo, "usuarios")

    @app.route('/usuarios/novo', methods=['GET', 'POST'])
    @admin_required
    def usuarios_novo():
        if request.method == 'POST':
            try:
                # Extrair dados do formulário
                username = request.form.get('username', '').strip()
                nome_completo = request.form.get('nome_completo', '').strip()
                email = request.form.get('email', '').strip()
                password = request.form.get('password', '').strip()
                confirm_password = request.form.get('confirm_password', '').strip()
                tipo_usuario = request.form.get('tipo_usuario', '').strip()
                
                # Validação básica
                if not all([username, nome_completo, password, confirm_password, tipo_usuario]):
                    flash('Por favor, preencha todos os campos obrigatórios!', 'error')
                    return redirect(url_for('usuarios_novo'))
                
                if password != confirm_password:
                    flash('As senhas não coincidem!', 'error')
                    return redirect(url_for('usuarios_novo'))
                
                if len(password) < 6:
                    flash('A senha deve ter pelo menos 6 caracteres!', 'error')
                    return redirect(url_for('usuarios_novo'))
                
                # Verificar se username já existe
                if Usuario.query.filter_by(username=username).first():
                    flash('Nome de usuário já existe!', 'error')
                    return redirect(url_for('usuarios_novo'))
                
                # Criar novo usuário
                usuario = Usuario(
                    username=username,
                    nome_completo=nome_completo,
                    email=email if email else None,
                    tipo_usuario=tipo_usuario
                )
                usuario.set_password(password)
                
                db.session.add(usuario)
                db.session.commit()
                
                flash(f'Usuário "{nome_completo}" cadastrado com sucesso!', 'success')
                return redirect(url_for('usuarios'))
                
            except Exception as e:
                db.session.rollback()
                flash(f'Erro ao cadastrar usuário: {str(e)}', 'error')
                print(f"❌ Erro ao cadastrar usuário: {e}")
        
        # Gerar alertas de mensagens flash
        messages_html = ""
        for category, message in get_flashed_messages(with_categories=True):
            alert_class = f"alert-{category}"
            messages_html += f'<div class="alert {alert_class}">{message}</div>'
        
        conteudo = f'''
        <div class="breadcrumb">
            <a href="/dashboard">Dashboard</a> > 
            <a href="/usuarios">Usuários</a> > 
            Novo Usuário
        </div>
        
        <div class="page-header">
            <h2>👤 Cadastrar Novo Usuário</h2>
            <p>Crie uma nova conta de acesso ao sistema</p>
        </div>
        
        {messages_html}
        
        <div class="card">
            <form method="POST">
                <div class="form-row">
                    <div class="form-group">
                        <label for="username">Nome de Usuário *</label>
                        <input type="text" id="username" name="username" required>
                    </div>
                    <div class="form-group">
                        <label for="nome_completo">Nome Completo *</label>
                        <input type="text" id="nome_completo" name="nome_completo" required>
                    </div>
                </div>
                
                <div class="form-row">
                    <div class="form-group">
                        <label for="email">E-mail</label>
                        <input type="email" id="email" name="email">
                    </div>
                    <div class="form-group">
                        <label for="tipo_usuario">Tipo de Usuário *</label>
                        <select id="tipo_usuario" name="tipo_usuario" required>
                            <option value="">Selecione...</option>
                            <option value="atendente">🎧 Atendente - Operações básicas</option>
                            <option value="supervisor">👨‍💼 Supervisor - Pode editar dados</option>
                            <option value="administrador">👑 Administrador - Acesso total</option>
                        </select>
                    </div>
                </div>
                
                <div class="form-row">
                    <div class="form-group">
                        <label for="password">Senha *</label>
                        <input type="password" id="password" name="password" required>
                    </div>
                    <div class="form-group">
                        <label for="confirm_password">Confirmar Senha *</label>
                        <input type="password" id="confirm_password" name="confirm_password" required>
                    </div>
                </div>
                
                <div class="form-group">
                    <h4 style="color: var(--primary-color); margin-bottom: 1rem;">Permissões por Tipo:</h4>
                    <div style="background: var(--color-95); padding: 1rem; border-radius: 0.5rem;">
                        <p><strong>🎧 Atendente:</strong> Criar agendamentos, visualizar dados, operações básicas</p>
                        <p><strong>👨‍💼 Supervisor:</strong> Todas as permissões do atendente + editar agendamentos e dados</p>
                        <p><strong>👑 Administrador:</strong> Todas as permissões + excluir dados + gerenciar usuários</p>
                    </div>
                </div>
                
                <div style="margin-top: 2rem;">
                    <button type="submit" class="btn btn-success">👤 Criar Usuário</button>
                    <a href="/usuarios" class="btn btn-secondary" style="margin-left: 1rem;">❌ Cancelar</a>
                </div>
            </form>
        </div>
        '''
        return gerar_layout_base("Novo Usuário", conteudo, "usuarios")
    
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
    
    # ===== DASHBOARD =====
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
        
        # Preparar dados para JavaScript
        agendamentos_js_data = []
        for ag in agendamentos_lista:
            status_class = {
                'confirmado': 'success',
                'agendado': 'warning', 
                'em_andamento': 'primary',
                'concluido': 'secondary'
            }.get(ag.status, 'secondary')
            
            agendamentos_js_data.append({
                'id': ag.id,
                'horario_saida': ag.hora.strftime('%H:%M'),
                'paciente_nome': escape_js_string(ag.paciente.nome),
                'paciente_telefone': escape_js_string(ag.paciente.telefone),
                'destino_nome': escape_js_string(ag.destino[:50]),
                'status': ag.status,
                'status_nome': escape_js_string(ag.status.replace('_', ' ').title()),
                'status_class': status_class
            })
        
        # Converter para JSON seguro
        agendamentos_json = json.dumps(agendamentos_js_data)
        
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
                            <h1 class="h3 mb-2">{obter_saudacao()}</h1>
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
                                        <a href="{url_for('relatorios')}" class="quick-action">
                                            <i class="bi bi-file-earmark-text"></i>
                                            <div class="fw-semibold">Relatórios</div>
                                        </a>
                                    </div>
                                    <div class="col-md-3 col-6">
                                        <a href="#" class="quick-action" onclick="refreshDashboard(); return false;">
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
                                    <!-- Conteúdo será carregado via JavaScript -->
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
                                <a href="{url_for('relatorios')}" class="list-group-item list-group-item-action">
                                    <i class="bi bi-file-earmark-text me-2"></i>Relatórios
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
                console.log('🚀 Dashboard carregado e pronto para atualizar!');
                
                // Dados iniciais dos agendamentos
                var agendamentosIniciais = {agendamentos_json};
                
                // Atualizar relógio
                function updateTime() {{
                    const now = new Date();
                    const timeString = now.toLocaleTimeString('pt-BR', {{ 
                        hour: '2-digit', 
                        minute: '2-digit' 
                    }});
                    const timeElement = document.getElementById('currentTime');
                    const updateElement = document.getElementById('lastUpdate');
                    
                    if (timeElement) timeElement.textContent = timeString;
                    if (updateElement) updateElement.textContent = now.toLocaleTimeString('pt-BR');
                }}
                
                // Refresh automático dos dados
                function refreshDashboard() {{
                    console.log('🔄 Atualizando dashboard...');
                    
                    fetch('/dashboard_api')
                        .then(response => {{
                            console.log('📡 Resposta recebida:', response.status);
                            if (!response.ok) {{
                                throw new Error('HTTP error! status: ' + response.status);
                            }}
                            return response.json();
                        }})
                        .then(data => {{
                            console.log('📊 Dados recebidos:', data);
                            
                            // Atualizar contadores com animação
                            const stats = data.stats;
                            if (stats) {{
                                animateCounter('agendamentosHoje', stats.agendamentos_hoje);
                                animateCounter('pacientesAtivos', stats.pacientes_ativos);
                                animateCounter('motoristasDisponiveis', stats.motoristas_disponiveis);
                                animateCounter('veiculosDisponiveis', stats.veiculos_disponiveis);
                            }}
                            
                            // Atualizar agendamentos
                            updateTodaySchedule(data.agendamentos_hoje);
                            
                            // Atualizar timestamp
                            updateTime();
                            
                            console.log('✅ Dashboard atualizado com sucesso!');
                        }})
                        .catch(error => {{
                            console.error('❌ Erro ao atualizar dashboard:', error);
                        }});
                }}
                
                // Animação dos contadores
                function animateCounter(elementId, newValue) {{
                    const element = document.getElementById(elementId);
                    if (!element) return;
                    
                    const currentValue = parseInt(element.textContent) || 0;
                    if (currentValue === newValue) return;
                    
                    const duration = 1000;
                    const steps = 20;
                    const stepTime = duration / steps;
                    const stepValue = (newValue - currentValue) / steps;
                    
                    let step = 0;
                    const timer = setInterval(function() {{
                        step++;
                        const value = Math.round(currentValue + (stepValue * step));
                        element.textContent = value;
                        
                        if (step >= steps) {{
                            clearInterval(timer);
                            element.textContent = newValue;
                        }}
                    }}, stepTime);
                }}
                
                function updateTodaySchedule(agendamentos) {{
                    const container = document.getElementById('todaySchedule');
                    if (!container) return;
                    
                    console.log('📅 Atualizando agendamentos:', agendamentos);
                    
                    if (!agendamentos || agendamentos.length === 0) {{
                        container.innerHTML = '<div class="text-center py-4">' +
                            '<i class="bi bi-calendar-x text-muted" style="font-size: 3rem;"></i>' +
                            '<p class="text-muted mt-3 mb-0">Nenhum agendamento para hoje</p>' +
                            '<a href="{url_for('agendamentos_novo')}" class="btn btn-primary mt-2">' +
                            '<i class="bi bi-plus-circle me-1"></i> Criar Agendamento</a>' +
                            '</div>';
                        return;
                    }}
                    
                    var html = '';
                    agendamentos.forEach(function(ag) {{
                        const statusClass = {{
                            'confirmado': 'success',
                            'agendado': 'warning',
                            'em_andamento': 'primary',
                            'concluido': 'secondary'
                        }}[ag.status] || 'secondary';
                        
                        html += '<div class="schedule-item">' +
                            '<div class="row align-items-center">' +
                            '<div class="col-md-2">' +
                            '<div class="schedule-time">' + ag.horario_saida + '</div>' +
                            '</div>' +
                            '<div class="col-md-4">' +
                            '<div class="fw-semibold">' + ag.paciente_nome + '</div>' +
                            '<div class="text-muted small">' + ag.paciente_telefone + '</div>' +
                            '</div>' +
                            '<div class="col-md-4">' +
                            '<div class="text-muted small">' +
                            '<strong>Destino:</strong><br>' + ag.destino_nome +
                            '</div>' +
                            '</div>' +
                            '<div class="col-md-2">' +
                            '<span class="badge bg-' + statusClass + '">' + ag.status_nome + '</span>' +
                            '</div>' +
                            '</div>' +
                            '</div>';
                    }});
                    
                    container.innerHTML = html;
                }}
                
                // Inicializar
                document.addEventListener('DOMContentLoaded', function() {{
                    console.log('📱 DOM carregado - inicializando dashboard');
                    
                    // Carregar agendamentos iniciais
                    updateTodaySchedule(agendamentosIniciais);
                    
                    // Atualizar a cada minuto
                    updateTime();
                    setInterval(updateTime, 60000);
                    
                    // Refresh automático a cada 2 minutos
                    setInterval(refreshDashboard, 2 * 60 * 1000);
                    
                    // Primeira atualização após 3 segundos
                    setTimeout(refreshDashboard, 3000);
                    
                    console.log('✅ Dashboard inicializado com sucesso!');
                }});
            </script>
            
        </body>
        </html>
        '''
    
    @app.route('/dashboard_api')
    @login_required
    def dashboard_api():
        try:
            print("🔄 API Dashboard chamada!")
            
            # Buscar dados reais do banco
            hoje = date.today()
            
            stats = {
                'agendamentos_hoje': Agendamento.query.filter_by(data=hoje).count(),
                'pacientes_ativos': Paciente.query.filter_by(ativo=True).count(),
                'motoristas_disponiveis': Motorista.query.filter_by(status='ativo').count(),
                'veiculos_disponiveis': Veiculo.query.filter_by(ativo=True).count()
            }
            
            print(f"📊 Stats calculadas: {stats}")
            
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
            
            print(f"📅 Agendamentos encontrados: {len(agendamentos_hoje)}")
            
            response_data = {
                'stats': stats,
                'agendamentos_hoje': agendamentos_hoje,
                'timestamp': datetime.now().isoformat()
            }
            
            print("✅ API Dashboard respondendo com sucesso!")
            return jsonify(response_data)
            
        except Exception as e:
            print(f"❌ Erro na API Dashboard: {e}")
            return jsonify({'error': str(e)}), 500
    
    # ===== PACIENTES =====
    @app.route('/pacientes')
    @login_required
    def pacientes():
        pacientes_lista = Paciente.query.filter_by(ativo=True).order_by(Paciente.data_cadastro.desc()).all()
        
        pacientes_html = ""
        if pacientes_lista:
            pacientes_html = '''
            <div class="card">
                <h3 style="color: var(--primary-color); margin-bottom: 1rem;">📋 Pacientes Cadastrados</h3>
                <div style="overflow-x: auto;">
                    <table style="width: 100%; border-collapse: collapse;">
                        <thead>
                            <tr style="background: var(--color-95);">
                                <th style="padding: 0.75rem; text-align: left; border-bottom: 2px solid var(--primary-color);">Nome</th>
                                <th style="padding: 0.75rem; text-align: left; border-bottom: 2px solid var(--primary-color);">CPF</th>
                                <th style="padding: 0.75rem; text-align: left; border-bottom: 2px solid var(--primary-color);">Telefone</th>
                                <!-- 🆕 COLUNA ENDEREÇO -->
                                <th style="padding: 0.75rem; text-align: left; border-bottom: 2px solid var(--primary-color);">Endereço</th>
                                <th style="padding: 0.75rem; text-align: left; border-bottom: 2px solid var(--primary-color);">Data Cadastro</th>
                                <th style="padding: 0.75rem; text-align: left; border-bottom: 2px solid var(--primary-color);">Agendamentos</th>
                                <th style="padding: 0.75rem; text-align: left; border-bottom: 2px solid var(--primary-color);">Ações</th>
                            </tr>
                        </thead>
                        <tbody>
            '''
            for paciente in pacientes_lista:
                # Contar agendamentos do paciente
                total_agendamentos = Agendamento.query.filter_by(paciente_id=paciente.id).count()
                
                # Botões de ação baseados em permissões
                acoes_html = ""
                if current_user.can_edit():
                    acoes_html += f'<a href="/pacientes/editar/{paciente.id}" class="btn btn-warning" style="padding: 0.25rem 0.5rem; font-size: 0.875rem; margin-right: 0.25rem;">✏️ Editar</a>'
                
                if current_user.can_delete():
                    if total_agendamentos == 0:
                        acoes_html += f'<a href="/pacientes/excluir/{paciente.id}" class="btn" style="background: var(--danger-color); color: white; padding: 0.25rem 0.5rem; font-size: 0.875rem;" onclick="return confirmarExclusao(\'paciente\')">🗑️ Excluir</a>'
                    else:
                        acoes_html += f'<span class="btn" style="background: var(--gray-color); color: white; padding: 0.25rem 0.5rem; font-size: 0.875rem; cursor: not-allowed;" title="Paciente possui {total_agendamentos} agendamento(s)">🔒 Bloqueado</span>'
                
                if not acoes_html:
                    acoes_html = '<span style="color: var(--gray-color); font-size: 0.875rem;">Visualização</span>'
                
                # 🆕 ENDEREÇO COMPLETO ESTRUTURADO
                endereco_completo = "Endereço não informado"
                if hasattr(paciente, 'endereco_completo') and paciente.logradouro:
                    endereco_completo = paciente.endereco_completo
                elif hasattr(paciente, 'endereco') and paciente.endereco:  # fallback para dados antigos
                    endereco_completo = paciente.endereco
                
                pacientes_html += f'''
                            <tr>
                                <td style="padding: 0.75rem; border-bottom: 1px solid var(--border-color);">{paciente.nome}</td>
                                <td style="padding: 0.75rem; border-bottom: 1px solid var(--border-color);">{paciente.cpf}</td>
                                <td style="padding: 0.75rem; border-bottom: 1px solid var(--border-color);">{paciente.telefone}</td>
                                <!-- 🆕 NOVA COLUNA ENDEREÇO -->
                                <td style="padding: 0.75rem; border-bottom: 1px solid var(--border-color); font-size: 0.875rem;" title="{endereco_completo}">{endereco_completo[:50]}{'...' if len(endereco_completo) > 50 else ''}</td>
                                <td style="padding: 0.75rem; border-bottom: 1px solid var(--border-color);">{paciente.data_cadastro.strftime('%d/%m/%Y')}</td>
                                <td style="padding: 0.75rem; border-bottom: 1px solid var(--border-color); text-align: center;">{total_agendamentos}</td>
                                <td style="padding: 0.75rem; border-bottom: 1px solid var(--border-color);">
                                    {acoes_html}
                                </td>
                            </tr>
                '''
            pacientes_html += '''
                        </tbody>
                    </table>
                </div>
            </div>
            '''
        
        conteudo = f'''
        <div class="page-header">
            <h2>👥 Gerenciamento de Pacientes</h2>
            <p>Cadastro e controle de pacientes do sistema de transporte</p>
            <div style="margin-top: 1rem;">
                <a href="{url_for('pacientes_cadastrar')}" class="btn">📋 Cadastrar Novo Paciente</a>
            </div>
        </div>
        
        {pacientes_html}
        
        {f'<div class="card"><div class="coming-soon"><div class="icon">👥</div><h3>Nenhum paciente cadastrado</h3><p>Comece cadastrando o primeiro paciente do sistema!</p></div></div>' if not pacientes_lista else ''}
        
        <script>
            function confirmarExclusao(tipo) {{
                return confirm("Tem certeza que deseja excluir este " + tipo + "? Esta ação não pode ser desfeita!");
            }}
        </script>
        
        '''
        return gerar_layout_base("Pacientes", conteudo, "pacientes")


    
# ===== CADASTRO DE PACIENTES =====
@app.route('/pacientes/cadastrar', methods=['GET', 'POST'])
@login_required
def pacientes_cadastrar():
    if request.method == 'POST':
        try:
            # Extrair dados do formulário
            nome = request.form.get('nome', '').strip()
            cpf = request.form.get('cpf', '').strip()
            telefone = request.form.get('telefone', '').strip()
            data_nascimento = request.form.get('data_nascimento')
            
            # 🆕 ENDEREÇO ESTRUTURADO
            cep = request.form.get('cep', '').strip()
            logradouro = request.form.get('logradouro', '').strip()
            numero = request.form.get('numero', '').strip()
            complemento = request.form.get('complemento', '').strip()
            bairro = request.form.get('bairro', '').strip()
            cidade = request.form.get('cidade', '').strip()
            uf = request.form.get('uf', '').strip()
            
            cartao_sus = request.form.get('cartao_sus', '').strip()
            observacoes = request.form.get('observacoes', '').strip()
            
            # 🆕 VALIDAÇÃO COMPLETA DE ENDEREÇO
            endereco_valido, erros_endereco = validar_endereco_completo(
                cep, logradouro, numero, bairro, cidade, uf
            )
            if not endereco_valido:
                for erro in erros_endereco:
                    flash(f'Erro no endereço: {erro}', 'error')
                return redirect(url_for('pacientes_cadastrar'))
            
            # Formatar CEP
            cep = formatar_cep(cep)
            
            # Validação básica de outros campos
            if not all([nome, cpf, telefone, data_nascimento]):
                flash('Por favor, preencha todos os campos obrigatórios!', 'error')
                return redirect(url_for('pacientes_cadastrar'))
            
            # Verificar se CPF já existe
            if Paciente.query.filter_by(cpf=cpf).first():
                flash('CPF já cadastrado no sistema!', 'error')
                return redirect(url_for('pacientes_cadastrar'))
            
            # Converter data
            data_nascimento = datetime.strptime(data_nascimento, '%Y-%m-%d').date()
            
            # Criar novo paciente
            paciente = Paciente(
                nome=nome,
                cpf=cpf,
                telefone=telefone,
                data_nascimento=data_nascimento,
                cep=cep,
                logradouro=logradouro,
                numero=numero,
                complemento=complemento if complemento else None,
                bairro=bairro,
                cidade=cidade,
                uf=uf.upper(),
                cartao_sus=cartao_sus if cartao_sus else None,
                observacoes=observacoes if observacoes else None
            )
            
            db.session.add(paciente)
            db.session.commit()
            
            flash(f'Paciente "{nome}" cadastrado com sucesso!', 'success')
            return redirect(url_for('pacientes'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao cadastrar paciente: {str(e)}', 'error')
            print(f"❌ Erro ao cadastrar paciente: {e}")

    # Gerar alertas de mensagens flash
    messages_html = ""
    for category, message in get_flashed_messages(with_categories=True):
        alert_class = f"alert-{category}"
        messages_html += f'<div class="alert {alert_class}">{message}</div>'
    
    # 🆕 Definição da variável conteudo
    conteudo = f'''
        <div class="breadcrumb">
            <a href="{url_for('dashboard')}">Dashboard</a> > 
            <a href="{url_for('pacientes')}">Pacientes</a> > 
            Cadastrar Novo Paciente
        </div>
        
        <div class="page-header">
            <h2>📋 Cadastrar Novo Paciente</h2>
            <p>Preencha os dados do paciente que será atendido pelo sistema de transporte</p>
        </div>
        
        {messages_html}
        
        <div class="card">
            <form method="POST">
                <div class="form-row">
                    <div class="form-group">
                        <label for="nome">Nome Completo *</label>
                        <input type="text" id="nome" name="nome" required>
                    </div>
                    <div class="form-group">
                        <label for="cpf">CPF *</label>
                        <input type="text" id="cpf" name="cpf" placeholder="000.000.000-00" required>
                    </div>
                </div>
                
                <div class="form-row">
                    <div class="form-group">
                        <label for="telefone">Telefone *</label>
                        <input type="tel" id="telefone" name="telefone" placeholder="(00) 00000-0000" required>
                    </div>
                    <div class="form-group">
                        <label for="data_nascimento">Data de Nascimento *</label>
                        <input type="date" id="data_nascimento" name="data_nascimento" required>
                    </div>
                </div>
                
                <!-- 🆕 ENDEREÇO ESTRUTURADO COM VIACEP -->
                <h4 style="color: var(--primary-color); margin: 2rem 0 1rem 0; border-bottom: 2px solid var(--border-color); padding-bottom: 0.5rem;">
                    🏠 Endereço Residencial
                </h4>
                
                <div class="form-row">
                    <div class="form-group">
                        <label for="cep">CEP *</label>
                        <input type="text" id="cep" name="cep" placeholder="00000-000" required maxlength="9">
                        <small style="color: #6c757d; font-size: 0.875rem; margin-top: 0.25rem; display: block;">
                            Digite o CEP para preenchimento automático do endereço
                        </small>
                    </div>
                    <div class="form-group">
                        <label for="uf">Estado *</label>
                        <input type="text" id="uf" name="uf" placeholder="SP" required maxlength="2" style="text-transform: uppercase;">
                    </div>
                </div>
                
                <div class="form-row">
                    <div class="form-group">
                        <label for="logradouro">Logradouro *</label>
                        <input type="text" id="logradouro" name="logradouro" placeholder="Rua, Avenida, Praça..." required>
                    </div>
                    <div class="form-group">
                        <label for="numero">Número *</label>
                        <input type="text" id="numero" name="numero" placeholder="123" required>
                    </div>
                </div>
                
                <div class="form-row">
                    <div class="form-group">
                        <label for="complemento">Complemento</label>
                        <input type="text" id="complemento" name="complemento" placeholder="Apto, Casa, Bloco...">
                    </div>
                    <div class="form-group">
                        <label for="bairro">Bairro *</label>
                        <input type="text" id="bairro" name="bairro" required>
                    </div>
                </div>
                
                <div class="form-group">
                    <label for="cidade">Cidade *</label>
                    <input type="text" id="cidade" name="cidade" required>
                </div>
                
                <!-- OUTROS DADOS -->
                <h4 style="color: var(--primary-color); margin: 2rem 0 1rem 0; border-bottom: 2px solid var(--border-color); padding-bottom: 0.5rem;">
                    📄 Documentos e Observações
                </h4>
                
                <div class="form-group">
                    <label for="cartao_sus">Cartão SUS</label>
                    <input type="text" id="cartao_sus" name="cartao_sus" placeholder="000 0000 0000 0000">
                </div>
                
                <div class="form-group">
                    <label for="observacoes">Necessidades Especiais / Observações</label>
                    <textarea id="observacoes" name="observacoes" rows="4" placeholder="Ex: Cadeirante, necessita maca, acompanhante, etc."></textarea>
                </div>
                
                <div style="margin-top: 2rem;">
                    <button type="submit" class="btn btn-success">💾 Salvar Paciente</button>
                    <a href="{url_for('pacientes')}" class="btn btn-secondary" style="margin-left: 1rem;">❌ Cancelar</a>
                </div>
            </form>
        </div>
        
        <!-- 🆕 INCLUIR VIACEP -->
        <script src="/static/js/viacep.js"></script>
        '''
    return gerar_layout_base("Cadastrar Paciente", conteudo, "pacientes")
             
             
    # ===== VEÍCULOS =====
    @app.route('/veiculos')
    @login_required
    def veiculos():
        veiculos_lista = Veiculo.query.filter_by(ativo=True).order_by(Veiculo.data_cadastro.desc()).all()
        
        veiculos_html = ""
        if veiculos_lista:
            veiculos_html = '''
            <div class="card">
                <h3 style="color: var(--primary-color); margin-bottom: 1rem;">🚗 Veículos Cadastrados</h3>
                <div style="overflow-x: auto;">
                    <table style="width: 100%; border-collapse: collapse;">
                        <thead>
                            <tr style="background: var(--color-95);">
                                <th style="padding: 0.75rem; text-align: left; border-bottom: 2px solid var(--primary-color);">Placa</th>
                                <th style="padding: 0.75rem; text-align: left; border-bottom: 2px solid var(--primary-color);">Marca/Modelo</th>
                                <th style="padding: 0.75rem; text-align: left; border-bottom: 2px solid var(--primary-color);">Tipo</th>
                                <th style="padding: 0.75rem; text-align: left; border-bottom: 2px solid var(--primary-color);">Ano</th>
                                <th style="padding: 0.75rem; text-align: left; border-bottom: 2px solid var(--primary-color);">Adaptado PCD</th>
                            </tr>
                        </thead>
                        <tbody>
            '''
            for veiculo in veiculos_lista:
                # Contar agendamentos do veículo
                total_agendamentos = Agendamento.query.filter_by(veiculo_id=veiculo.id).count()
                
                # Botões de ação baseados em permissões
                acoes_html = ""
                if current_user.can_edit():
                    acoes_html += f'<a href="/veiculos/editar/{veiculo.id}" class="btn btn-warning" style="padding: 0.25rem 0.5rem; font-size: 0.875rem; margin-right: 0.25rem;">✏️ Editar</a>'
                
                if current_user.can_delete():
                    if total_agendamentos == 0:
                        acoes_html += f'<a href="/veiculos/excluir/{veiculo.id}" class="btn" style="background: var(--danger-color); color: white; padding: 0.25rem 0.5rem; font-size: 0.875rem;" onclick="return confirmarExclusao(\'veículo\')">🗑️ Excluir</a>'
                    else:
                        acoes_html += f'<span class="btn" style="background: var(--gray-color); color: white; padding: 0.25rem 0.5rem; font-size: 0.875rem; cursor: not-allowed;" title="Veículo possui {total_agendamentos} agendamento(s)">🔒 Bloqueado</span>'
                
                if not acoes_html:
                    acoes_html = '<span style="color: var(--gray-color); font-size: 0.875rem;">Visualização</span>'
                
                veiculos_html += f'''
                            <tr>
                                <td style="padding: 0.75rem; border-bottom: 1px solid var(--border-color);">{veiculo.placa}</td>
                                <td style="padding: 0.75rem; border-bottom: 1px solid var(--border-color);">{veiculo.marca} {veiculo.modelo}</td>
                                <td style="padding: 0.75rem; border-bottom: 1px solid var(--border-color);">{veiculo.tipo.replace('_', ' ').title()}</td>
                                <td style="padding: 0.75rem; border-bottom: 1px solid var(--border-color);">{veiculo.ano}</td>
                                <td style="padding: 0.75rem; border-bottom: 1px solid var(--border-color);">{'✅ Sim' if veiculo.adaptado else '❌ Não'}</td>
                                <td style="padding: 0.75rem; border-bottom: 1px solid var(--border-color); text-align: center;">{total_agendamentos}</td>
                                <td style="padding: 0.75rem; border-bottom: 1px solid var(--border-color);">
                                    {acoes_html}
                                </td>
                            </tr>
                '''
            veiculos_html += '''
                        </tbody>
                    </table>
                </div>
            </div>
            '''
        
        conteudo = f'''
        <div class="page-header">
            <h2>🚗 Gerenciamento de Veículos</h2>
            <p>Controle da frota municipal de transporte de pacientes</p>
            <div style="margin-top: 1rem;">
                <a href="{url_for('veiculos_cadastrar')}" class="btn">🚗 Cadastrar Novo Veículo</a>
            </div>
        </div>
        
        {veiculos_html}
        
        {f'<div class="card"><div class="coming-soon"><div class="icon">🚗</div><h3>Nenhum veículo cadastrado</h3><p>Comece cadastrando o primeiro veículo da frota!</p></div></div>' if not veiculos_lista else ''}
        
         <script>
            function confirmarExclusao(tipo) {{
                return confirm("Tem certeza que deseja excluir este " + tipo + "? Esta ação não pode ser desfeita!");
            }}
        </script>
      '''
        return gerar_layout_base("Veículos", conteudo, "veiculos")
    
    
    
    @app.route('/veiculos/cadastrar', methods=['GET', 'POST'])
    @login_required
    def veiculos_cadastrar():
        if request.method == 'POST':
            try:
                # Extrair dados do formulário
                placa = request.form.get('placa', '').strip().upper()
                marca = request.form.get('marca', '').strip()
                modelo = request.form.get('modelo', '').strip()
                ano = int(request.form.get('ano', 0))
                cor = request.form.get('cor', '').strip()
                tipo = request.form.get('tipo', '').strip()
                capacidade = request.form.get('capacidade')
                adaptado = request.form.get('adaptado') == 'sim'
                observacoes = request.form.get('observacoes', '').strip()
                
                # Validação básica
                if not all([placa, marca, modelo, ano, tipo]):
                    flash('Por favor, preencha todos os campos obrigatórios!', 'error')
                    return redirect(url_for('veiculos_cadastrar'))
                
                # Verificar se placa já existe
                if Veiculo.query.filter_by(placa=placa).first():
                    flash('Placa já cadastrada no sistema!', 'error')
                    return redirect(url_for('veiculos_cadastrar'))
                
                # Criar novo veículo
                veiculo = Veiculo(
                    placa=placa,
                    marca=marca,
                    modelo=modelo,
                    ano=ano,
                    cor=cor if cor else None,
                    tipo=tipo,
                    capacidade=int(capacidade) if capacidade else None,
                    adaptado=adaptado,
                    observacoes=observacoes if observacoes else None
                )
                
                db.session.add(veiculo)
                db.session.commit()
                
                flash(f'Veículo "{placa}" cadastrado com sucesso!', 'success')
                return redirect(url_for('veiculos'))
                
            except Exception as e:
                db.session.rollback()
                flash(f'Erro ao cadastrar veículo: {str(e)}', 'error')
                print(f"❌ Erro ao cadastrar veículo: {e}")
        
        # Gerar alertas de mensagens flash
        messages_html = ""
        for category, message in get_flashed_messages(with_categories=True):
            alert_class = f"alert-{category}"
            messages_html += f'<div class="alert {alert_class}">{message}</div>'
        
        conteudo = f'''
        <div class="breadcrumb">
            <a href="{url_for('dashboard')}">Dashboard</a> > 
            <a href="{url_for('veiculos')}">Veículos</a> > 
            Cadastrar Novo Veículo
        </div>
        
        <div class="page-header">
            <h2>🚗 Cadastrar Novo Veículo</h2>
            <p>Registre um novo veículo na frota municipal</p>
        </div>
        
        {messages_html}
        
        <div class="card">
            <form method="POST">
                <div class="form-row">
                    <div class="form-group">
                        <label for="placa">Placa *</label>
                        <input type="text" id="placa" name="placa" placeholder="ABC-1234" required style="text-transform: uppercase;">
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
                    <a href="{url_for('veiculos')}" class="btn btn-secondary" style="margin-left: 1rem;">❌ Cancelar</a>
                </div>
            </form>
        </div>
        '''
        return gerar_layout_base("Cadastrar Veículo", conteudo, "veiculos")
    
    # ===== MOTORISTAS =====
    @app.route('/motoristas')
    @login_required
    def motoristas():
        motoristas_lista = Motorista.query.order_by(Motorista.data_cadastro.desc()).all()
        
        motoristas_html = ""
        if motoristas_lista:
            motoristas_html = '''
            <div class="card">
                <h3 style="color: var(--primary-color); margin-bottom: 1rem;">👨‍💼 Motoristas Cadastrados</h3>
                <div style="overflow-x: auto;">
                    <table style="width: 100%; border-collapse: collapse;">
                        <thead>
                            <tr style="background: var(--color-95);">
                                <th style="padding: 0.75rem; text-align: left; border-bottom: 2px solid var(--primary-color);">Nome</th>
                                <th style="padding: 0.75rem; text-align: left; border-bottom: 2px solid var(--primary-color);">CNH</th>
                                <th style="padding: 0.75rem; text-align: left; border-bottom: 2px solid var(--primary-color);">Categoria</th>
                                <th style="padding: 0.75rem; text-align: left; border-bottom: 2px solid var(--primary-color);">Status</th>
                                <th style="padding: 0.75rem; text-align: left; border-bottom: 2px solid var(--primary-color);">Vencimento CNH</th>
                                <th style="padding: 0.75rem; text-align: left; border-bottom: 2px solid var(--primary-color);">Agendamentos</th>
                                <th style="padding: 0.75rem; text-align: left; border-bottom: 2px solid var(--primary-color);">Ações</th>
                            </tr>
                        </thead>
                        <tbody>
            '''
            for motorista in motoristas_lista:
                # Contar agendamentos do motorista
                total_agendamentos = Agendamento.query.filter_by(motorista_id=motorista.id).count()
                
                status_color = {
                    'ativo': 'color: var(--success-color);',
                    'inativo': 'color: var(--gray-color);',
                    'ferias': 'color: var(--warning-color);',
                    'licenca': 'color: var(--info-color);'
                }.get(motorista.status, '')
                
                # Botões de ação baseados em permissões
                acoes_html = ""
                if current_user.can_edit():
                    acoes_html += f'<a href="/motoristas/editar/{motorista.id}" class="btn btn-warning" style="padding: 0.25rem 0.5rem; font-size: 0.875rem; margin-right: 0.25rem;">✏️ Editar</a>'
                
                if current_user.can_delete():
                    if total_agendamentos == 0:
                        acoes_html += f'<a href="/motoristas/excluir/{motorista.id}" class="btn" style="background: var(--danger-color); color: white; padding: 0.25rem 0.5rem; font-size: 0.875rem;" onclick="return confirmarExclusao(\'motorista\')">🗑️ Excluir</a>'
                    else:
                        acoes_html += f'<span class="btn" style="background: var(--gray-color); color: white; padding: 0.25rem 0.5rem; font-size: 0.875rem; cursor: not-allowed;" title="Motorista possui {total_agendamentos} agendamento(s)">🔒 Bloqueado</span>'
                
                if not acoes_html:
                    acoes_html = '<span style="color: var(--gray-color); font-size: 0.875rem;">Visualização</span>'
                
                motoristas_html += f'''
                            <tr>
                                <td style="padding: 0.75rem; border-bottom: 1px solid var(--border-color);">{motorista.nome}</td>
                                <td style="padding: 0.75rem; border-bottom: 1px solid var(--border-color);">{motorista.cnh}</td>
                                <td style="padding: 0.75rem; border-bottom: 1px solid var(--border-color);">{motorista.categoria_cnh}</td>
                                <td style="padding: 0.75rem; border-bottom: 1px solid var(--border-color); {status_color}">{motorista.status.title()}</td>
                                <td style="padding: 0.75rem; border-bottom: 1px solid var(--border-color);">{motorista.vencimento_cnh.strftime('%d/%m/%Y')}</td>
                                <td style="padding: 0.75rem; border-bottom: 1px solid var(--border-color); text-align: center;">{total_agendamentos}</td>
                                <td style="padding: 0.75rem; border-bottom: 1px solid var(--border-color);">
                                    {acoes_html}
                                </td>
                            </tr>
                '''
            motoristas_html += '''
                        </tbody>
                    </table>
                </div>
            </div>
            '''
        
        conteudo = f'''
        <div class="page-header">
            <h2>👨‍💼 Gerenciamento de Motoristas</h2>
            <p>Cadastro e controle dos motoristas do sistema</p>
            <div style="margin-top: 1rem;">
                <a href="{url_for('motoristas_cadastrar')}" class="btn">👨‍💼 Cadastrar Novo Motorista</a>
            </div>
        </div>
        
        {motoristas_html}
        
        {f'<div class="card"><div class="coming-soon"><div class="icon">👨‍💼</div><h3>Nenhum motorista cadastrado</h3><p>Comece cadastrando o primeiro motorista!</p></div></div>' if not motoristas_lista else ''}
        
        <script>
            function confirmarExclusao(tipo) {{
                return confirm("Tem certeza que deseja excluir este " + tipo + "? Esta ação não pode ser desfeita!");
            }}
        </script>
        
        '''
        return gerar_layout_base("Motoristas", conteudo, "motoristas")
    
    @app.route('/motoristas/cadastrar', methods=['GET', 'POST'])
    @login_required
    def motoristas_cadastrar():
        if request.method == 'POST':
            try:
                # Extrair dados do formulário
                nome = request.form.get('nome', '').strip()
                cpf = request.form.get('cpf', '').strip()
                telefone = request.form.get('telefone', '').strip()
                data_nascimento = request.form.get('data_nascimento')
                cnh = request.form.get('cnh', '').strip()
                categoria_cnh = request.form.get('categoria_cnh', '').strip()
                vencimento_cnh = request.form.get('vencimento_cnh')
                endereco = request.form.get('endereco', '').strip()
                status = request.form.get('status', 'ativo').strip()
                observacoes = request.form.get('observacoes', '').strip()
                
                # Validação básica
                if not all([nome, cpf, telefone, data_nascimento, cnh, categoria_cnh, vencimento_cnh]):
                    flash('Por favor, preencha todos os campos obrigatórios!', 'error')
                    return redirect(url_for('motoristas_cadastrar'))
                
                # Verificar se CPF ou CNH já existem
                if Motorista.query.filter_by(cpf=cpf).first():
                    flash('CPF já cadastrado no sistema!', 'error')
                    return redirect(url_for('motoristas_cadastrar'))
                
                if Motorista.query.filter_by(cnh=cnh).first():
                    flash('CNH já cadastrada no sistema!', 'error')
                    return redirect(url_for('motoristas_cadastrar'))
                
                # Converter datas
                data_nascimento = datetime.strptime(data_nascimento, '%Y-%m-%d').date()
                vencimento_cnh = datetime.strptime(vencimento_cnh, '%Y-%m-%d').date()
                
                # Criar novo motorista
                motorista = Motorista(
                    nome=nome,
                    cpf=cpf,
                    telefone=telefone,
                    data_nascimento=data_nascimento,
                    cnh=cnh,
                    categoria_cnh=categoria_cnh,
                    vencimento_cnh=vencimento_cnh,
                    endereco=endereco if endereco else None,
                    status=status,
                    observacoes=observacoes if observacoes else None
                )
                
                db.session.add(motorista)
                db.session.commit()
                
                flash(f'Motorista "{nome}" cadastrado com sucesso!', 'success')
                return redirect(url_for('motoristas'))
                
            except Exception as e:
                db.session.rollback()
                flash(f'Erro ao cadastrar motorista: {str(e)}', 'error')
                print(f"❌ Erro ao cadastrar motorista: {e}")
        
        # Gerar alertas de mensagens flash
        messages_html = ""
        for category, message in get_flashed_messages(with_categories=True):
            alert_class = f"alert-{category}"
            messages_html += f'<div class="alert {alert_class}">{message}</div>'
        
        conteudo = f'''
        <div class="breadcrumb">
            <a href="{url_for('dashboard')}">Dashboard</a> > 
            <a href="{url_for('motoristas')}">Motoristas</a> > 
            Cadastrar Novo Motorista
        </div>
        
        <div class="page-header">
            <h2>👨‍💼 Cadastrar Novo Motorista</h2>
            <p>Registre um novo motorista no sistema</p>
        </div>
        
        {messages_html}
        
        <div class="card">
            <form method="POST">
                <div class="form-row">
                    <div class="form-group">
                        <label for="nome">Nome Completo *</label>
                        <input type="text" id="nome" name="nome" required>
                    </div>
                    <div class="form-group">
                        <label for="cpf">CPF *</label>
                        <input type="text" id="cpf" name="cpf" placeholder="000.000.000-00" required>
                    </div>
                </div>
                
                <div class="form-row">
                    <div class="form-group">
                        <label for="telefone">Telefone *</label>
                        <input type="tel" id="telefone" name="telefone" placeholder="(00) 00000-0000" required>
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
                    <a href="{url_for('motoristas')}" class="btn btn-secondary" style="margin-left: 1rem;">❌ Cancelar</a>
                </div>
            </form>
        </div>
        '''
        return gerar_layout_base("Cadastrar Motorista", conteudo, "motoristas")
    
    # ===== AGENDAMENTOS =====
    @app.route('/agendamentos')
    @login_required
    def agendamentos():
        agendamentos_lista = Agendamento.query.order_by(Agendamento.data.desc(), Agendamento.hora.desc()).all()
        
        agendamentos_html = ""
        if agendamentos_lista:
            agendamentos_html = '''
            <div class="card">
                <h3 style="color: var(--primary-color); margin-bottom: 1rem;">📅 Agendamentos</h3>
                <div style="overflow-x: auto;">
                    <table style="width: 100%; border-collapse: collapse;">
                        <thead>
                            <tr style="background: var(--color-95);">
                                <th style="padding: 0.75rem; text-align: left; border-bottom: 2px solid var(--primary-color);">Data</th>
                                <th style="padding: 0.75rem; text-align: left; border-bottom: 2px solid var(--primary-color);">Hora</th>
                                <th style="padding: 0.75rem; text-align: left; border-bottom: 2px solid var(--primary-color);">Paciente</th>
                                <th style="padding: 0.75rem; text-align: left; border-bottom: 2px solid var(--primary-color);">Tipo</th>
                                <th style="padding: 0.75rem; text-align: left; border-bottom: 2px solid var(--primary-color);">Especialidade</th>
                                <th style="padding: 0.75rem; text-align: left; border-bottom: 2px solid var(--primary-color);">Motorista</th>
                                <th style="padding: 0.75rem; text-align: left; border-bottom: 2px solid var(--primary-color);">Status</th>
                                <th style="padding: 0.75rem; text-align: left; border-bottom: 2px solid var(--primary-color);">Ações</th>
                            </tr>
                        </thead>
                        <tbody>
            '''
            for agendamento in agendamentos_lista:
                paciente = Paciente.query.get(agendamento.paciente_id)
                veiculo = Veiculo.query.get(agendamento.veiculo_id) if agendamento.veiculo_id else None
                motorista = Motorista.query.get(agendamento.motorista_id) if agendamento.motorista_id else None
                
                # Cor do status
                status_color = {
                    'agendado': 'color: var(--info-color);',
                    'em_andamento': 'color: var(--warning-color);',
                    'concluido': 'color: var(--success-color);',
                    'cancelado': 'color: var(--danger-color);'
                }.get(agendamento.status, '')
                
                # Botões de ação baseados em permissões
                acoes_html = ""
                if current_user.can_edit():
                    acoes_html += f'<a href="/agendamentos/editar/{agendamento.id}" class="btn btn-warning" style="padding: 0.25rem 0.5rem; font-size: 0.875rem; margin-right: 0.25rem;">✏️ Editar</a>'
                
                if current_user.can_delete():
                    acoes_html += f'<a href="/agendamentos/excluir/{agendamento.id}" class="btn" style="background: var(--danger-color); color: white; padding: 0.25rem 0.5rem; font-size: 0.875rem;" onclick="return confirmarExclusao(\'agendamento\')">🗑️ Excluir</a>'
                
                if not acoes_html:
                    acoes_html = '<span style="color: var(--gray-color); font-size: 0.875rem;">Visualização</span>'
                
                agendamentos_html += f'''
                            <tr>
                                <td style="padding: 0.75rem; border-bottom: 1px solid var(--border-color);">{agendamento.data.strftime('%d/%m/%Y')}</td>
                                <td style="padding: 0.75rem; border-bottom: 1px solid var(--border-color);">{agendamento.hora.strftime('%H:%M')}</td>
                                <td style="padding: 0.75rem; border-bottom: 1px solid var(--border-color);">{paciente.nome if paciente else 'N/A'}</td>
                                <td style="padding: 0.75rem; border-bottom: 1px solid var(--border-color);">{agendamento.tipo_transporte.replace('_', ' ').title()}</td>
                                <td style="padding: 0.75rem; border-bottom: 1px solid var(--border-color);">{agendamento.especialidade or 'N/A'}</td>
                                <td style="padding: 0.75rem; border-bottom: 1px solid var(--border-color);">{motorista.nome if motorista else 'Automático'}</td>
                                <td style="padding: 0.75rem; border-bottom: 1px solid var(--border-color); {status_color}">{agendamento.status.replace('_', ' ').title()}</td>
                                <td style="padding: 0.75rem; border-bottom: 1px solid var(--border-color);">
                                    {acoes_html}
                                </td>
                            </tr>
                '''
            agendamentos_html += '''
                        </tbody>
                    </table>
                </div>
            </div>
            <script>
            function confirmarExclusao(tipo) {
                    return confirm(`Tem certeza que deseja excluir este ${tipo}? Esta ação não pode ser desfeita!`);
                }
            </script>
            '''
        
        conteudo = f'''
        <div class="page-header">
            <h2>📅 Gerenciamento de Agendamentos</h2>
            <p>Programação e controle de transportes de pacientes</p>
            <div style="margin-top: 1rem;">
                <a href="{url_for('agendamentos_novo')}" class="btn">📅 Novo Agendamento</a>
            </div>
        </div>
        
        {agendamentos_html}
        
        {f'<div class="card"><div class="coming-soon"><div class="icon">📅</div><h3>Nenhum agendamento criado</h3><p>Comece criando o primeiro agendamento!</p></div></div>' if not agendamentos_lista else ''}
        
           /*
            <script>
                function confirmarExclusao(tipo) {{
                    const confirmacao = confirm('Tem certeza que deseja excluir este ' + tipo + '?\\n\\nEsta ação não pode ser desfeita!');
                    return confirmacao;
                }}
                
                // Adicionar eventos aos botões de exclusão
                document.addEventListener('DOMContentLoaded', function() {{
                    const botoesExcluir = document.querySelectorAll('a[href*="/excluir/"]');
                    botoesExcluir.forEach(botao => {{
                        botao.addEventListener('click', function(e) {{
                            const tipo = this.href.includes('agendamentos') ? 'agendamento' : 'item';
                            if (!confirmarExclusao(tipo)) {{
                                e.preventDefault();
                                return false;
                            }}
                        }});
                    }});
                }});
            </script>
            */
            <script>
                function confirmarExclusao(tipo) {{
                    return confirm("Tem certeza que deseja excluir este " + tipo + "? Esta ação não pode ser desfeita!");
                }}
                onclick="return confirmarExclusao('agendamento')"
            </script>
        '''
           
        return gerar_layout_base("Agendamentos", conteudo, "agendamentos")
        
        
       
   
    @app.route('/agendamentos/novo', methods=['GET', 'POST'])
    @login_required
    def agendamentos_novo():
        if request.method == 'POST':
            try:
                # Extrair dados do formulário
                paciente_id = int(request.form.get('paciente_id', 0))
                tipo_transporte = request.form.get('tipo_transporte', '').strip()
                especialidade = request.form.get('especialidade', '').strip()
                data = request.form.get('data')
                hora = request.form.get('hora')
                origem = request.form.get('origem', '').strip()
                destino = request.form.get('destino', '').strip()
                veiculo_id = request.form.get('veiculo_id')
                motorista_id = request.form.get('motorista_id')
                observacoes = request.form.get('observacoes', '').strip()
                
                # Validação básica (agora inclui motorista como obrigatório)
                if not all([paciente_id, tipo_transporte, data, hora, origem, destino, motorista_id]):
                    flash('Por favor, preencha todos os campos obrigatórios (incluindo motorista)!', 'error')
                    return redirect(url_for('agendamentos_novo'))
                
                # Converter data e hora
                data = datetime.strptime(data, '%Y-%m-%d').date()
                hora = datetime.strptime(hora, '%H:%M').time()
                
                # Criar novo agendamento
                agendamento = Agendamento(
                    paciente_id=paciente_id,
                    tipo_transporte=tipo_transporte,
                    especialidade=especialidade if especialidade else None,
                    data=data,
                    hora=hora,
                    origem=origem,
                    destino=destino,
                    veiculo_id=int(veiculo_id) if veiculo_id else None,  # OPCIONAL
                    motorista_id=int(motorista_id),  # OBRIGATÓRIO
                    observacoes=observacoes if observacoes else None
                )
                
                db.session.add(agendamento)
                db.session.commit()
                
                # Log detalhado
                motorista = Motorista.query.get(motorista_id)
                veiculo = Veiculo.query.get(veiculo_id) if veiculo_id else None
                
                print(f"✅ Agendamento criado: {agendamento.id} para {data} às {hora}")
                print(f"👨‍💼 Motorista selecionado: {motorista.nome if motorista else 'N/A'}")
                if veiculo:
                    print(f"🚗 Veículo selecionado: {veiculo.marca} {veiculo.modelo} - {veiculo.placa}")
                else:
                    print(f"🚗 Veículo: Sistema escolherá automaticamente")
                if especialidade:
                    print(f"📝 Especialidade: {especialidade}")
                
                flash('Agendamento criado com sucesso!', 'success')
                return redirect(url_for('agendamentos'))
                
            except Exception as e:
                db.session.rollback()
                flash(f'Erro ao criar agendamento: {str(e)}', 'error')
                print(f"❌ Erro ao criar agendamento: {e}")
        
        # Buscar dados para os selects
        pacientes = Paciente.query.filter_by(ativo=True).order_by(Paciente.nome).all()
        veiculos = Veiculo.query.filter_by(ativo=True).order_by(Veiculo.placa).all()
        motoristas = Motorista.query.filter_by(status='ativo').order_by(Motorista.nome).all()
        
        # Gerar options para os selects
        pacientes_options = ""
        for p in pacientes:
            pacientes_options += f'<option value="{p.id}">{p.nome} - CPF: {p.cpf}</option>'
        
        veiculos_options = ""
        for v in veiculos:
            veiculos_options += f'<option value="{v.id}">{v.marca} {v.modelo} - {v.placa}</option>'
        
        motoristas_options = ""
        for m in motoristas:
            motoristas_options += f'<option value="{m.id}">{m.nome} - CNH: {m.categoria_cnh}</option>'
        
        # Gerar alertas de mensagens flash
        messages_html = ""
        for category, message in get_flashed_messages(with_categories=True):
            alert_class = f"alert-{category}"
            messages_html += f'<div class="alert {alert_class}">{message}</div>'
        
        # Data de hoje no formato YYYY-MM-DD
        hoje = date.today().strftime('%Y-%m-%d')
        
        # URLs usando caminhos diretos para evitar problemas de contexto
        dashboard_url = "/dashboard"
        agendamentos_url = "/agendamentos"
        
        conteudo = f'''
        <div class="breadcrumb">
            <a href="{dashboard_url}">Dashboard</a> > 
            <a href="{agendamentos_url}">Agendamentos</a> > 
            Novo Agendamento
        </div>
        
        <div class="page-header">
            <h2>📅 Novo Agendamento</h2>
            <p>Agende um novo transporte de paciente</p>
        </div>
        
        {messages_html}
        
        <div class="card">
            <form method="POST">
                <div class="form-row">
                    <div class="form-group">
                        <label for="paciente_id">Paciente *</label>
                        <select id="paciente_id" name="paciente_id" required>
                            <option value="">Selecione o paciente...</option>
                            {pacientes_options}
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
                
                <!-- CAMPO DE ESPECIALIDADE -->
                <div class="form-group">
                    <label for="especialidade">Especialidade Médica</label>
                    <div id="especialidade-container">
                        <input type="text" id="especialidade" name="especialidade" placeholder="">
                    </div>
                </div>
                
                <div class="form-row">
                    <div class="form-group">
                        <label for="data">Data *</label>
                        <input type="date" id="data" name="data" value="{hoje}" required>
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
                    <div id="destino-container">
                        <input type="text" id="destino" name="destino" placeholder="" required>
                    </div>
                </div>
                
                <!-- CAMPOS DE VEÍCULO E MOTORISTA ATUALIZADOS -->
                <div class="form-row">
                    <div class="form-group">
                        <label for="veiculo_id">Veículo</label>
                        <select id="veiculo_id" name="veiculo_id">
                            <option value="">🚗 Sistema escolherá automaticamente</option>
                            {veiculos_options}
                        </select>
                        <small style="color: #6c757d; font-size: 0.875rem; margin-top: 0.25rem; display: block;">
                            Opcional: Deixe em branco para seleção automática baseada na disponibilidade
                        </small>
                    </div>
                    <div class="form-group">
                        <label for="motorista_id">Motorista *</label>
                        <select id="motorista_id" name="motorista_id" required>
                            <option value="">Selecione o motorista...</option>
                            {motoristas_options}
                        </select>
                        <small style="color: #dc3545; font-size: 0.875rem; margin-top: 0.25rem; display: block;">
                            Obrigatório: Escolha qual motorista fará o transporte
                        </small>
                    </div>
                </div>
                
                <div class="form-group">
                    <label for="observacoes">Observações</label>
                    <textarea id="observacoes" name="observacoes" rows="3" placeholder="Informações adicionais sobre o transporte"></textarea>
                </div>
                
                <div style="margin-top: 2rem;">
                    <button type="submit" class="btn btn-success">📅 Agendar Transporte</button>
                    <a href="{agendamentos_url}" class="btn btn-secondary" style="margin-left: 1rem;">❌ Cancelar</a>
                </div>
            </form>
        </div>
        
        <script src="/static/js/cidades.js"></script>
        <script src="/static/js/especialidades.js"></script>
        <style>
            .cidade-select, .especialidade-select {{
                border: 2px solid var(--border-color);
                border-radius: 0.5rem;
                padding: 0.75rem;
                font-size: 1rem;
                background: white;
                width: 100%;
                box-sizing: border-box;
            }}
            
            .cidade-select:focus, .especialidade-select:focus {{
                border-color: var(--input-focus);
                outline: none;
                box-shadow: 0 0 0 3px var(--input-focus-shadow);
            }}
            
            #destino-container input, #especialidade-container input {{
                margin-top: 0.5rem;
            }}
        </style>
        '''
        return gerar_layout_base("Novo Agendamento", conteudo, "agendamentos")    
    
    # ===== RELATÓRIOS =====
    @app.route('/relatorios')
    @login_required
    def relatorios():
        # Obter parâmetros de filtro
        filtro_tipo = request.args.get('tipo', 'pacientes')
        data_inicio = request.args.get('data_inicio', '')
        data_fim = request.args.get('data_fim', '')
        status_filtro = request.args.get('status', '')
        
        # Definir datas padrão (últimos 30 dias)
        if not data_inicio:
            data_inicio = (date.today() - timedelta(days=30)).strftime('%Y-%m-%d')
        if not data_fim:
            data_fim = date.today().strftime('%Y-%m-%d')
        
        # Buscar dados
        pacientes_dados = []
        veiculos_dados = []
        motoristas_dados = []
        agendamentos_dados = []
        usuarios_dados = []
        
        try:
            # Relatório de Pacientes
            pacientes = Paciente.query.filter_by(ativo=True).order_by(Paciente.nome).all()
            for p in pacientes:
                total_agendamentos = Agendamento.query.filter_by(paciente_id=p.id).count()
                pacientes_dados.append({
                    'nome': p.nome,
                    'cpf': p.cpf,
                    'telefone': p.telefone,
                    'endereco': p.endereco,
                    'cartao_sus': p.cartao_sus or '-',
                    'total_agendamentos': total_agendamentos,
                    'data_cadastro': p.data_cadastro.strftime('%d/%m/%Y'),
                    'observacoes': p.observacoes or '-'
                })
            
            # Relatório de Veículos
            veiculos = Veiculo.query.filter_by(ativo=True).order_by(Veiculo.placa).all()
            for v in veiculos:
                total_agendamentos = Agendamento.query.filter_by(veiculo_id=v.id).count()
                veiculos_dados.append({
                    'placa': v.placa,
                    'marca_modelo': f"{v.marca} {v.modelo}",
                    'ano': v.ano,
                    'tipo': v.tipo.replace('_', ' ').title(),
                    'capacidade': v.capacidade or '-',
                    'adaptado': 'Sim' if v.adaptado else 'Não',
                    'total_agendamentos': total_agendamentos,
                    'status': 'Ativo'
                })
            
            # Relatório de Motoristas
            motoristas = Motorista.query.order_by(Motorista.nome).all()
            for m in motoristas:
                total_agendamentos = Agendamento.query.filter_by(motorista_id=m.id).count()
                # Verificar se CNH está vencida
                cnh_status = 'Válida'
                if m.vencimento_cnh < date.today():
                    cnh_status = 'Vencida'
                elif m.vencimento_cnh <= date.today() + timedelta(days=30):
                    cnh_status = 'Vence em breve'
                
                motoristas_dados.append({
                    'nome': m.nome,
                    'cpf': m.cpf,
                    'telefone': m.telefone,
                    'cnh': m.cnh,
                    'categoria_cnh': m.categoria_cnh,
                    'vencimento_cnh': m.vencimento_cnh.strftime('%d/%m/%Y'),
                    'cnh_status': cnh_status,
                    'status': m.status.title(),
                    'total_agendamentos': total_agendamentos
                })
            
            # Relatório de Agendamentos
            query = Agendamento.query
            if data_inicio and data_fim:
                query = query.filter(Agendamento.data.between(data_inicio, data_fim))
            if status_filtro:
                query = query.filter_by(status=status_filtro)
            
            agendamentos = query.order_by(Agendamento.data.desc(), Agendamento.hora.desc()).all()
            for a in agendamentos:
                motorista_nome = a.motorista.nome if a.motorista else 'Não atribuído'
                veiculo_info = f"{a.veiculo.marca} {a.veiculo.modelo} - {a.veiculo.placa}" if a.veiculo else 'Não atribuído'
                
                agendamentos_dados.append({
                    'data': a.data.strftime('%d/%m/%Y'),
                    'hora': a.hora.strftime('%H:%M'),
                    'paciente': a.paciente.nome,
                    'telefone': a.paciente.telefone,
                    'tipo_transporte': a.tipo_transporte.title(),
                    'origem': a.origem,
                    'destino': a.destino,
                    'motorista': motorista_nome,
                    'veiculo': veiculo_info,
                    'status': a.status.replace('_', ' ').title(),
                    'observacoes': a.observacoes or '-'
                })
            
            # Relatório de Usuários
            usuarios = Usuario.query.order_by(Usuario.nome_completo).all()
            for u in usuarios:
                usuarios_dados.append({
                    'nome': u.nome_completo,
                    'username': u.username,
                    'email': u.email or '-',
                    'tipo': u.tipo_usuario.title(),
                    'status': 'Ativo' if u.ativo else 'Inativo'
                })
            
        except Exception as e:
            print(f"❌ Erro ao gerar relatórios: {e}")
            flash('Erro ao carregar dados dos relatórios.', 'error')
        
        conteudo = f'''
        <div class="page-header">
            <h2>📊 Relatórios Gerenciais</h2>
            <p>Visualize e imprima relatórios completos do sistema</p>
        </div>
        
        <!-- Filtros -->
        <div class="filters no-print">
            <form method="GET" id="filtrosForm">
                <div class="filters-row">
                    <div class="form-group">
                        <label>Período:</label>
                        <input type="date" name="data_inicio" value="{data_inicio}">
                    </div>
                    <div class="form-group">
                        <label>Até:</label>
                        <input type="date" name="data_fim" value="{data_fim}">
                    </div>
                    <div class="form-group">
                        <label>Status Agendamentos:</label>
                        <select name="status">
                            <option value="">Todos</option>
                            <option value="agendado" {"selected" if status_filtro == "agendado" else ""}>Agendado</option>
                            <option value="confirmado" {"selected" if status_filtro == "confirmado" else ""}>Confirmado</option>
                            <option value="em_andamento" {"selected" if status_filtro == "em_andamento" else ""}>Em Andamento</option>
                            <option value="concluido" {"selected" if status_filtro == "concluido" else ""}>Concluído</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <button type="submit" class="btn">🔍 Filtrar</button>
                        <button type="button" class="btn print-btn" onclick="window.print()">🖨️ Imprimir</button>
                    </div>
                </div>
            </form>
        </div>
        
        <!-- Abas dos Relatórios -->
        <div class="tabs no-print">
            <button class="tab active" onclick="showTab('pacientes')">👥 Pacientes ({len(pacientes_dados)})</button>
            <button class="tab" onclick="showTab('agendamentos')">📅 Agendamentos ({len(agendamentos_dados)})</button>
            <button class="tab" onclick="showTab('motoristas')">👨‍💼 Motoristas ({len(motoristas_dados)})</button>
            <button class="tab" onclick="showTab('veiculos')">🚗 Veículos ({len(veiculos_dados)})</button>
            <button class="tab" onclick="showTab('usuarios')">👤 Usuários ({len(usuarios_dados)})</button>
        </div>
        
        <!-- Conteúdo dos Relatórios -->
        
        <!-- Relatório de Pacientes -->
        <div id="pacientes" class="tab-content active">
            <div class="card">
                <h3 style="color: var(--primary-color); margin-bottom: 1rem;">📋 Relatório de Pacientes</h3>
                <p><strong>Total de pacientes ativos:</strong> {len(pacientes_dados)}</p>
                <div class="table-container">
                    <table class="report-table">
                        <thead>
                            <tr>
                                <th>Nome</th>
                                <th>CPF</th>
                                <th>Telefone</th>
                                <th>Endereço</th>
                                <th>Cartão SUS</th>
                                <th>Total Agendamentos</th>
                                <th>Data Cadastro</th>
                                <th>Observações</th>
                            </tr>
                        </thead>
                        <tbody>
                            {"".join([f'''
                            <tr>
                                <td>{p["nome"]}</td>
                                <td>{p["cpf"]}</td>
                                <td>{p["telefone"]}</td>
                                <td>{p["endereco"][:40]}{'...' if len(p["endereco"]) > 40 else ''}</td>
                                <td>{p["cartao_sus"]}</td>
                                <td>{p["total_agendamentos"]}</td>
                                <td>{p["data_cadastro"]}</td>
                                <td>{p["observacoes"][:30]}{'...' if len(p["observacoes"]) > 30 else ''}</td>
                            </tr>
                            ''' for p in pacientes_dados])}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
        
        <!-- Relatório de Agendamentos -->
        <div id="agendamentos" class="tab-content">
            <div class="card">
                <h3 style="color: var(--primary-color); margin-bottom: 1rem;">📅 Relatório de Agendamentos</h3>
                <p><strong>Período:</strong> {datetime.strptime(data_inicio, '%Y-%m-%d').strftime('%d/%m/%Y')} a {datetime.strptime(data_fim, '%Y-%m-%d').strftime('%d/%m/%Y')}</p>
                <p><strong>Total de agendamentos:</strong> {len(agendamentos_dados)}</p>
                <div class="table-container">
                    <table class="report-table">
                        <thead>
                            <tr>
                                <th>Data</th>
                                <th>Hora</th>
                                <th>Paciente</th>
                                <th>Telefone</th>
                                <th>Tipo</th>
                                <th>Origem</th>
                                <th>Destino</th>
                                <th>Motorista</th>
                                <th>Veículo</th>
                                <th>Status</th>
                            </tr>
                        </thead>
                        <tbody>
                            {"".join([f'''
                            <tr>
                                <td>{a["data"]}</td>
                                <td>{a["hora"]}</td>
                                <td>{a["paciente"]}</td>
                                <td>{a["telefone"]}</td>
                                <td>{a["tipo_transporte"]}</td>
                                <td>{a["origem"][:25]}{'...' if len(a["origem"]) > 25 else ''}</td>
                                <td>{a["destino"][:25]}{'...' if len(a["destino"]) > 25 else ''}</td>
                                <td>{a["motorista"]}</td>
                                <td>{a["veiculo"][:20]}{'...' if len(a["veiculo"]) > 20 else ''}</td>
                                <td style="color: {'var(--success-color)' if a['status'] == 'Concluído' else 'var(--warning-color)' if a['status'] == 'Agendado' else 'var(--primary-color)'};">{a["status"]}</td>
                            </tr>
                            ''' for a in agendamentos_dados])}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
        
        <!-- Relatório de Motoristas -->
        <div id="motoristas" class="tab-content">
            <div class="card">
                <h3 style="color: var(--primary-color); margin-bottom: 1rem;">👨‍💼 Relatório de Motoristas</h3>
                <p><strong>Total de motoristas:</strong> {len(motoristas_dados)}</p>
                <div class="table-container">
                    <table class="report-table">
                        <thead>
                            <tr>
                                <th>Nome</th>
                                <th>CPF</th>
                                <th>Telefone</th>
                                <th>CNH</th>
                                <th>Categoria</th>
                                <th>Vencimento CNH</th>
                                <th>Status CNH</th>
                                <th>Status</th>
                                <th>Total Viagens</th>
                            </tr>
                        </thead>
                        <tbody>
                            {"".join([f'''
                            <tr>
                                <td>{m["nome"]}</td>
                                <td>{m["cpf"]}</td>
                                <td>{m["telefone"]}</td>
                                <td>{m["cnh"]}</td>
                                <td>{m["categoria_cnh"]}</td>
                                <td>{m["vencimento_cnh"]}</td>
                                <td style="color: {'var(--danger-color)' if m['cnh_status'] == 'Vencida' else 'var(--warning-color)' if m['cnh_status'] == 'Vence em breve' else 'var(--success-color)'};">{m["cnh_status"]}</td>
                                <td style="color: {'var(--success-color)' if m['status'] == 'Ativo' else 'var(--gray-color)'};">{m["status"]}</td>
                                <td>{m["total_agendamentos"]}</td>
                            </tr>
                            ''' for m in motoristas_dados])}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
        
        <!-- Relatório de Veículos -->
        <div id="veiculos" class="tab-content">
            <div class="card">
                <h3 style="color: var(--primary-color); margin-bottom: 1rem;">🚗 Relatório de Veículos</h3>
                <p><strong>Total de veículos ativos:</strong> {len(veiculos_dados)}</p>
                <div class="table-container">
                    <table class="report-table">
                        <thead>
                            <tr>
                                <th>Placa</th>
                                <th>Marca/Modelo</th>
                                <th>Ano</th>
                                <th>Tipo</th>
                                <th>Capacidade</th>
                                <th>Adaptado PCD</th>
                                <th>Total Transportes</th>
                                <th>Status</th>
                            </tr>
                        </thead>
                        <tbody>
                            {"".join([f'''
                            <tr>
                                <td><strong>{v["placa"]}</strong></td>
                                <td>{v["marca_modelo"]}</td>
                                <td>{v["ano"]}</td>
                                <td>{v["tipo"]}</td>
                                <td>{v["capacidade"]}</td>
                                <td style="color: {'var(--success-color)' if v['adaptado'] == 'Sim' else 'var(--gray-color)'};">{v["adaptado"]}</td>
                                <td>{v["total_agendamentos"]}</td>
                                <td style="color: var(--success-color);">{v["status"]}</td>
                            </tr>
                            ''' for v in veiculos_dados])}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
        
        <!-- Relatório de Usuários -->
        <div id="usuarios" class="tab-content">
            <div class="card">
                <h3 style="color: var(--primary-color); margin-bottom: 1rem;">👤 Relatório de Usuários</h3>
                <p><strong>Total de usuários:</strong> {len(usuarios_dados)}</p>
                <div class="table-container">
                    <table class="report-table">
                        <thead>
                            <tr>
                                <th>Nome Completo</th>
                                <th>Username</th>
                                <th>Email</th>
                                <th>Tipo de Usuário</th>
                                <th>Status</th>
                            </tr>
                        </thead>
                        <tbody>
                            {"".join([f'''
                            <tr>
                                <td>{u["nome"]}</td>
                                <td><strong>{u["username"]}</strong></td>
                                <td>{u["email"]}</td>
                                <td>{u["tipo"]}</td>
                                <td style="color: {'var(--success-color)' if u['status'] == 'Ativo' else 'var(--danger-color)'};">{u["status"]}</td>
                            </tr>
                            ''' for u in usuarios_dados])}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
        
        <script>
            function showTab(tabName) {{
                // Esconder todas as abas
                const contents = document.querySelectorAll('.tab-content');
                contents.forEach(content => content.classList.remove('active'));
                
                const tabs = document.querySelectorAll('.tab');
                tabs.forEach(tab => tab.classList.remove('active'));
                
                // Mostrar aba selecionada
                document.getElementById(tabName).classList.add('active');
                event.target.classList.add('active');
            }}
            
            // Auto-submit do formulário quando alterar filtros
            const form = document.getElementById('filtrosForm');
            const inputs = form.querySelectorAll('input, select');
            inputs.forEach(input => {{
                if (input.type !== 'submit' && !input.classList.contains('btn')) {{
                    input.addEventListener('change', function() {{
                        // Auto-submit após pequeno delay
                        setTimeout(() => form.submit(), 100);
                    }});
                }}
            }});
        </script>
        '''
        
        return gerar_layout_base("Relatórios", conteudo, "relatorios")
    
    @app.route('/logout')
    @login_required
    def logout():
        logout_user()
        session.pop('_flashes', None)
        flash('Logout realizado com sucesso!', 'success')
        return redirect(url_for('login'))


    
    # 🆕 EDIÇÃO DE AGENDAMENTOS
    @app.route('/agendamentos/editar/<int:id>', methods=['GET', 'POST'])
    @edit_required
    def agendamentos_editar(id):
        agendamento = Agendamento.query.get_or_404(id)
        
        if request.method == 'POST':
            try:
                # Extrair dados do formulário
                paciente_id = int(request.form.get('paciente_id', 0))
                tipo_transporte = request.form.get('tipo_transporte', '').strip()
                especialidade = request.form.get('especialidade', '').strip()
                data = request.form.get('data')
                hora = request.form.get('hora')
                origem = request.form.get('origem', '').strip()
                destino = request.form.get('destino', '').strip()
                veiculo_id = request.form.get('veiculo_id')
                motorista_id = request.form.get('motorista_id')
                observacoes = request.form.get('observacoes', '').strip()
                
                # Validação básica
                if not all([paciente_id, tipo_transporte, data, hora, origem, destino, motorista_id]):
                    flash('Por favor, preencha todos os campos obrigatórios!', 'error')
                    return redirect(url_for('agendamentos_editar', id=id))
                
                # Converter data e hora
                data = datetime.strptime(data, '%Y-%m-%d').date()
                hora = datetime.strptime(hora, '%H:%M').time()
                
                # Atualizar agendamento
                agendamento.paciente_id = paciente_id
                agendamento.tipo_transporte = tipo_transporte
                agendamento.especialidade = especialidade if especialidade else None
                agendamento.data = data
                agendamento.hora = hora
                agendamento.origem = origem
                agendamento.destino = destino
                agendamento.veiculo_id = int(veiculo_id) if veiculo_id else None
                agendamento.motorista_id = int(motorista_id)
                agendamento.observacoes = observacoes if observacoes else None
                
                db.session.commit()
                
                flash('Agendamento atualizado com sucesso!', 'success')
                return redirect(url_for('agendamentos'))
                
            except Exception as e:
                db.session.rollback()
                flash(f'Erro ao atualizar agendamento: {str(e)}', 'error')
                print(f"❌ Erro ao atualizar agendamento: {e}")
        
        # Buscar dados para os selects
        pacientes = Paciente.query.filter_by(ativo=True).order_by(Paciente.nome).all()
        veiculos = Veiculo.query.filter_by(ativo=True).order_by(Veiculo.placa).all()
        motoristas = Motorista.query.filter_by(status='ativo').order_by(Motorista.nome).all()
        
        # Gerar options para os selects com dados atuais selecionados
        pacientes_options = ""
        for p in pacientes:
            selected = 'selected' if p.id == agendamento.paciente_id else ''
            pacientes_options += f'<option value="{p.id}" {selected}>{p.nome} - CPF: {p.cpf}</option>'
        
        veiculos_options = ""
        for v in veiculos:
            selected = 'selected' if v.id == agendamento.veiculo_id else ''
            veiculos_options += f'<option value="{v.id}" {selected}>{v.marca} {v.modelo} - {v.placa}</option>'
        
        motoristas_options = ""
        for m in motoristas:
            selected = 'selected' if m.id == agendamento.motorista_id else ''
            motoristas_options += f'<option value="{m.id}" {selected}>{m.nome} - CNH: {m.categoria_cnh}</option>'
        
        # Gerar alertas de mensagens flash
        messages_html = ""
        for category, message in get_flashed_messages(with_categories=True):
            alert_class = f"alert-{category}"
            messages_html += f'<div class="alert {alert_class}">{message}</div>'
        
        # Formatar dados atuais para os campos
        data_atual = agendamento.data.strftime('%Y-%m-%d')
        hora_atual = agendamento.hora.strftime('%H:%M')
        
        conteudo = f'''
        <div class="breadcrumb">
            <a href="/dashboard">Dashboard</a> > 
            <a href="/agendamentos">Agendamentos</a> > 
            Editar Agendamento
        </div>
        
        <div class="page-header">
            <h2>✏️ Editar Agendamento</h2>
            <p>Altere os dados do agendamento #{agendamento.id}</p>
        </div>
        
        {messages_html}
        
        <div class="card">
            <form method="POST">
                <div class="form-row">
                    <div class="form-group">
                        <label for="paciente_id">Paciente *</label>
                        <select id="paciente_id" name="paciente_id" required>
                            <option value="">Selecione o paciente...</option>
                            {pacientes_options}
                        </select>
                    </div>
                    <div class="form-group">
                        <label for="tipo_transporte">Tipo de Transporte *</label>
                        <select id="tipo_transporte" name="tipo_transporte" required>
                            <option value="">Selecione...</option>
                            <option value="consulta" {'selected' if agendamento.tipo_transporte == 'consulta' else ''}>Consulta Médica</option>
                            <option value="exame" {'selected' if agendamento.tipo_transporte == 'exame' else ''}>Exame</option>
                            <option value="cirurgia" {'selected' if agendamento.tipo_transporte == 'cirurgia' else ''}>Cirurgia</option>
                            <option value="tratamento" {'selected' if agendamento.tipo_transporte == 'tratamento' else ''}>Tratamento</option>
                            <option value="emergencia" {'selected' if agendamento.tipo_transporte == 'emergencia' else ''}>Emergência</option>
                        </select>
                    </div>
                </div>
                
                <div class="form-group">
                    <label for="especialidade">Especialidade Médica</label>
                    <div id="especialidade-container">
                        <input type="text" id="especialidade" name="especialidade" value="{agendamento.especialidade or ''}" placeholder="">
                    </div>
                </div>
                
                <div class="form-row">
                    <div class="form-group">
                        <label for="data">Data *</label>
                        <input type="date" id="data" name="data" value="{data_atual}" required>
                    </div>
                    <div class="form-group">
                        <label for="hora">Hora *</label>
                        <input type="time" id="hora" name="hora" value="{hora_atual}" required>
                    </div>
                </div>
                
                <div class="form-group">
                    <label for="origem">Endereço de Origem *</label>
                    <input type="text" id="origem" name="origem" value="{agendamento.origem}" required>
                </div>
                
                <div class="form-group">
                    <label for="destino">Endereço de Destino *</label>
                    <div id="destino-container">
                        <input type="text" id="destino" name="destino" value="{agendamento.destino}" required>
                    </div>
                </div>
                
                <div class="form-row">
                    <div class="form-group">
                        <label for="veiculo_id">Veículo</label>
                        <select id="veiculo_id" name="veiculo_id">
                            <option value="">🚗 Sistema escolherá automaticamente</option>
                            {veiculos_options}
                        </select>
                    </div>
                    <div class="form-group">
                        <label for="motorista_id">Motorista *</label>
                        <select id="motorista_id" name="motorista_id" required>
                            <option value="">Selecione o motorista...</option>
                            {motoristas_options}
                        </select>
                    </div>
                </div>
                
                <div class="form-group">
                    <label for="observacoes">Observações</label>
                    <textarea id="observacoes" name="observacoes" rows="3">{agendamento.observacoes or ''}</textarea>
                </div>
                
                <div style="margin-top: 2rem;">
                    <button type="submit" class="btn btn-success">✅ Salvar Alterações</button>
                    <a href="/agendamentos" class="btn btn-secondary" style="margin-left: 1rem;">❌ Cancelar</a>
                </div>
            </form>
        </div>
        
        <script src="/static/js/cidades.js"></script>
        <script src="/static/js/especialidades.js"></script>
        '''
        return gerar_layout_base("Editar Agendamento", conteudo, "agendamentos")

    # 🆕 EXCLUSÃO DE AGENDAMENTOS
    @app.route('/agendamentos/excluir/<int:id>')
    @delete_required
    def agendamentos_excluir(id):
        try:
            agendamento = Agendamento.query.get_or_404(id)
            
            print(f"🗑️ Excluindo agendamento: {agendamento.id} - {agendamento.data} às {agendamento.hora}")
            
            db.session.delete(agendamento)
            db.session.commit()
            
            flash('Agendamento excluído com sucesso!', 'success')
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao excluir agendamento: {str(e)}', 'error')
            print(f"❌ Erro ao excluir agendamento: {e}")
        
        return redirect(url_for('agendamentos'))
        
        
    # 🆕 EDIÇÃO DE PACIENTES
    @app.route('/pacientes/editar/<int:id>', methods=['GET', 'POST'])
    @edit_required
    def pacientes_editar(id):
        paciente = Paciente.query.get_or_404(id)
        
        if request.method == 'POST':
            try:
                # Extrair dados do formulário
                nome = request.form.get('nome', '').strip()
                cpf = request.form.get('cpf', '').strip()
                telefone = request.form.get('telefone', '').strip()
                data_nascimento = request.form.get('data_nascimento')
                
                # 🆕 ENDEREÇO ESTRUTURADO
                cep = request.form.get('cep', '').strip()
                logradouro = request.form.get('logradouro', '').strip()
                numero = request.form.get('numero', '').strip()
                complemento = request.form.get('complemento', '').strip()
                bairro = request.form.get('bairro', '').strip()
                cidade = request.form.get('cidade', '').strip()
                uf = request.form.get('uf', '').strip()
                
                cartao_sus = request.form.get('cartao_sus', '').strip()
                observacoes = request.form.get('observacoes', '').strip()
                
                # 🆕 VALIDAÇÃO COMPLETA DE ENDEREÇO
                endereco_valido, erros_endereco = validar_endereco_completo(
                    cep, logradouro, numero, bairro, cidade, uf
                )
                
                if not endereco_valido:
                    for erro in erros_endereco:
                        flash(f'Erro no endereço: {erro}', 'error')
                    return redirect(url_for('pacientes_editar', id=id))
                
                # Formatar CEP
                cep = formatar_cep(cep)
                
                # Verificar se CPF já existe (exceto o próprio)
                cpf_existente = Paciente.query.filter(Paciente.cpf == cpf, Paciente.id != id).first()
                if cpf_existente:
                    flash('CPF já cadastrado para outro paciente!', 'error')
                    return redirect(url_for('pacientes_editar', id=id))
                
                # Converter data
                data_nascimento = datetime.strptime(data_nascimento, '%Y-%m-%d').date()
                
                # Atualizar paciente
                paciente.nome = nome
                paciente.cpf = cpf
                paciente.telefone = telefone
                paciente.data_nascimento = data_nascimento
                paciente.cep = cep
                paciente.logradouro = logradouro
                paciente.numero = numero
                paciente.complemento = complemento if complemento else None
                paciente.bairro = bairro
                paciente.cidade = cidade
                paciente.uf = uf.upper()
                paciente.cartao_sus = cartao_sus if cartao_sus else None
                paciente.observacoes = observacoes if observacoes else None
                
                db.session.commit()
                
                flash(f'Paciente "{nome}" atualizado com sucesso!', 'success')
                return redirect(url_for('pacientes'))
                
            except Exception as e:
                db.session.rollback()
                flash(f'Erro ao atualizar paciente: {str(e)}', 'error')
                print(f"❌ Erro ao atualizar paciente: {e}")
        
        # Gerar alertas de mensagens flash
        messages_html = ""
        for category, message in get_flashed_messages(with_categories=True):
            alert_class = f"alert-{category}"
            messages_html += f'<div class="alert {alert_class}">{message}</div>'
        
        # Formatar data para o campo
        data_nascimento_str = paciente.data_nascimento.strftime('%Y-%m-%d')
        
        conteudo = f'''
        <div class="breadcrumb">
            <a href="/dashboard">Dashboard</a> > 
            <a href="/pacientes">Pacientes</a> > 
            Editar Paciente
        </div>
        
        <div class="page-header">
            <h2>✏️ Editar Paciente</h2>
            <p>Altere os dados do paciente {paciente.nome}</p>
        </div>
        
        {messages_html}
        
        <div class="card">
            <form method="POST">
                <div class="form-row">
                    <div class="form-group">
                        <label for="nome">Nome Completo *</label>
                        <input type="text" id="nome" name="nome" value="{paciente.nome}" required>
                    </div>
                    <div class="form-group">
                        <label for="cpf">CPF *</label>
                        <input type="text" id="cpf" name="cpf" value="{paciente.cpf}" placeholder="000.000.000-00" required>
                    </div>
                </div>
                
                <div class="form-row">
                    <div class="form-group">
                        <label for="telefone">Telefone *</label>
                        <input type="tel" id="telefone" name="telefone" value="{paciente.telefone}" placeholder="(00) 00000-0000" required>
                    </div>
                    <div class="form-group">
                        <label for="data_nascimento">Data de Nascimento *</label>
                        <input type="date" id="data_nascimento" name="data_nascimento" value="{data_nascimento_str}" required>
                    </div>
                </div>
                
                <!-- 🆕 ENDEREÇO ESTRUTURADO -->
                <div class="form-row">
                    <div class="form-group">
                        <label for="cep">CEP *</label>
                        <input type="text" id="cep" name="cep" value="{paciente.cep or ''}" placeholder="00000-000" required>
                    </div>
                    <div class="form-group">
                        <label for="logradouro">Logradouro *</label>
                        <input type="text" id="logradouro" name="logradouro" value="{paciente.logradouro or ''}" required>
                    </div>
                </div>
                
                <div class="form-row">
                    <div class="form-group">
                        <label for="numero">Número *</label>
                        <input type="text" id="numero" name="numero" value="{paciente.numero or ''}" required>
                    </div>
                    <div class="form-group">
                        <label for="complemento">Complemento</label>
                        <input type="text" id="complemento" name="complemento" value="{paciente.complemento or ''}">
                    </div>
                </div>
                
                <div class="form-row">
                    <div class="form-group">
                        <label for="bairro">Bairro *</label>
                        <input type="text" id="bairro" name="bairro" value="{paciente.bairro or ''}" required>
                    </div>
                    <div class="form-group">
                        <label for="cidade">Cidade *</label>
                        <input type="text" id="cidade" name="cidade" value="{paciente.cidade or ''}" required>
                    </div>
                    <div class="form-group">
                        <label for="uf">UF *</label>
                        <input type="text" id="uf" name="uf" value="{paciente.uf or ''}" maxlength="2" required>
                    </div>
                </div>
                
                <div class="form-row">
                    <div class="form-group">
                        <label for="cartao_sus">Cartão SUS</label>
                        <input type="text" id="cartao_sus" name="cartao_sus" value="{paciente.cartao_sus or ''}" placeholder="000 0000 0000 0000">
                    </div>
                </div>
                
                <div class="form-group">
                    <label for="observacoes">Necessidades Especiais / Observações</label>
                    <textarea id="observacoes" name="observacoes" rows="4">{paciente.observacoes or ''}</textarea>
                </div>
                
                <div style="margin-top: 2rem;">
                    <button type="submit" class="btn btn-success">✅ Salvar Alterações</button>
                    <a href="/pacientes" class="btn btn-secondary" style="margin-left: 1rem;">❌ Cancelar</a>
                </div>
            </form>
        </div>
        '''
        return gerar_layout_base("Editar Paciente", conteudo, "pacientes")

    # 🆕 EXCLUSÃO DE PACIENTES
    @app.route('/pacientes/excluir/<int:id>')
    @delete_required
    def pacientes_excluir(id):
        try:
            paciente = Paciente.query.get_or_404(id)
            
            # Verificar se o paciente tem agendamentos
            agendamentos_count = Agendamento.query.filter_by(paciente_id=id).count()
            if agendamentos_count > 0:
                flash(f'Não é possível excluir o paciente "{paciente.nome}" pois possui {agendamentos_count} agendamento(s) vinculado(s).', 'error')
                return redirect(url_for('pacientes'))
            
            print(f"🗑️ Excluindo paciente: {paciente.id} - {paciente.nome}")
            
            db.session.delete(paciente)
            db.session.commit()
            
            flash(f'Paciente "{paciente.nome}" excluído com sucesso!', 'success')
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao excluir paciente: {str(e)}', 'error')
            print(f"❌ Erro ao excluir paciente: {e}")
        
        return redirect(url_for('pacientes'))
    
    # 🆕 EDIÇÃO DE VEÍCULOS
    @app.route('/veiculos/editar/<int:id>', methods=['GET', 'POST'])
    @edit_required
    def veiculos_editar(id):
        veiculo = Veiculo.query.get_or_404(id)
        
        if request.method == 'POST':
            try:
                # Extrair dados do formulário
                placa = request.form.get('placa', '').strip().upper()
                marca = request.form.get('marca', '').strip()
                modelo = request.form.get('modelo', '').strip()
                ano = int(request.form.get('ano', 0))
                cor = request.form.get('cor', '').strip()
                tipo = request.form.get('tipo', '').strip()
                capacidade = request.form.get('capacidade')
                adaptado = request.form.get('adaptado') == 'sim'
                observacoes = request.form.get('observacoes', '').strip()
                
                # Validação básica
                if not all([placa, marca, modelo, ano, tipo]):
                    flash('Por favor, preencha todos os campos obrigatórios!', 'error')
                    return redirect(url_for('veiculos_editar', id=id))
                
                # Verificar se placa já existe (exceto o próprio)
                placa_existente = Veiculo.query.filter(Veiculo.placa == placa, Veiculo.id != id).first()
                if placa_existente:
                    flash('Placa já cadastrada para outro veículo!', 'error')
                    return redirect(url_for('veiculos_editar', id=id))
                
                # Atualizar veículo
                veiculo.placa = placa
                veiculo.marca = marca
                veiculo.modelo = modelo
                veiculo.ano = ano
                veiculo.cor = cor if cor else None
                veiculo.tipo = tipo
                veiculo.capacidade = int(capacidade) if capacidade else None
                veiculo.adaptado = adaptado
                veiculo.observacoes = observacoes if observacoes else None
                
                db.session.commit()
                
                flash(f'Veículo "{placa}" atualizado com sucesso!', 'success')
                return redirect(url_for('veiculos'))
                
            except Exception as e:
                db.session.rollback()
                flash(f'Erro ao atualizar veículo: {str(e)}', 'error')
                print(f"❌ Erro ao atualizar veículo: {e}")
        
        # Gerar alertas de mensagens flash
        messages_html = ""
        for category, message in get_flashed_messages(with_categories=True):
            alert_class = f"alert-{category}"
            messages_html += f'<div class="alert {alert_class}">{message}</div>'
        
        conteudo = f'''
        <div class="breadcrumb">
            <a href="/dashboard">Dashboard</a> > 
            <a href="/veiculos">Veículos</a> > 
            Editar Veículo
        </div>
        
        <div class="page-header">
            <h2>✏️ Editar Veículo</h2>
            <p>Altere os dados do veículo {veiculo.placa}</p>
        </div>
        
        {messages_html}
        
        <div class="card">
            <form method="POST">
                <div class="form-row">
                    <div class="form-group">
                        <label for="placa">Placa *</label>
                        <input type="text" id="placa" name="placa" value="{veiculo.placa}" placeholder="ABC-1234" required style="text-transform: uppercase;">
                    </div>
                    <div class="form-group">
                        <label for="marca">Marca *</label>
                        <input type="text" id="marca" name="marca" value="{veiculo.marca}" required>
                    </div>
                </div>
                
                <div class="form-row">
                    <div class="form-group">
                        <label for="modelo">Modelo *</label>
                        <input type="text" id="modelo" name="modelo" value="{veiculo.modelo}" required>
                    </div>
                    <div class="form-group">
                        <label for="ano">Ano *</label>
                        <input type="number" id="ano" name="ano" value="{veiculo.ano}" min="1980" max="2030" required>
                    </div>
                </div>
                
                <div class="form-row">
                    <div class="form-group">
                        <label for="cor">Cor</label>
                        <input type="text" id="cor" name="cor" value="{veiculo.cor or ''}">
                    </div>
                    <div class="form-group">
                        <label for="tipo">Tipo de Veículo *</label>
                        <select id="tipo" name="tipo" required>
                            <option value="">Selecione...</option>
                            <option value="ambulancia" {'selected' if veiculo.tipo == 'ambulancia' else ''}>Ambulância</option>
                            <option value="van" {'selected' if veiculo.tipo == 'van' else ''}>Van</option>
                            <option value="micro_onibus" {'selected' if veiculo.tipo == 'micro_onibus' else ''}>Micro-ônibus</option>
                            <option value="carro" {'selected' if veiculo.tipo == 'carro' else ''}>Carro</option>
                        </select>
                    </div>
                </div>
                
                <div class="form-row">
                    <div class="form-group">
                        <label for="capacidade">Capacidade de Passageiros</label>
                        <input type="number" id="capacidade" name="capacidade" value="{veiculo.capacidade or ''}" min="1" max="50">
                    </div>
                    <div class="form-group">
                        <label for="adaptado">Adaptado para PCD</label>
                        <select id="adaptado" name="adaptado">
                            <option value="nao" {'selected' if not veiculo.adaptado else ''}>Não</option>
                            <option value="sim" {'selected' if veiculo.adaptado else ''}>Sim</option>
                        </select>
                    </div>
                </div>
                
                <div class="form-group">
                    <label for="observacoes">Observações</label>
                    <textarea id="observacoes" name="observacoes" rows="3">{veiculo.observacoes or ''}</textarea>
                </div>
                
                <div style="margin-top: 2rem;">
                    <button type="submit" class="btn btn-success">✅ Salvar Alterações</button>
                    <a href="/veiculos" class="btn btn-secondary" style="margin-left: 1rem;">❌ Cancelar</a>
                </div>
            </form>
        </div>
        '''
        return gerar_layout_base("Editar Veículo", conteudo, "veiculos")

    # 🆕 EXCLUSÃO DE VEÍCULOS
    @app.route('/veiculos/excluir/<int:id>')
    @delete_required
    def veiculos_excluir(id):
        try:
            veiculo = Veiculo.query.get_or_404(id)
            
            # Verificar se o veículo tem agendamentos
            agendamentos_count = Agendamento.query.filter_by(veiculo_id=id).count()
            if agendamentos_count > 0:
                flash(f'Não é possível excluir o veículo "{veiculo.placa}" pois possui {agendamentos_count} agendamento(s) vinculado(s).', 'error')
                return redirect(url_for('veiculos'))
            
            print(f"🗑️ Excluindo veículo: {veiculo.id} - {veiculo.placa}")
            
            db.session.delete(veiculo)
            db.session.commit()
            
            flash(f'Veículo "{veiculo.placa}" excluído com sucesso!', 'success')
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao excluir veículo: {str(e)}', 'error')
            print(f"❌ Erro ao excluir veículo: {e}")
        
        return redirect(url_for('veiculos'))
    
    # 🆕 EDIÇÃO DE MOTORISTAS
    @app.route('/motoristas/editar/<int:id>', methods=['GET', 'POST'])
    @edit_required
    def motoristas_editar(id):
        motorista = Motorista.query.get_or_404(id)
        
        if request.method == 'POST':
            try:
                # Extrair dados do formulário
                nome = request.form.get('nome', '').strip()
                cpf = request.form.get('cpf', '').strip()
                telefone = request.form.get('telefone', '').strip()
                data_nascimento = request.form.get('data_nascimento')
                cnh = request.form.get('cnh', '').strip()
                categoria_cnh = request.form.get('categoria_cnh', '').strip()
                vencimento_cnh = request.form.get('vencimento_cnh')
                endereco = request.form.get('endereco', '').strip()
                status = request.form.get('status', 'ativo').strip()
                observacoes = request.form.get('observacoes', '').strip()
                
                # Validação básica
                if not all([nome, cpf, telefone, data_nascimento, cnh, categoria_cnh, vencimento_cnh]):
                    flash('Por favor, preencha todos os campos obrigatórios!', 'error')
                    return redirect(url_for('motoristas_editar', id=id))
                
                # Verificar se CPF ou CNH já existem (exceto o próprio)
                cpf_existente = Motorista.query.filter(Motorista.cpf == cpf, Motorista.id != id).first()
                if cpf_existente:
                    flash('CPF já cadastrado para outro motorista!', 'error')
                    return redirect(url_for('motoristas_editar', id=id))
                
                cnh_existente = Motorista.query.filter(Motorista.cnh == cnh, Motorista.id != id).first()
                if cnh_existente:
                    flash('CNH já cadastrada para outro motorista!', 'error')
                    return redirect(url_for('motoristas_editar', id=id))
                
                # Converter datas
                data_nascimento = datetime.strptime(data_nascimento, '%Y-%m-%d').date()
                vencimento_cnh = datetime.strptime(vencimento_cnh, '%Y-%m-%d').date()
                
                # Atualizar motorista
                motorista.nome = nome
                motorista.cpf = cpf
                motorista.telefone = telefone
                motorista.data_nascimento = data_nascimento
                motorista.cnh = cnh
                motorista.categoria_cnh = categoria_cnh
                motorista.vencimento_cnh = vencimento_cnh
                motorista.endereco = endereco if endereco else None
                motorista.status = status
                motorista.observacoes = observacoes if observacoes else None
                
                db.session.commit()
                
                flash(f'Motorista "{nome}" atualizado com sucesso!', 'success')
                return redirect(url_for('motoristas'))
                
            except Exception as e:
                db.session.rollback()
                flash(f'Erro ao atualizar motorista: {str(e)}', 'error')
                print(f"❌ Erro ao atualizar motorista: {e}")
        
        # Gerar alertas de mensagens flash
        messages_html = ""
        for category, message in get_flashed_messages(with_categories=True):
            alert_class = f"alert-{category}"
            messages_html += f'<div class="alert {alert_class}">{message}</div>'
        
        # Formatar datas para os campos
        data_nascimento_str = motorista.data_nascimento.strftime('%Y-%m-%d')
        vencimento_cnh_str = motorista.vencimento_cnh.strftime('%Y-%m-%d')
        
        conteudo = f'''
        <div class="breadcrumb">
            <a href="/dashboard">Dashboard</a> > 
            <a href="/motoristas">Motoristas</a> > 
            Editar Motorista
        </div>
        
        <div class="page-header">
            <h2>✏️ Editar Motorista</h2>
            <p>Altere os dados do motorista {motorista.nome}</p>
        </div>
        
        {messages_html}
        
        <div class="card">
            <form method="POST">
                <div class="form-row">
                    <div class="form-group">
                        <label for="nome">Nome Completo *</label>
                        <input type="text" id="nome" name="nome" value="{motorista.nome}" required>
                    </div>
                    <div class="form-group">
                        <label for="cpf">CPF *</label>
                        <input type="text" id="cpf" name="cpf" value="{motorista.cpf}" placeholder="000.000.000-00" required>
                    </div>
                </div>
                
                <div class="form-row">
                    <div class="form-group">
                        <label for="telefone">Telefone *</label>
                        <input type="tel" id="telefone" name="telefone" value="{motorista.telefone}" placeholder="(00) 00000-0000" required>
                    </div>
                    <div class="form-group">
                        <label for="data_nascimento">Data de Nascimento *</label>
                        <input type="date" id="data_nascimento" name="data_nascimento" value="{data_nascimento_str}" required>
                    </div>
                </div>
                
                <div class="form-row">
                    <div class="form-group">
                        <label for="cnh">Número da CNH *</label>
                        <input type="text" id="cnh" name="cnh" value="{motorista.cnh}" required>
                    </div>
                    <div class="form-group">
                        <label for="categoria_cnh">Categoria CNH *</label>
                        <select id="categoria_cnh" name="categoria_cnh" required>
                            <option value="">Selecione...</option>
                            <option value="A" {'selected' if motorista.categoria_cnh == 'A' else ''}>A - Motocicleta</option>
                            <option value="B" {'selected' if motorista.categoria_cnh == 'B' else ''}>B - Carro</option>
                            <option value="C" {'selected' if motorista.categoria_cnh == 'C' else ''}>C - Caminhão</option>
                            <option value="D" {'selected' if motorista.categoria_cnh == 'D' else ''}>D - Ônibus</option>
                            <option value="E" {'selected' if motorista.categoria_cnh == 'E' else ''}>E - Carreta</option>
                        </select>
                    </div>
                </div>
                
                <div class="form-row">
                    <div class="form-group">
                        <label for="vencimento_cnh">Vencimento da CNH *</label>
                        <input type="date" id="vencimento_cnh" name="vencimento_cnh" value="{vencimento_cnh_str}" required>
                    </div>
                    <div class="form-group">
                        <label for="status">Status *</label>
                        <select id="status" name="status" required>
                            <option value="ativo" {'selected' if motorista.status == 'ativo' else ''}>Ativo</option>
                            <option value="inativo" {'selected' if motorista.status == 'inativo' else ''}>Inativo</option>
                            <option value="ferias" {'selected' if motorista.status == 'ferias' else ''}>Férias</option>
                            <option value="licenca" {'selected' if motorista.status == 'licenca' else ''}>Licença</option>
                        </select>
                    </div>
                </div>
                
                <div class="form-group">
                    <label for="endereco">Endereço Completo</label>
                    <input type="text" id="endereco" name="endereco" value="{motorista.endereco or ''}">
                </div>
                
                <div class="form-group">
                    <label for="observacoes">Observações</label>
                    <textarea id="observacoes" name="observacoes" rows="3">{motorista.observacoes or ''}</textarea>
                </div>
                
                <div style="margin-top: 2rem;">
                    <button type="submit" class="btn btn-success">✅ Salvar Alterações</button>
                    <a href="/motoristas" class="btn btn-secondary" style="margin-left: 1rem;">❌ Cancelar</a>
                </div>
            </form>
        </div>
        '''
        return gerar_layout_base("Editar Motorista", conteudo, "motoristas")

# 🆕 EXCLUSÃO DE MOTORISTAS
    @app.route('/motoristas/excluir/<int:id>')
    @delete_required
    def motoristas_excluir(id):
        try:
            motorista = Motorista.query.get_or_404(id)
            
            # Verificar se o motorista tem agendamentos
            agendamentos_count = Agendamento.query.filter_by(motorista_id=id).count()
            if agendamentos_count > 0:
                flash(f'Não é possível excluir o motorista "{motorista.nome}" pois possui {agendamentos_count} agendamento(s) vinculado(s).', 'error')
                return redirect(url_for('motoristas'))
            
            print(f"🗑️ Excluindo motorista: {motorista.id} - {motorista.nome}")
            
            db.session.delete(motorista)
            db.session.commit()
            
            flash(f'Motorista "{motorista.nome}" excluído com sucesso!', 'success')
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao excluir motorista: {str(e)}', 'error')
            print(f"❌ Erro ao excluir motorista: {e}")
        
        return redirect(url_for('motoristas'))
    
    return app
    
    
if __name__ == '__main__':
    print("🚀 Iniciando Sistema de Transporte de Pacientes...")
    
    try:
        # Criar a aplicação
        app = create_app()
        
        # Testar contexto da aplicação
        with app.app_context():
            print("✅ Contexto da aplicação configurado")
            print("📱 Acesse: http://localhost:5010")
            print("🏥 Prefeitura Municipal de Cosmópolis")
            print("👤 Login: admin / admin123")
            print("🏙️ Sistema com cidades e especialidades!")
        
        # Executar a aplicação
        app.run(debug=True, host='0.0.0.0', port=5010)
        
    except Exception as e:
        print(f"❌ Erro ao iniciar aplicação: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)