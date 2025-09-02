import os
from flask import Flask, render_template, redirect, url_for, flash, request, get_flashed_messages
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash
from config import config

# Inicializar extensões
db = SQLAlchemy()
login_manager = LoginManager()

# Modelo simples de usuário para teste
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
        return check_password_hash(self.password_hash, password)
    
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

@login_manager.user_loader
def load_user(user_id):
    return Usuario.query.get(int(user_id))

def create_app(config_name=None):
    app = Flask(__name__)
    
    # Configuração
    config_name = config_name or os.environ.get('FLASK_CONFIG') or 'default'
    app.config.from_object(config[config_name])
    
    # Criar diretórios necessários
    os.makedirs('db', exist_ok=True)
    os.makedirs('uploads', exist_ok=True)
    os.makedirs('relatorios', exist_ok=True)
    os.makedirs('static/css', exist_ok=True)
    os.makedirs('static/js', exist_ok=True)
    os.makedirs('static/img', exist_ok=True)
    
    # Inicializar extensões
    db.init_app(app)
    login_manager.init_app(app)
    
    # Configurar Login Manager
    login_manager.login_view = 'login'
    login_manager.login_message = 'Por favor, faça login para acessar esta página.'
    login_manager.login_message_category = 'info'
    
    # Rotas
    @app.route('/')
    def index():
        if current_user.is_authenticated:
            return redirect(url_for('dashboard'))
        return redirect(url_for('login'))
    
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == 'POST':
            username = request.form.get('username')
            password = request.form.get('password')
            
            user = Usuario.query.filter_by(username=username).first()
            
            if user and user.check_password(password):
                login_user(user)
                flash('Login realizado com sucesso!', 'success')
                return redirect(url_for('dashboard'))
            else:
                flash('Usuário ou senha incorretos!', 'error')
        
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
                body {{ font-family: Arial, sans-serif; margin: 0; padding: 0; background: linear-gradient(135deg, #5D5CDE, #4a49c4); min-height: 100vh; display: flex; align-items: center; justify-content: center; }}
                .login-container {{ background: white; padding: 2rem; border-radius: 1rem; box-shadow: 0 0.5rem 2rem rgba(0,0,0,0.2); max-width: 400px; width: 100%; }}
                .header {{ text-align: center; margin-bottom: 2rem; }}
                .header h1 {{ color: #5D5CDE; margin: 0; }}
                .header p {{ color: #666; margin: 0.5rem 0 0 0; }}
                .form-group {{ margin-bottom: 1rem; }}
                .form-group label {{ display: block; margin-bottom: 0.5rem; color: #333; font-weight: 600; }}
                .form-group input {{ width: 100%; padding: 0.75rem; border: 2px solid #e9ecef; border-radius: 0.5rem; font-size: 1rem; box-sizing: border-box; }}
                .form-group input:focus {{ border-color: #5D5CDE; outline: none; }}
                .btn {{ width: 100%; padding: 0.75rem; background: #5D5CDE; color: white; border: none; border-radius: 0.5rem; font-size: 1rem; cursor: pointer; }}
                .btn:hover {{ background: #4a49c4; }}
                .alert {{ padding: 0.75rem; margin-bottom: 1rem; border-radius: 0.5rem; }}
                .alert-error {{ background: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }}
                .alert-success {{ background: #d4edda; color: #155724; border: 1px solid #c3e6cb; }}
                .default-info {{ background: #e3f2fd; padding: 1rem; border-radius: 0.5rem; margin-top: 1rem; font-size: 0.875rem; }}
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
    
    @app.route('/dashboard')
    @login_required
    def dashboard():
        return f'''
        <html>
        <head>
            <title>Dashboard - Sistema de Transporte</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 0; padding: 0; background: #f5f5f5; }}
                .header {{ background: linear-gradient(135deg, #5D5CDE, #4a49c4); color: white; padding: 1rem 2rem; }}
                .header h1 {{ margin: 0; }}
                .header .user-info {{ float: right; }}
                .container {{ padding: 2rem; max-width: 1200px; margin: 0 auto; }}
                .stats {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 1rem; margin-bottom: 2rem; }}
                .stat-card {{ background: white; padding: 1.5rem; border-radius: 1rem; box-shadow: 0 0.125rem 0.25rem rgba(0,0,0,0.075); }}
                .stat-card h3 {{ margin: 0 0 0.5rem 0; color: #5D5CDE; }}
                .stat-card .number {{ font-size: 2rem; font-weight: bold; color: #333; }}
                .menu {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; }}
                .menu-item {{ background: white; padding: 2rem; border-radius: 1rem; box-shadow: 0 0.125rem 0.25rem rgba(0,0,0,0.075); text-align: center; text-decoration: none; color: #333; transition: transform 0.3s ease; }}
                .menu-item:hover {{ transform: translateY(-5px); }}
                .menu-item i {{ font-size: 3rem; margin-bottom: 1rem; color: #5D5CDE; }}
                .logout {{ background: #dc3545; color: white; padding: 0.5rem 1rem; border: none; border-radius: 0.5rem; cursor: pointer; text-decoration: none; }}
                .logout:hover {{ background: #c82333; }}
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
            
            <div class="container">
                <div class="stats">
                    <div class="stat-card">
                        <h3>📊 Total de Pacientes</h3>
                        <div class="number">0</div>
                    </div>
                    <div class="stat-card">
                        <h3>🚗 Veículos Ativos</h3>
                        <div class="number">0</div>
                    </div>
                    <div class="stat-card">
                        <h3>👨‍💼 Motoristas</h3>
                        <div class="number">0</div>
                    </div>
                    <div class="stat-card">
                        <h3>📅 Agendamentos Hoje</h3>
                        <div class="number">0</div>
                    </div>
                </div>
                
                <div class="menu">
                    <div class="menu-item">
                        <div style="font-size: 3rem;">👥</div>
                        <h3>Pacientes</h3>
                        <p>Gerenciar pacientes cadastrados</p>
                    </div>
                    <div class="menu-item">
                        <div style="font-size: 3rem;">🚗</div>
                        <h3>Veículos</h3>
                        <p>Controlar frota municipal</p>
                    </div>
                    <div class="menu-item">
                        <div style="font-size: 3rem;">👨‍💼</div>
                        <h3>Motoristas</h3>
                        <p>Administrar motoristas</p>
                    </div>
                    <div class="menu-item">
                        <div style="font-size: 3rem;">📅</div>
                        <h3>Agendamentos</h3>
                        <p>Programar transportes</p>
                    </div>
                </div>
                
                <div style="margin-top: 2rem; padding: 1rem; background: #e8f5e8; border-radius: 0.5rem; border-left: 4px solid #28a745;">
                    <h4>✅ Sistema Funcionando!</h4>
                    <p>Banco de dados conectado com sucesso. Usuário logado: <strong>{current_user.username}</strong></p>
                    <p>Próximos passos: Implementar módulos de pacientes, veículos, motoristas e agendamentos.</p>
                </div>
            </div>
        </body>
        </html>
        '''
    
    @app.route('/logout')
    @login_required
    def logout():
        logout_user()
        flash('Logout realizado com sucesso!', 'success')
        return redirect(url_for('login'))
    
    return app

if __name__ == '__main__':
    app = create_app()
    
    with app.app_context():
        # Verificar se o banco existe
        if os.path.exists('db/transporte_pacientes.db'):
            print("✅ Banco de dados encontrado!")
        else:
            print("❌ Banco de dados não encontrado. Execute: python init_db.py")
            exit(1)
    
    print("🚀 Iniciando Sistema de Transporte de Pacientes...")
    print("📱 Acesse: http://localhost:5010")
    print("🏥 Prefeitura Municipal de Cosmópolis")
    print("👤 Login: admin / admin123")
    app.run(debug=True, host='0.0.0.0', port=5010)