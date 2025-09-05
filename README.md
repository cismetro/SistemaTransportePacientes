# SistemaTransportePacientes
Sistema Transporte Pacientes Secretaria de Saúde Cosmópolis

Sistema de Transporte de Pacientes

📋 Descrição
Sistema completo de gerenciamento de transporte de pacientes desenvolvido para a Prefeitura Municipal de Cosmópolis. O sistema permite o controle total da frota municipal, agendamentos de transporte, cadastro de pacientes e motoristas, além de relatórios gerenciais completos.

🎯 Principais Funcionalidades

👥 Gestão de Pacientes: Cadastro completo com necessidades especiais e histórico médico

🚗 Controle de Frota: Gerenciamento de veículos, manutenções e documentações

👨‍💼 Administração de Motoristas: Controle de habilitações, disponibilidade e vínculos

📅 Agendamentos Inteligentes: Sistema completo de agendamentos com prioridades e status

📊 Relatórios Gerenciais: Exportação em PDF, Excel e CSV com filtros avançados

🔐 Sistema de Permissões: Controle granular de acesso por tipo de usuário

📱 Interface Responsiva: Design moderno adaptável a todos os dispositivos

🏗️ Estrutura do Projeto



sistema-transporte-pacientes/
├── app.py                          # Aplicação principal Flask
├── config.py                       # Configurações do sistema
├── requirements.txt                # Dependências Python
├── .env.example                    # Exemplo de variáveis de ambiente
├── 
├── db/
│   └── database.py                 # Configuração do banco de dados
│
├── sistema/
│   ├── models/                     # Modelos de dados (SQLAlchemy)
│   │   ├── paciente.py            # Modelo Paciente
│   │   ├── motorista.py           # Modelo Motorista
│   │   ├── veiculo.py             # Modelo Veículo
│   │   ├── agendamento.py         # Modelo Agendamento
│   │   └── usuario.py             # Modelo Usuário
│   │
│   ├── routes/                     # Rotas da aplicação
│   │   ├── pacientes.py           # CRUD Pacientes
│   │   ├── motoristas.py          # CRUD Motoristas
│   │   ├── veiculos.py            # CRUD Veículos
│   │   └── agendamentos.py        # CRUD Agendamentos
│   │
│   ├── services/                   # Serviços e lógica de negócio
│   │   ├── agendamento_service.py # Serviços de agendamento
│   │   └── relatorios_service.py  # Geração de relatórios
│   │
│   ├── auth/                       # Sistema de autenticação
│   │   ├── utils.py               # Utilitários de autenticação
│   │   └── routes.py              # Rotas de auth
│   │
│   ├── status/                     # Enumerações e status
│   │   └── status_enum.py         # Definições de status
│   │
│   └── templates/                  # Templates HTML
│       ├── base.html              # Template base
│       ├── login.html             # Página de login
│       ├── dashboard.html         # Dashboard principal
│       ├── pacientes.html         # Interface de pacientes
│       ├── motoristas.html        # Interface de motoristas
│       ├── veiculos.html          # Interface de veículos
│       └── agendamentos.html      # Interface de agendamentos
│
└── static/                         # Arquivos estáticos
    ├── css/                       # Estilos customizados
    ├── js/                        # JavaScript personalizado
    └── img/                       # Imagens e ícones

🛠️ Tecnologias Utilizadas

Backend
Flask 3.0+ - Framework web Python
SQLAlchemy - ORM para banco de dados
Flask-Login - Sistema de autenticação
Flask-WTF - Formulários e CSRF
PostgreSQL/MySQL - Banco de dados
ReportLab - Geração de PDFs
OpenPyXL - Geração de Excel

Frontend
HTML5 + CSS3 - Estrutura e estilização
Bootstrap 5.3 - Framework CSS
JavaScript ES6+ - Interatividade
Bootstrap Icons - Ícones
Moment.js - Manipulação de datas

Ferramentas
Python 3.9+ - Linguagem principal
Werkzeug - Servidor de desenvolvimento
Jinja2 - Template engine

🚀 Instalação e Configuração
1. Pré-requisitos


- Python 3.9 ou superior
- PostgreSQL ou MySQL
- pip (gerenciador de pacotes Python)
2. Clone o Repositório



git clone https://github.com/prefeitura-cosmopolis/sistema-transporte-pacientes.git
cd sistema-transporte-pacientes
3. Criar Ambiente Virtual



python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
4. Instalar Dependências



pip install -r requirements.txt
5. Configurar Variáveis de Ambiente



cp .env.example .env
Edite o arquivo .env com suas configurações:

env


# Configurações da Aplicação
SECRET_KEY=sua_chave_secreta_muito_forte_aqui
DEBUG=False
ENV=production

# Banco de Dados
DATABASE_URL=postgresql://usuario:senha@localhost/transporte_pacientes

# Email (opcional)
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=sistema@cosmopolis.sp.gov.br
MAIL_PASSWORD=senha_do_email

# Configurações de Upload
UPLOAD_FOLDER=uploads
MAX_CONTENT_LENGTH=16777216

# Relatórios
REPORTS_FOLDER=relatorios
6. Configurar Banco de Dados


# Criar banco de dados
createdb transporte_pacientes

# Executar migrations (se disponível)
flask db upgrade

# Ou executar script de inicialização
python init_db.py
7. Criar Usuário Administrador



python create_admin.py
▶️ Execução
Desenvolvimento



python app.py
A aplicação estará disponível em http://localhost:5000

Produção



# Usando Gunicorn
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app

# Ou usando uWSGI
pip install uwsgi
uwsgi --http 0.0.0.0:5000 --module app:app --processes 4

👤 Usuários Padrão
Administrador
Usuário: admin
Senha: admin123
Permissões: Acesso total ao sistema
Operador
Usuário: operador
Senha: op123
Permissões: Gestão de agendamentos e consultas

🎮 Como Usar

1. Primeiro Acesso
Acesse http://localhost:5000
Faça login com usuário administrador
Configure os dados básicos do sistema

2. Cadastros Básicos
Motoristas: Cadastre os motoristas com CNH e dados pessoais
Veículos: Registre a frota com documentações
Pacientes: Cadastre os pacientes com necessidades especiais

3. Operação Diária
Agendamentos: Crie e gerencie os transportes
Dashboard: Monitore estatísticas em tempo real
Relatórios: Gere relatórios gerenciais

📊 Módulos do Sistema

🏠 Dashboard
Estatísticas em tempo real
Agendamentos do dia
Alertas importantes
Ações rápidas

👥 Pacientes
Cadastro completo com foto
Histórico médico
Necessidades especiais
Contatos de emergência

🚗 Veículos
Controle da frota municipal
Manutenções programadas
Vencimentos de documentos
Consumo de combustível

👨‍💼 Motoristas
Cadastro com habilitação
Controle de disponibilidade
Histórico de viagens
Vencimento de CNH

📅 Agendamentos
Agendamentos por prioridade
Controle de status em tempo real
Timeline de horários
Confirmações automáticas

📈 Relatórios
Relatórios gerenciais completos
Exportação em PDF, Excel e CSV
Filtros avançados
Gráficos e estatísticas

🔒 Segurança
Autenticação segura com hash de senhas
Controle de sessões com timeout automático
Validação CSRF em todos os formulários
Logs de auditoria para ações críticas
Backup automático do banco de dados
Criptografia de dados sensíveis

📱 Responsividade
Design Mobile-First adaptável a qualquer tela
PWA Ready com suporte a notificações
Offline-First para funcionalidades críticas
Touch-Friendly otimizado para tablets

🎨 Temas
Tema Claro/Escuro com alternância automática
Cores institucionais da Prefeitura
Alto contraste para acessibilidade
Fonte legível em todos os tamanhos

🤝 Como Contribuir
Fork o projeto
Crie uma branch para sua feature (git checkout -b feature/AmazingFeature)
Commit suas mudanças (git commit -m 'Add some AmazingFeature')
Push para a branch (git push origin feature/AmazingFeature)
Abra um Pull Request

📝 Licença
Este sistema foi desenvolvido especificamente para a Prefeitura Municipal de Cosmópolis e pode ser utilizado por outras entidades públicas mediante autorização.

📞 Suporte
Email: ti@cosmopolis.sp.gov.br
Telefone: (19) 3872-1234
Endereço: Prefeitura Municipal de Cosmópolis - SP

🏆 Créditos
Desenvolvido com ❤️ para a comunidade de Cosmópolis/SP

Versão: 1.0.0
Última Atualização: Dezembro 2024
Status: Em Produção ✅





🚀 Iniciando Sistema de Transporte de Pacientes...

🔍 Verificando banco em: 
D:\Projetos\SistemaTransportePacientes\db\transporte_pacientes.db

❌ Banco de dados não encontrado. Criando automaticamente...

✅ Tabelas criadas no banco de dados

✅ Usuário administrador criado: admin / admin123

📱 Acesse: http://localhost:5010

🏥 Prefeitura Municipal de Cosmópolis

👤 Login: admin / admin123


Rotas adicionadas:

/pacientes/cadastrar - Formulário de cadastro de pacientes
/veiculos/cadastrar - Formulário de cadastro de veículos
/motoristas/cadastrar - Formulário de cadastro de motoristas
/agendamentos/novo - Formulário de novo agendamento
✅ Funcionalidades:

📋 Formulários completos com validação
🧭 Breadcrumbs para navegação
⚠️ Avisos de funcionalidade em desenvolvimento
🎨 Botões coloridos (verde para salvar, cinza para cancelar)
📱 Layout responsivo com duas colunas
✅ Experiência do usuário:

Formulários realistas e funcionais
Navegação intuitiva
Feedback visual adequado
Mensagens de aviso para funcionalidades futuras
Execute o novo código e teste clicando em qualquer botão cinza! 🚀


✅ Modelos de banco de dados criados:

👥 Paciente - dados pessoais, endereço, SUS, etc.
🚗 Veiculo - placa, tipo, capacidade, adaptações PCD
👨‍💼 Motorista - CNH, categoria, status, vencimento
📅 Agendamento - transportes com origem/destino
✅ Funcionalidades reais implementadas:

💾 Cadastros funcionam e salvam no banco
📊 Dashboard atualiza automaticamente com dados reais
📋 Listagens mostram dados cadastrados
✅ Validações de campos obrigatórios e únicos
🔄 Relacionamentos entre tabelas
✅ Experiência do usuário:

📈 Contadores atualizados em tempo real
📝 Formulários completos e validados
📋 Tabelas organizadas com dados reais
🎨 Mensagens de sucesso/erro
🧭 Navegação intuitiva com breadcrumbs


✅ Sistema de Relatórios Completo:
📊 Menu "Relatórios" - Nova aba no menu principal

5 Relatórios diferentes:

👥 Pacientes - Lista completa com agendamentos
📅 Agendamentos - Com filtros de data e status
👨‍💼 Motoristas - Status CNH, viagens realizadas
🚗 Veículos - Uso da frota
👤 Usuários - Controle de acesso
🔍 Filtros dinâmicos:

Período de datas
Status de agendamentos
Auto-submit nos filtros
🖨️ Função de impressão - CSS otimizado para impressão

📱 Interface responsiva - Funciona em mobile e desktop

✅ Relacionamentos implementados:
Agendamentos ↔ Motoristas
Agendamentos ↔ Pacientes
Agendamentos ↔ Veículos
Contadores de uso

✅ Recursos especiais:
Status CNH - Alerta para CNH vencida
Abas dinâmicas - JavaScript para navegação
Cores por status - Visual para diferentes estados
Dados em tempo real - Conectado ao banco

🚀 Para testar:
Salve o código como app.py
Execute: python app.py
Acesse: http://localhost:5010
Vá em "📊 Relatórios"
Teste os filtros e impressão!
Agora você tem um sistema completo de relatórios gerenciais! 📊✨



TESTAT A PARTIR DAQUI ... DIA 05/09


Sistema de Permissões implementado:
🎧 ATENDENTE (acesso padrão): Marce4la 123456
✅ PODE:

Criar agendamentos
Visualizar pacientes, veículos, motoristas
Gerar relatórios
Operações básicas do sistema
❌ NÃO PODE: ok ok ok ok

❌ Editar dados existentes
❌ Excluir qualquer registro
❌ Gerenciar usuários
❌ Ver menu "Usuários"
👨‍💼 SUPERVISOR:
✅ PODE:

Tudo que o atendente pode
✅ Editar agendamentos
✅ Editar pacientes, veículos, motoristas
✅ Badge "SUPERVISOR" aparece
❌ NÃO PODE:

❌ Excluir registros
❌ Gerenciar usuários
👑 ADMINISTRADOR:
✅ PODE TUDO:

✅ Criar, editar, visualizar
✅ EXCLUIR qualquer registro
✅ Gerenciar usuários
✅ Menu "👥 Usuários" aparece
✅ Badge "ADMINISTRADOR" aparece

🔐 Para testar as permissões:
Crie um usuário atendente via /usuarios/novo
Faça logout do admin
Login com o atendente
Observe que:
❌ Não aparece menu "Usuários"
❌ Badge mostra "ATENDENTE"
❌ Botões de excluir ficam ocultos/desabilitados


TIPO DE USUÁRIOS
Atendente: Criar agendamentos, visualizar dados, operações básicas
Supervisor: Todas as permissões do atendente + editar agendamentos e dados
Administrador: Todas as permissões + excluir dados + gerenciar usuários

TESTE COMPLETO DO SISTEMA:
🔍 Teste estas funcionalidades:

👑 Como ADMINISTRADOR:

✅ Vê todos os botões "Editar" e "Excluir"
✅ Acessa menu "👥 Usuários"
✅ Badge "ADMINISTRADOR" aparece
✅ Pode gerenciar todos os módulos
👨‍💼 Como SUPERVISOR:

✅ Vê botões "Editar" (mas não "Excluir")
❌ NÃO vê menu "Usuários"
✅ Badge "SUPERVISOR" aparece
🎧 Como ATENDENTE:

❌ Vê apenas "Visualização"
❌ NÃO vê botões de editar/excluir
❌ NÃO vê menu "Usuários"
✅ Badge "ATENDENTE" aparece
🔐 Proteções implementadas:

✅ Itens com agendamentos aparecem "🔒 Bloqueado"
✅ Confirmação antes de excluir
✅ Validação de permissões nas rotas
✅ Mensagens de erro informativas
🎯 Me confirme como está funcionando e se há algum problema para ajustarmos!


Funcionalidades implementadas:
✅ Endereço estruturado (logradouro, número, bairro, cidade, UF)
✅ Busca automática por CEP via API ViaCEP
✅ Validação em tempo real no frontend
✅ Validação robusta no backend
✅ Máscara automática de CEP (00000-000)
✅ Mensagens de erro e sucesso
✅ Exibição do endereço completo na listagem







Preciso como requisito importante é que o usuario ou a atentende ira atrela um veiculo para transporte..
ai o contador deverar acessar os veiculos usados no mes para poder efetuar o pagamento.. 
FAZER UM COMPARATIVO DA FATURA... CHECAR SE O VEICULO REALMENTE PRESTOU SERVICO NO MES.. PRA QUE NÃO HAJA DIVERGENCIA NOS VEICULOS.. 
e novo agemdamendo ou em outro lugar qualquer preciso que isso seja contabilizado para que o contador tenha acesso as estas informações.. o que vc me sugere..

E TBM...

O cadastro de veiculo deve ser dividido em dois:
Pertence a prefeitura municipal de cosmopolis ou seja Veículo Proprio
Pertence à empresa terceirizada ou seja não é da prefeitura.. vehículo terceiro 


tbm preciso implantar o Endereço de origem Usar a api Via Cep

