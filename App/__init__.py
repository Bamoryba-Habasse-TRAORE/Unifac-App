import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_mail import Mail
from dotenv import load_dotenv
from flask_babel import Babel

# Création de l'instance
db = SQLAlchemy()
mail = Mail()
load_dotenv()
babel = Babel()

def create_app():
    app = Flask(__name__, template_folder=os.path.join(os.path.pardir, 'templates'), static_folder=os.path.abspath("static"))
    # Configuration de l'application
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')

    # Configuration de la base de données SQLite
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///formulaire.db'  # SQLite
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # Désactiver les avertissements
    app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER')  # Remplace par ton serveur SMTP
    app.config['MAIL_PORT'] = os.getenv('MAIL_PORT') # Port pour SSL
    app.config['MAIL_USE_SSL'] = os.getenv('MAIL_USE_SSL')
    app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME') # Remplace par ton email
    app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')  # Remplace par ton mot de passe
    app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_DEFAULT_SENDER') # Remplace par ton email
    app.config['BABEL_DEFAULT_LOCALE'] = 'fr'
    app.config['BABEL_SUPPORTED_LOCALES'] = ['fr', 'en', 'ar']

    db.init_app(app)
    mail.init_app(app)
    babel.init_app(app)
    login_manager = LoginManager()
    login_manager.login_view = 'auth.login_fr' 
    login_manager.init_app(app)     
    from .auth import auth
    from .views import views
    app.register_blueprint(auth, url_prefix='/')
    app.register_blueprint(views, url_prefix='/')
    with app.app_context():
        create_database(app)
    from .models import Formulaire 
    @login_manager.user_loader
    def load_user(id):
        return Formulaire.query.get(int(id))
    return app
def create_database(app):
    with app.app_context():
        db.create_all()  
    print('📦 Base de données créée !')
