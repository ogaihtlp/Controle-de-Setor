from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_required, current_user
from dotenv import load_dotenv
from flask import Flask
import os

print("Iniciando a aplicação...")  

app = Flask(__name__)
print(f"Templates folder: {app.template_folder}")  

app.config['SECRET_KEY'] = 'dev'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///atendimentos.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'auth.login' # type: ignore

from .models.usuario import Usuario 
from app.routes.auth import bp as auth_bp
from app.routes.atendimentos import bp as atendimentos_bp
from app.routes.atividades import bp as atividades_bp

app.register_blueprint(auth_bp)
app.register_blueprint(atendimentos_bp, url_prefix='/atendimentos')
app.register_blueprint(atividades_bp, url_prefix='/atividades')

 
print("Rotas registradas:", [str(rule) for rule in app.url_map.iter_rules()]) 

@app.route('/')
@login_required
def index():
    print("Acessando rota index")  
    try:
        return render_template('index.html')
    except Exception as e:
        print(f"Erro ao renderizar index: {str(e)}")  
        return f"Erro: {str(e)}", 500

@app.route('/login-test')
def login_test():
    print("Acessando rota login-test")  
    try:
        return render_template('auth/login.html')
    except Exception as e:
        print(f"Erro ao renderizar login: {str(e)}")  
        return f"Erro: {str(e)}", 500

with app.app_context():
    db.create_all()
    
    if not Usuario.query.first():
        admin = Usuario()
        admin.username = 'admin'
        admin.nome = 'Administrador'
        admin.tipo = 'gestor'
        admin.set_password('admin')
        db.session.add(admin)
        db.session.commit()
        print("Usuário admin criado")  


