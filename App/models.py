from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from . import db
import re
from datetime import datetime

class Formulaire(db.Model, UserMixin):
    __tablename__ = 'formulaire'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    username = db.Column(db.String(100), nullable=False)
    password = db.Column(db.String(200), nullable=False)
    reset_token = db.Column(db.String(200), nullable=True)
    reset_token_created_at = db.Column(db.DateTime, nullable=True)
    is_active = db.Column(db.Boolean, default=True) 
    confirmation_code = db.Column(db.String(6), nullable=True)
    is_confirmed = db.Column(db.Boolean, default=False)
    failed_attempts = db.Column(db.Integer, default=0)
    lockout_time = db.Column(db.DateTime, nullable=True)
    lockout_level = db.Column(db.Integer, default=0)

    # Relation avec les calculs (calculations)
    calculations = db.relationship('Calculation', backref='user', lazy=True)
    def __repr__(self):
        return f'<Formulaire {self.username}>'
    def set_password(self, password):
        if len(password) < 8:
            raise ValueError("Le mot de passe doit comporter au moins 8 caractères.")
        if not any(c.islower() for c in password):
            raise ValueError("Le mot de passe doit contenir au moins une lettre minuscule.")
        if not any(c.isupper() for c in password):
            raise ValueError("Le mot de passe doit contenir au moins une lettre majuscule.")
        if not any(c.isdigit() for c in password):
            raise ValueError("Le mot de passe doit contenir au moins un chiffre.")
        self.password = generate_password_hash(password, method='pbkdf2:sha256')
    def check_password(self, password):
        return check_password_hash(self.password, password)
    @staticmethod
    def is_valid_email(email):
        return re.match(r"[^@]+@[^@]+\.[^@]+", email) is not None
    def get_id(self):
        return str(self.id)
# ✅ Modèle pour stocker les historiques de calculs
class Calculation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('formulaire.id'), nullable=False)
    compound_A = db.Column(db.String(100))
    compound_B = db.Column(db.String(100))
    x_A = db.Column(db.Float)
    T = db.Column(db.Float)
    D_exp = db.Column(db.Float)
    D_calc = db.Column(db.Float)
    error = db.Column(db.Float)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
