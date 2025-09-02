#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sistema de Transporte de Pacientes
Desenvolvido para a Prefeitura Municipal de Cosmópolis
Pode ser usado por terceiros autorizados

Arquivo principal da aplicação Flask
"""

from flask import Flask, render_template, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from werkzeug.security import generate_password_hash
import os
from datetime import timedelta

# Importações locais
from config import Config
from db.database import db, init_db

def create_app():
    """
    Factory function para criar a aplicação Flask
    Sistema da Prefeitura Municipal de Cosmópolis
    """
    app = Flask(__name__, 
                template_folder='sistema/templates',
                static_folder='sistema/static')
    
    # Configuração da aplicação
    app.config.from_object(Config)
    
    # Inicialização do banco de dados
    db.init_app(app)
    
    # Configuração de migração (preparado para PostgreSQL/MySQL)
    migrate = Migrate(app, db)
    
    # Configuração de sessão para autenticação
    app.permanent_session_lifetime = timedelta(hours=8)
    
    # Registrar blueprints (rotas organizadas)
    register_blueprints(app)
    
    # Inicializar banco de dados na primeira execução
    with app.app_context():
        init_db()
        create_default_admin()
    
    # Rota principal
    @app.route('/')
    def index():
        """Página inicial - redireciona para dashboard se logado, senão para login"""
        if 'user_id' in session:
            return redirect(url_for('dashboard'))
        return redirect(url_for('auth.login'))
    
    @app.route('/dashboard')
    def dashboard():
        """Dashboard principal do sistema"""
        if 'user_id' not in session:
            flash('Você precisa estar logado para acessar o sistema.', 'warning')
            return redirect(url_for('auth.login'))
        
        # Estatísticas básicas para o dashboard
        from sistema.models.paciente import Paciente
        from sistema.models.motorista import Motorista
        from sistema.models.veiculo import Veiculo
        from sistema.models.agendamento import Agendamento
        
        stats = {
            'total_pacientes': Paciente.query.count(),
            'total_motoristas': Motorista.query.count(),
            'total_veiculos': Veiculo.query.count(),
            'total_agendamentos': Agendamento.query.count()
        }
        
        return render_template('dashboard.html', stats=stats)
    
    # Handler de erro 404
    @app.errorhandler(404)
    def not_found(error):
        return render_template('base.html', 
                             error_message='Página não encontrada'), 404
    
    # Handler de erro 500
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template('base.html', 
                             error_message='Erro interno do servidor'), 500
    
    return app

def register_blueprints(app):
    """
    Registra todos os blueprints da aplicação
    Organização modular das rotas
    """
    # Importar blueprints
    from sistema.auth.routes import auth_bp
    from sistema.routes.pacientes import pacientes_bp
    from sistema.routes.motoristas import motoristas_bp
    from sistema.routes.veiculos import veiculos_bp
    from sistema.routes.agendamentos import agendamentos_bp
    
    # Registrar blueprints com prefixos
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(pacientes_bp, url_prefix='/pacientes')
    app.register_blueprint(motoristas_bp, url_prefix='/motoristas')
    app.register_blueprint(veiculos_bp, url_prefix='/veiculos')
    app.register_blueprint(agendamentos_bp, url_prefix='/agendamentos')

def create_default_admin():
    """
    Cria usuário administrador padrão na primeira execução
    Login: admin | Senha: admin123
    ALTERE A SENHA APÓS PRIMEIRO ACESSO!
    """
    from sistema.models.usuario import Usuario
    
    # Verificar se já existe usuário admin
    admin_exists = Usuario.query.filter_by(login='admin').first()
    
    if not admin_exists:
        admin_user = Usuario(
            nome='Administrador do Sistema',
            login='admin',
            senha=generate_password_hash('admin123'),
            tipo_usuario='admin',
            ativo=True,
            observacoes='Usuário padrão criado automaticamente - ALTERE A SENHA!'
        )
        
        try:
            db.session.add(admin_user)
            db.session.commit()
            print("✅ Usuário administrador padrão criado:")
            print("   Login: admin")
            print("   Senha: admin123")
            print("   ⚠️  ALTERE A SENHA APÓS PRIMEIRO ACESSO!")
        except Exception as e:
            print(f"❌ Erro ao criar usuário administrador: {e}")
            db.session.rollback()

if __name__ == '__main__':
    """
    Execução principal da aplicação
    Para produção, usar Waitress: waitress-serve --host=0.0.0.0 --port=8080 app:app
    """
    # Criar a aplicação
    app = create_app()
    
    # Verificar se está em modo de desenvolvimento
    debug_mode = os.getenv('FLASK_ENV') == 'development'
    
    if debug_mode:
        print("🚀 Iniciando Sistema de Transporte de Pacientes")
        print("📍 Prefeitura Municipal de Cosmópolis")
        print("🌐 Modo: Desenvolvimento")
        print("🔗 Acesso: http://localhost:5000")
        print("👤 Admin padrão - Login: admin | Senha: admin123")
        print("=" * 50)
        
        # Executar em modo desenvolvimento
        app.run(
            host='0.0.0.0',
            port=5000,
            debug=True,
            threaded=True
        )
    else:
        print("🚀 Iniciando Sistema de Transporte de Pacientes")
        print("📍 Prefeitura Municipal de Cosmópolis") 
        print("🌐 Modo: Produção")
        print("⚡ Usando Waitress WSGI Server")
        print("=" * 50)
        
        # Executar em modo produção com Waitress
        from waitress import serve
        serve(app, host='0.0.0.0', port=8080, threads=6)