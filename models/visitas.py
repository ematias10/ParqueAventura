from models import db

class Visita(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    parque = db.Column(db.String(50), nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    fecha_visita = db.Column(db.Date, nullable=False)
    detalles = db.Column(db.Text, nullable=False)
    visitante = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)

    #relacion con likes
    me_gusta = db.relationship('Usuario', secondary='me_gusta', backref=db.backref('me_gusta_visitas'))
    #relacion con usuario
    usuario = db.relationship('Usuario', backref=db.backref('visitas', lazy=True))

