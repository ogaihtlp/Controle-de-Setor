from app import db
from datetime import datetime

class Atendimento(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    origem = db.Column(db.String(50), nullable=False)
    protocolo = db.Column(db.String(50), unique=True, nullable=False)
    status = db.Column(db.String(20), nullable=False)
    atendente_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    atendente_responsavel = db.Column(db.String(50), nullable=False)  # Nome do atendente
    suporte_adicional = db.Column(db.String(50))  # Para nível 3
    departamento = db.Column(db.String(50))
    motivo = db.Column(db.Text)
    nome_cliente = db.Column(db.String(100), nullable=False)
    numero = db.Column(db.String(50))
    data = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    data_finalizacao = db.Column(db.DateTime)
    data_ultima_mensagem = db.Column(db.DateTime)
    possui_anexo = db.Column(db.Boolean, default=False)
    avaliacao = db.Column(db.Integer)
    nivel = db.Column(db.Integer, nullable=False)
    observacoes = db.Column(db.Text)

    def __repr__(self):
        return f'<Atendimento {self.protocolo}>'