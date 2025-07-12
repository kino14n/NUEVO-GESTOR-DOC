from flask_sqlalchemy import SQLAlchemy
from datetime import date

db = SQLAlchemy()

class Document(db.Model):
    __tablename__ = 'documents'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    date = db.Column(db.Date, nullable=False, default=date.today)
    path = db.Column(db.String(255), nullable=False)
    codigos_extraidos = db.Column(db.Text)

    def __repr__(self):
        return f"<Document {self.name}>"
