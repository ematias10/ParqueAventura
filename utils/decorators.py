from flask import session, redirect, url_for, flash
from functools import wraps

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'usuario_id' not in session:
            flash("Debes iniciar sesion para acceder a esta pagina.", "warning")
            print("Debes iniciar sesion para acceder a esta pagina.")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function