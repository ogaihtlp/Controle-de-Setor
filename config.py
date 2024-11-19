class Config:
    SECRET_KEY = 'sua-chave-secreta'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///seu_banco.db'  # ou sua URL do banco
    SQLALCHEMY_TRACK_MODIFICATIONS = False