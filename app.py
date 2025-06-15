from flask import Flask, render_template, request, url_for, redirect, flash, session
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from database.connection import db
from database.models import Usuario, Libro

from urllib.parse import urlparse, urljoin

def is_safe_url(target):
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ('http', 'https') and ref_url.netloc == test_url.netloc

app = Flask(__name__)
app.secret_key = 'supersecretkey'  # Cambia esto por una clave secreta más segura en producción

# Configuración de Flask-Login
login_manager = LoginManager(app)
login_manager.login_view = "login"
login_manager.login_message = "Por favor inicia sesión para acceder a esta página"
login_manager.login_message_category = "warning"

# Manejo de conexiones a la base de datos
@app.before_request
def before_request():
    db.connect(reuse_if_open=True)

@app.teardown_request
def teardown_request(exception):
    if not db.is_closed():
        db.close()

# Cargador de usuario para Flask-Login
@login_manager.user_loader
def load_user(user_id):
    try:
        with db.connection_context():
            return Usuario.get_or_none(Usuario.id == int(user_id))
    except Exception as e:
        print(f"Error cargando usuario: {str(e)}")
        return None

# Rutas principales
@app.route("/")
@login_required
def index():
    return render_template("index.html")

@app.route("/login", methods=["GET", "POST"]) 
def login():
    if current_user.is_authenticated:
        flash("Ya tienes una sesión activa", "info")
        return redirect(url_for('listar_libros')) #puedo cambiarlo en cualquier momento

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()
        
        # Validación más robusta
        if len(username) < 4 or len(password) < 6:
            flash("Credenciales inválidas", "danger")
            return redirect(url_for('login'))

        try:
            with db.connection_context():
                user = Usuario.get_or_none(Usuario.usuario == username)
                
                if not user:
                    flash("Usuario no encontrado", "danger")
                    app.logger.warning(f"Intento de login con usuario inexistente: {username}")
                    return redirect(url_for('login'))

                # Aquí añadimos un print para revisar los datos del hash
                print(f"Hash almacenado: {user.password_hash}")
                print(f"Contraseña recibida: {password}")
                
                if not user.check_password(password):
                    flash("Contraseña incorrecta", "danger") # es un modulo para enviar mensajes 
                    app.logger.warning(f"Intento de login con contraseña incorrecta para usuario: {username}")
                    return redirect(url_for('login'))
                
                # Login exitoso
                login_user(user)
                flash(f"Bienvenido, {user.usuario}!", "success")
                app.logger.info(f"Usuario {user.usuario} ha iniciado sesión")
                
                # Redirección segura
                next_page = request.args.get('next')
                if not next_page or not is_safe_url(next_page):
                    next_page = url_for('index')
                return redirect(next_page)

        except Exception as e:
            flash("Error en el sistema. Intente nuevamente", "danger")
            app.logger.error(f"Error en login: {str(e)}", exc_info=True)
            return redirect(url_for('login'))

    return render_template("auth/login.html")

@app.route("/logout")
@login_required
def logout(): #este es mi endpoint
    logout_user() #metodod que cierra la sesion de un usuario en la app 
    flash("Has cerrado sesión correctamente", "success")
    return redirect(url_for('login'))# index

@app.route("/libros")
@login_required
def listar_libros():
    try:
        with db.connection_context():
            libros = Libro.select().order_by(Libro.titulo)
            return render_template("libros.html", libros=libros)
    except Exception as ex:
        flash("Error al cargar los libros", "danger")
        app.logger.error(f"Error listando libros: {str(ex)}")
        return redirect(url_for('index'))
    
    
@app.route("/agregar_autor", methods=["GET", "POST"])
@login_required
def agregar_autor():
    if request.method == "POST":
        apellido = request.form.get("apellido", "").strip()
        nombres = request.form.get("nombres", "").strip()
        fechanacimiento = request.form.get("fechanacimiento", "").strip()
        
        # Validación básica
        if not all([apellido, nombres, fechanacimiento]):
            flash("Todos los campos son requeridos", "danger")
            return redirect(url_for('agregar_autor'))
            
        try:
            with db.connection_context():
                from database.models import Autor
                Autor.create(
                    apellido=apellido,
                    nombres=nombres,
                    fechanacimiento=fechanacimiento
                )
            flash("Autor agregado correctamente", "success")
            return redirect(url_for('agregar'))  # Redirecciona al formulario de agregar libro
        except Exception as e:
            flash(f"Error al agregar autor: {str(e)}", "danger")
            app.logger.error(f"Error agregando autor: {str(e)}")
            return redirect(url_for('agregar_autor'))
    
    return render_template('agregar_autor.html')

#Agregaremos un nuevo libro
@app.route("/agregar", methods=["GET", "POST"])
@login_required
def agregar():
    if request.method == "POST":
        titulo = request.form.get("titulo", "").strip()
        autor_id = request.form.get("autor_id", "").strip()  # Cambiado de "autor" a "autor_id"
        anoedicion = request.form.get("anoedicion", "").strip()
        precioedicion = request.form.get("precioedicion", "").strip()
        isbn = request.form.get("isbn", "").strip()  # Añadido campo ISBN que es la clave primaria
        
        # Validación básica
        if not all([titulo, autor_id, anoedicion, precioedicion, isbn]):
            flash("Todos los campos son requeridos", "danger")
            return redirect(url_for('agregar'))
            
        try:
            with db.connection_context():
                # Verificar si el autor existe
                from database.models import Autor  # Importar modelo Autor
                autor = Autor.get_or_none(Autor.id == autor_id)
                
                if not autor:
                    flash(f"El autor con ID {autor_id} no existe", "danger")
                    return redirect(url_for('agregar'))
                
                # Crear el libro con el autor existente
                Libro.create(
                    isbn=isbn,
                    titulo=titulo,
                    autor=autor,  # Pasamos el objeto autor, no solo el ID
                    anoedicion=anoedicion,
                    precioedicion=precioedicion
                )
                
            flash("Libro agregado correctamente", "success")
            return redirect(url_for('listar_libros'))
        except Exception as e:
            flash(f"Error al agregar libro: {str(e)}", "danger")
            app.logger.error(f"Error agregando libro: {str(e)}")
            return redirect(url_for('agregar'))
    
    # En GET, obtenemos la lista de autores para el formulario
    try:
        with db.connection_context():
            from database.models import Autor
            autores = Autor.select()
            return render_template('agregar.html', autores=autores)
    except Exception as e:
        flash(f"Error al cargar autores: {str(e)}", "danger")
        return redirect(url_for('index'))

# Manejo de errores
@app.errorhandler(404)
def pagina_no_encontrada(error):
    return render_template("errores/404.html"), 404

@app.errorhandler(500)
def error_interno(error):
    db.rollback()
    return render_template("errores/500.html"), 500

if __name__ == "__main__":
    app.run(debug=True)


