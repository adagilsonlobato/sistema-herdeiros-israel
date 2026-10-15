import os
from datetime import timedelta
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, flash, session, abort
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', '')
if not app.config['SECRET_KEY']:
    raise RuntimeError('Configure SECRET_KEY no ambiente.')
url = os.environ.get('DATABASE_URL', '')
if url.startswith('postgres://'):
    url = 'postgresql://' + url[len('postgres://'):]
if not url:
    raise RuntimeError('Configure DATABASE_URL com PostgreSQL.')
app.config['SQLALCHEMY_DATABASE_URI'] = url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_SECURE'] = os.environ.get('COOKIE_SECURE', '1') == '1'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=8)
app.config['WTF_CSRF_TIME_LIMIT'] = 3600
app.config['MAX_CONTENT_LENGTH'] = 1024 * 1024
orm = SQLAlchemy(app)
csrf = CSRFProtect(app)
ROLES = {'diretor':'Diretor', 'diretor_associado':'Diretor associado', 'secretaria':'Secretária', 'conselheiro':'Conselheiro', 'membro':'Membro', 'desbravador':'Desbravador'}

class User(orm.Model):
    id = orm.Column(orm.Integer, primary_key=True)
    name = orm.Column(orm.String(120), nullable=False)
    email = orm.Column(orm.String(255), unique=True, nullable=False)
    password_hash = orm.Column(orm.String(255), nullable=False)
    role = orm.Column(orm.String(32), nullable=False, default='desbravador')
    unit = orm.Column(orm.String(120), nullable=True)
    active = orm.Column(orm.Boolean, nullable=False, default=True)

with app.app_context():
    orm.create_all()
    admin_email = os.environ.get('ADMIN_EMAIL', '').strip().lower()
    admin_password = os.environ.get('ADMIN_PASSWORD', '')
    if admin_email and admin_password and not User.query.filter_by(role='diretor').first():
        if len(admin_password) < 12:
            raise RuntimeError('ADMIN_PASSWORD deve ter pelo menos 12 caracteres.')
        orm.session.add(User(name='Direção', email=admin_email, password_hash=generate_password_hash(admin_password), role='diretor'))
        orm.session.commit()

def current_user():
    uid = session.get('uid')
    return orm.session.get(User, uid) if uid else None

@app.context_processor
def inject():
    return {'me': current_user(), 'roles': ROLES}

def login_required(fn):
    @wraps(fn)
    def inner(*args, **kwargs):
        user = current_user()
        if not user or not user.active:
            session.clear()
            return redirect(url_for('login'))
        return fn(*args, **kwargs)
    return inner

def director_required(fn):
    @wraps(fn)
    @login_required
    def inner(*args, **kwargs):
        if current_user().role != 'diretor':
            abort(403)
        return fn(*args, **kwargs)
    return inner

@app.route('/')
def home():
    if not current_user():
        return redirect(url_for('login'))
    return render_template('home.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        user = User.query.filter_by(email=email, active=True).first()
        if user and check_password_hash(user.password_hash, password):
            session.clear()
            session.permanent = True
            session['uid'] = user.id
            return redirect(url_for('home'))
        flash('E-mail ou senha inválidos.')
    return render_template('login.html')

@app.post('/logout')
@login_required
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/usuarios')
@director_required
def users():
    return render_template('users.html', users=User.query.order_by(User.name).all())

@app.post('/usuarios')
@director_required
def add_user():
    name = request.form.get('name', '').strip()
    email = request.form.get('email', '').strip().lower()
    password = request.form.get('password', '')
    role = request.form.get('role', '')
    unit = request.form.get('unit', '').strip() or None
    if not name or '@' not in email or len(password) < 12 or role not in ROLES:
        flash('Confira os campos. A senha deve ter pelo menos 12 caracteres.')
    elif User.query.filter_by(email=email).first():
        flash('Este e-mail já está cadastrado.')
    else:
        orm.session.add(User(name=name, email=email, password_hash=generate_password_hash(password), role=role, unit=unit))
        orm.session.commit()
        flash('Usuário criado com sucesso.')
    return redirect(url_for('users'))

@app.post('/usuarios/<int:uid>/alterar')
@director_required
def update_user(uid):
    user = orm.session.get(User, uid)
    if not user:
        abort(404)
    role = request.form.get('role', '')
    if role not in ROLES:
        abort(400)
    if user.id == current_user().id and role != 'diretor':
        flash('Você não pode retirar seu próprio acesso de diretor.')
        return redirect(url_for('users'))
    user.role = role
    user.unit = request.form.get('unit', '').strip() or None
    new_password = request.form.get('password', '')
    if new_password:
        if len(new_password) < 12:
            flash('Nova senha deve ter pelo menos 12 caracteres.')
            return redirect(url_for('users'))
        user.password_hash = generate_password_hash(new_password)
    orm.session.commit()
    flash('Usuário atualizado.')
    return redirect(url_for('users'))

@app.errorhandler(403)
def forbidden(e):
    return render_template('error.html', message='Você não tem permissão para acessar esta área.'), 403

if __name__ == '__main__':
    app.run(debug=False)
