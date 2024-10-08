import datetime
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import pandas as pd


app = Flask(__name__)

# Configuração do banco de dados SQLite
app.config["SECRET_KEY"] = "Biblioteca@1020"  # Substitua por uma chave secreta segura
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///livros.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = "login"


class Livro(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(200), nullable=False)
    autor = db.Column(db.String(200), nullable=False)
    categoria = db.Column(db.String(100), nullable=False)
    ano = db.Column(db.Integer, nullable=False)
    editora = db.Column(db.String(200), default="Sem Editora")
    ativo = db.Column(db.Boolean, default=False)

    def __init__(self, titulo, autor, categoria, ano, editora="Sem Editora", ativo=False):
        self.titulo = titulo
        self.autor = autor
        self.categoria = categoria
        self.ano = ano
        self.editora = editora
        self.ativo = ativo

    def __repr__(self):
        return f"<Livro {self.titulo}>"
    
#Classe criação modelo de usuario
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), nullable=False, unique=True)
    password = db.Column(db.String(150), nullable=False)
    first_name = db.Column(db.String(150), nullable=False)
    last_name = db.Column(db.String(150), nullable=False)
    role = db.Column(db.String(150), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)

    def __init__(self, username, password, first_name, last_name, role, is_admin=False):
        self.username = username
        self.password = bcrypt.generate_password_hash(password).decode("utf-8")
        self.first_name = first_name
        self.last_name = last_name
        self.role = role
        self.is_admin = is_admin



#Criar classe para reserva
class Reservation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey('livro.id'), nullable=False)
    date_reserved = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def __init__(self, user_id, book_id):
        self.user_id = user_id
        self.book_id = book_id 



# Criar a classe para o modelo de Autor
class Autor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(200), nullable=False, unique=True)
    biografia = db.Column(db.Text, nullable=True)

    def __init__(self, nome, biografia=None):
        self.nome = nome
        self.biografia = biografia

    def __repr__(self):
        return f"<Autor {self.nome}>"





@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
        



    
with app.app_context():
    db.create_all()

    # Ler o arquivo CSV para um DataFrame
    df = pd.read_csv("tabela_livros.csv")

    # Adicionar cada livro à base de dados, se ainda não estiverem presentes
    for index, row in df.iterrows():
        if not Livro.query.filter_by(titulo=row["Titulo do Livro"]).first():
            livro = Livro(
                titulo=row["Titulo do Livro"],
                autor=row["Autor"],
                categoria=row["Categoria"],
                ano=row["Ano de Publicação"],
                ativo=row["Ativo"] == "TRUE",
            )
            db.session.add(livro)
    db.session.commit() 

   
#Criar a rota para exibir todos os livros
@app.route("/inicio")
@login_required
def inicio():
    livros = Livro.query.all()
    return render_template("lista.html", lista_de_livros=livros)

#Criar a rota para a página de currículo
@app.route("/curriculo")
def curriculo():
    return render_template("curriculo.html")

#Criar a rota para a página de adicionar novos livros
@app.route("/novo")
@login_required
def novo():
    return render_template("novo.html", titulo="Novo Livro") 


#Crir uma rota para processar o formulário e salvar o novo livro
@app.route("/criar", methods=["POST"])
@login_required
def criar():
    titulo = request.form["titulo"]
    autor = request.form["autor"]
    categoria = request.form["categoria"]
    ano = request.form["ano"]
    editora = request.form["editora"]

    livro = Livro(
        titulo=titulo, autor=autor, categoria=categoria, ano=ano, editora=editora
    )

    db.session.add(livro)
    db.session.commit()

    return redirect(url_for("inicio")) 

#Criar a rota para deletar livros
@app.route("/deletar/<int:id>")
@login_required
def deletar(id):
    # Buscar o livro pelo ID
    livro = Livro.query.get(id)
    if livro:
        # Remover o livro do banco de dados
        db.session.delete(livro)
        db.session.commit()
    # Redirecionar de volta para a página inicial
    return redirect(url_for("inicio"))

#Criar a rota para editar os livros
@app.route("/editar/<int:id>")
@login_required
def editar(id):
    # Buscar o livro pelo ID
    livro = Livro.query.get(id)
    if livro:
        return render_template("editar.html", livro=livro)
    return redirect(url_for("inicio"))

#Criar a rota para processar a atualização
@app.route("/atualizar/<int:id>", methods=["POST"])
@login_required
def atualizar(id):
    # Buscar o livro pelo ID
    livro = Livro.query.get(id)
    if livro:
        # Atualizar os dados do livro
        livro.titulo = request.form["titulo"]
        livro.autor = request.form["autor"]
        livro.categoria = request.form["categoria"]
        livro.ano = request.form["ano"]
        livro.editora = request.form["editora"]
        db.session.commit()
    return redirect(url_for("inicio"))

#Criar a rota para o formulario de login
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        user = User.query.filter_by(username=username).first()
        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for("inicio"))
        else:
            flash("Login ou senha incorretos. Tente novamente.")
    return render_template("login.html")

#Criar rota para logout do usuario
@app.route("/logout")
@login_required

def logout():
    logout_user()
    return redirect(url_for("login"))

#Adicionar decorador para verificar administradores
from functools import wraps
from flask import abort

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            return abort(403)
        return f(*args, **kwargs)
    return decorated_function
#Criar rota para cadastro de usuario
@app.route("/cadastro", methods=["GET", "POST"])
@login_required
@admin_required
def cadastro():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        # Verifique se o usuário já existe
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash("Nome de usuário já existe. Tente um diferente.")
            return redirect(url_for("cadastro"))

        # Criação de um novo usuário
        new_user = User(username=username, password=password)
        db.session.add(new_user)
        db.session.commit()
        flash("Cadastro realizado com sucesso! Você já pode fazer login.")
        return redirect(url_for("login"))
    return render_template("cadastro.html")

#Criar rota para exibir os livros
@app.route("/reservar", methods=["GET"])
@login_required
def reservar():
    livros = Livro.query.all()  # Pega todos os livros
    return render_template("reservar.html", livros=livros)

#Criar uma rota para processar a reserva
@app.route("/fazer_reserva/<int:book_id>")
@login_required
def fazer_reserva(book_id):
    # Verifica se o livro já foi reservado pelo usuário
    reserva_existente = Reservation.query.filter_by(user_id=current_user.id, book_id=book_id).first()
    if reserva_existente:
        flash("Você já reservou este livro.")
        return redirect(url_for("reservar"))

    # Criação de uma nova reserva
    nova_reserva = Reservation(user_id=current_user.id, book_id=book_id)
    db.session.add(nova_reserva)
    db.session.commit()
    flash("Reserva realizada com sucesso!")
    return redirect(url_for("reservar"))

#Criar uma rota para visualizar as reservas
@app.route("/minhas_reservas")
@login_required
def minhas_reservas():
    reservas = Reservation.query.filter_by(user_id=current_user.id).all()
    return render_template("minhas_reservas.html", reservas=reservas)


#Criação de rota para o dashboard

@app.route("/dashboard")
@login_required
@admin_required
def dashboard():
    # Totalizadores
    total_livros = Livro.query.count()
    total_usuarios = User.query.count()
    total_reservas = Reservation.query.count()

    # Dados para os gráficos
    livros_por_autor = db.session.query(Livro.autor, db.func.count(Livro.id)).group_by(Livro.autor).all()
    livros_por_ano = db.session.query(Livro.ano, db.func.count(Livro.id)).group_by(Livro.ano).all()
    livros_por_editora = db.session.query(Livro.editora, db.func.count(Livro.id)).group_by(Livro.editora).all()

    return render_template("dashboard.html",
                           total_livros=total_livros,
                           total_usuarios=total_usuarios,
                           total_reservas=total_reservas,
                           livros_por_autor=livros_por_autor,
                           livros_por_ano=livros_por_ano,
                           livros_por_editora=livros_por_editora)

#Crie uma nova rota para exibir o formulário de cadastro de autores:
@app.route("/cadastro_autor", methods=["GET"])
@login_required
@admin_required
def cadastro_autor():
    return render_template("cadastro_autor.html")



#Crie uma nova rota para processar o formulário e adicionar novos autores ao banco de dados
@app.route("/criar_autor", methods=["POST"])
@login_required
@admin_required
def criar_autor():
    nome = request.form.get("nome")
    biografia = request.form.get("biografia")

    print(f"Nome do Autor: {nome}")
    print(f"Biografia do Autor: {biografia}")

    # Verificar se o autor já existe
    autor_existente = Autor.query.filter_by(nome=nome).first()
    if autor_existente:
        flash("Autor já cadastrado.")
        return redirect(url_for("cadastro_autor"))

    # Criar novo autor e adicionar ao banco de dados
    novo_autor = Autor(nome=nome, biografia=biografia)
    db.session.add(novo_autor)

    try:
        db.session.commit()
        print(f"Autor {nome} adicionado com sucesso.")
    except Exception as e:
        db.session.rollback()
        print(f"Erro ao adicionar autor: {e}")
        flash("Erro ao cadastrar o autor. Tente novamente.")
        return redirect(url_for("cadastro_autor"))

    # Redirecionar para a página de confirmação
    return redirect(url_for("confirmacao_autor"))




#Rota para informar a confirmação do cadastro do autor
@app.route("/confirmacao_autor")
@login_required
def confirmacao_autor():
    return render_template("confirmacao_autor.html")











if __name__ == "__main__":
    app.run(debug=True)