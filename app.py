from datetime import datetime, date
from flask import Flask, render_template, request, redirect, session, flash, url_for
import re
from flask_migrate import Migrate
from flask_bcrypt import Bcrypt
from utils.decorators import login_required
from models import db  
from models.usuario import Usuario
from models.visitas import Visita
from models.likes import MeGusta


import os
from dotenv import load_dotenv
import pymysql

EMAIL_REGEX = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'

pymysql.install_as_MySQLdb()
app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL", "mysql+pymysql://root:2022@localhost/parqueaventura")
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "clave_por_defecto")
db.init_app(app)  # Solo una vez
bcrypt = Bcrypt(app)
migrate = Migrate(app, db)

with app.app_context():
    db.create_all()


# Ruta Principal
@app.route('/')
def home():
    return render_template('home.html')

#Rutas manejo de usuarios y sesiones
@app.route('/register', methods=['GET','POST'])
def register():
    errores = {}
    datos = {}
    if request.method == 'POST':
        nombre = request.form['nombre'].strip()
        apellido = request.form['apellido'].strip()
        email = request.form['email'].strip()
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        #validar nombre
        if len(nombre) == 0:
            errores['nombre'] = 'El nombre es requerido'
        elif len(nombre) < 2:
            errores['nombre'] = 'El nombre debe tener al menos 2 caracteres'
        elif not nombre.isalpha():
            errores['nombre'] = 'El nombre solo puede contener letras'

        #validar apellido
        if len(apellido) == 0:
            errores['apellido'] = 'El apellido es requerido'
        elif len(apellido) < 2:
            errores['apellido'] = 'El apellido debe tener al menos 2 caracteres'
        elif not apellido.isalpha():
            errores['apellido'] = 'El apellido solo puede contener letras'

        #almacenar datos ingresados por formulario
        datos = request.form

        #validar email
        if len(email) == 0:
            errores['email'] = 'El email es requerido'
        elif not re.match(EMAIL_REGEX, email):
            errores['email'] = 'El email no es válido'
        elif Usuario.query.filter_by(email=email).first():
            errores['email'] = 'El email ya está registrado'

        #validar password
        if len(password) == 0:
            errores['password'] = 'La contraseña es requerida'
        elif len(password) < 4:
            errores['password'] = 'La contraseña debe tener al menos 4 caracteres'
        elif password != confirm_password:
            errores['password'] = 'Las contraseñas no coinciden'
        
        if errores:
            return render_template('register.html', errores=errores, datos=datos)
        
        #encriptar password con bcrypt
        password_encriptada = bcrypt.generate_password_hash(password).decode('utf-8')

        usuario = Usuario(
            nombre = nombre,
            apellido = apellido,
            email = email,
            password = password_encriptada
        )
        db.session.add(usuario)
        db.session.commit()

        flash('Usuario registrado correctamente', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', errores={}, datos = {})


@app.route('/login', methods=['GET','POST'])
def login():
    errores = {}
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        
        usuario = Usuario.query.filter_by(email=email).first()
        print(usuario)
        if usuario == None:
            errores['email'] = 'El email no está registrado'
            print('Usuario no encontrado')
            flash('Credenciales incorrectas', 'danger')
            return render_template('login.html',errores=errores)
        else:
            if bcrypt.check_password_hash(usuario.password, password):
                session['usuario_id'] = usuario.id
                session['usuario_nombre'] = f"{usuario.nombre} {usuario.apellido}"
                flash('Bienvenido de nuevo', 'success')
                
                return redirect(url_for('dashboard'))
            else:
                errores['password'] = 'La contraseña es incorrecta'
                flash('Credenciales incorrectas', 'danger')
                return render_template('login.html', errores=errores)

    return render_template('login.html', errores={})

@app.route('/logout')
def logout():
    session.clear()
    flash('Sesión cerrada correctamente', 'success')
    return redirect(url_for('home'))

#Rutas de visitas
@app.route('/dashboard')
@login_required
def dashboard():
    username = session['usuario_nombre']
    mis_visitas = Visita.query.filter_by(visitante=session['usuario_id']).order_by(Visita.rating.desc()).all()
    otras_visitas = Visita.query.filter(Visita.visitante != session['usuario_id']).order_by(Visita.rating.desc()).all()
    return render_template('visitas/dashboard.html', mis_visitas=mis_visitas, otras_visitas=otras_visitas, username=username)

@app.route('/visitas/nueva', methods=['GET','POST'])
@login_required
def crear_visita():
    errores = {}
    datos = {}
    fecha_maxima = date.today().strftime('%Y-%m-%d')

    if request.method == 'POST':
        parque = request.form['parque'].strip()
        rating = request.form['rating']
        fecha_visita = request.form['fecha_visita']
        detalles = request.form['detalles']

        usuario_id = session.get('usuario_id')
        datos = request.form

         # Validar si el usuario ya ha registrado el mismo parque
        visita_existente = Visita.query.filter_by(parque=parque, visitante=usuario_id).first()
        if visita_existente:
            errores['parque'] = "Ya has registrado una visita a este parque antes"

        
        #validar parque
        if len(parque) == 0:
            errores['parque'] = 'El nombre del parque es requerido'

        #validar rating
        if len(rating) == 0:
            errores['rating'] = 'El rating es requerido'
        if not rating.isdigit():
            errores['rating'] = 'El rating debe ser un número'
        if int(rating) < 1 or int(rating) > 5:
            errores['rating'] = 'El rating debe estar entre 1 y 5'

        #validar fecha de visita
        if len(fecha_visita) == 0:
            errores['fecha_visita'] = 'La fecha de visita es requerida'
        elif fecha_visita > fecha_maxima:
            errores['fecha_visita'] = 'La fecha de visita no puede ser mayor a la fecha actual'
        
        #validar detalles
        if len(detalles) == 0:
            errores['detalles'] = 'Los detalles son requeridos'

        if errores:
            return render_template('visitas/nueva_visita.html', errores=errores, datos=datos)

        visita = Visita(
            parque = parque,
            rating = rating,
            fecha_visita = fecha_visita,
            detalles = detalles,
            visitante = session['usuario_id']
        )

        db.session.add(visita)
        db.session.commit()

        flash('Visita creada correctamente', 'success')
        return redirect(url_for('dashboard'))

    return render_template('visitas/nueva_visita.html', errores={}, datos={})


@app.route('/visitas/editar/<int:id>', methods=['GET','POST'])
@login_required
def editar_visita(id):
    errores = {}
    fecha_maxima = date.today().strftime('%Y-%m-%d')
    visita= Visita.query.get_or_404(id)

    if visita.visitante != session['usuario_id']:
        flash('No tienes permisos para editar esta visita', 'danger')
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        parque = request.form['parque'].strip()
        rating = request.form['rating']
        fecha_visita = request.form['fecha_visita']
        detalles = request.form['detalles']

               #validar parque
        if len(parque) == 0:
            errores['parque'] = 'El nombre del parque es requerido'
        elif parque != visita.parque:  # Verificar si el parque ingresado es diferente al original
            errores['parque'] = f'El nombre del parque debe ser igual al que ya estaba registrado: {visita.parque}'

        #validar rating
        if len(rating) == 0:
            errores['rating'] = 'El rating es requerido'
        if not rating.isdigit():
            errores['rating'] = 'El rating debe ser un número'
        if int(rating) < 1 or int(rating) > 5:
            errores['rating'] = 'El rating debe estar entre 1 y 5'

        #validar fecha de visita
        if len(fecha_visita) == 0:
            errores['fecha_visita'] = 'La fecha de visita es requerida'
        elif fecha_visita > fecha_maxima:
            errores['fecha_visita'] = 'La fecha de visita no puede ser mayor a la fecha actual'
        
        #validar detalles
        if len(detalles) == 0:
            errores['detalles'] = 'Los detalles son requeridos'

        if errores:
            return render_template('visitas/editar_visita.html', errores=errores, visita=visita, fecha_maxima=fecha_maxima)
        
        visita.parque = parque
        visita.rating = int(rating)
        visita.fecha_visita = fecha_visita
        visita.detalles = detalles

        db.session.commit()
        flash("Visita actualizada con éxito", "success")
        return redirect(url_for('dashboard'))
    return render_template('visitas/editar_visita.html', errores={}, visita=visita, fecha_maxima=fecha_maxima)
        
@app.route('/visitas/eliminar/<int:id>', methods=['GET','POST'])
@login_required
def borrar_visita(id):
    visita = Visita.query.get_or_404(id)

    if visita.visitante != session['usuario_id']:
        flash('No tienes permisos para eliminar esta visita', 'danger')
        return redirect(url_for('dashboard'))

    db.session.delete(visita)
    db.session.commit()
    flash('Visita eliminada correctamente', 'success')
    return redirect(url_for('dashboard'))

@app.route('/visitas/ver/<int:id>')
@login_required
def ver_visita(id):
    visita = Visita.query.get_or_404(id)
    user_id = session['usuario_id']
    usuario_ya_dio_me_gusta = MeGusta.query.filter_by(visita_id=id, usuario_id=user_id).first() is not None


    return render_template('visitas/ver_visita.html', visita=visita, usuario_ya_dio_me_gusta=usuario_ya_dio_me_gusta)

#Rutas de likes
@app.route('/visita/<int:visita_id>/me_gusta', methods=['POST'])
@login_required
def dar_me_gusta(visita_id):
    user_id = session['usuario_id']
    
    visita = Visita.query.get_or_404(visita_id)
    me_gusta = MeGusta.query.filter_by(visita_id=visita_id, usuario_id=user_id).first()

    if me_gusta:
        flash('Ya has dado "Me gusta" a esta visita', 'info')
        return redirect(url_for('ver_visita', id=visita_id))
    
    
    nuevo_me_gusta = MeGusta(visita_id=visita_id, usuario_id=user_id)
    db.session.add(nuevo_me_gusta)
    db.session.commit()

    flash('¡Gracias por tu "Me gusta"!', 'success')
    return redirect(url_for('ver_visita', id=visita_id))

if __name__ == '__main__':
    app.run(debug=True)

