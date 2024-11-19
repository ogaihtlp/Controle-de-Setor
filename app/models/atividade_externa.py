from app import db
from datetime import datetime

class AtividadeExterna(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    atendente_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    atendente_nome = db.Column(db.String(50), nullable=False)
    setor = db.Column(db.String(50), nullable=False)
    hora_inicio = db.Column(db.DateTime, nullable=False)
    hora_fim = db.Column(db.DateTime, nullable=False)
    descricao = db.Column(db.Text, nullable=False)
    data_registro = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<AtividadeExterna {self.id} - {self.atendente_nome}>'