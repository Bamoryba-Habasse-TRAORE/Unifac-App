import os
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_mail import Mail
from flask_babel import Babel
from dotenv import load_dotenv
from flask import Flask, render_template, request

# Initialisation des extensions
db = SQLAlchemy()
mail = Mail()
babel = Babel()
load_dotenv()

def create_app():
    app = Flask(__name__, template_folder="templates", static_folder="static")

    # Configuration générale
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')

    # Configuration de la base de données PostgreSQL
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DATABASE_URL")
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Configuration Email
    app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER')
    app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT'))
    app.config['MAIL_USE_SSL'] = os.getenv('MAIL_USE_SSL') == 'True'
    app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
    app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
    app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_DEFAULT_SENDER')

    # Babel / Langues
    app.config['BABEL_DEFAULT_LOCALE'] = 'fr'
    app.config['BABEL_SUPPORTED_LOCALES'] = ['fr', 'en', 'ar']

    # Sélecteur de langue compatible Flask-Babel 4.0.0
    def select_locale():
        lang = request.args.get('lang')
        if lang and lang in app.config['BABEL_SUPPORTED_LOCALES']:
            return lang
        return request.accept_languages.best_match(app.config['BABEL_SUPPORTED_LOCALES'])

    # Initialisation des extensions avec sélecteur
    db.init_app(app)
    mail.init_app(app)
    babel.init_app(app, locale_selector=select_locale)

    login_manager = LoginManager()
    login_manager.login_view = 'auth.login_fr'
    login_manager.init_app(app)

    # Blueprints
    from .auth import auth
    from .views import views
    app.register_blueprint(auth, url_prefix='/')
    app.register_blueprint(views, url_prefix='/')

    # Login
    from .models import Formulaire
    @login_manager.user_loader
    def load_user(id):
        return Formulaire.query.get(int(id))

    # Gestion des erreurs
    @app.errorhandler(404)
    def page_not_found(e):
        locale = select_locale()
        return render_template(f"{locale}/404.html"), 404

    return app
