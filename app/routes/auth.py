from flask import Blueprint, render_template, redirect, url_for, request
from flask_login import login_user, logout_user
from app.models.usuario import Usuario

bp = Blueprint('auth', __name__)

@bp.route('/login', methods=['GET', 'POST'])
def login():
    print("Método:", request.method)
    if request.method == 'POST':
        print("Dados do formulário:", request.form)  # Debug
        username = request.form.get('username')
        password = request.form.get('password')
        user = Usuario.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('index'))
    return render_template('auth/login.html')

@bp.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('auth.login'))

