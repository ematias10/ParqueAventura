from models import db

class MeGusta(db.Model):
    __tablename__ = 'me_gusta'
    visita_id = db.Column(db.Integer, db.ForeignKey('visita.id'), primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), primary_key=True)