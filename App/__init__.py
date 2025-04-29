import os
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_mail import Mail
from flask_babel import Babel
from dotenv import load_dotenv
from flask import Flask

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

    # Initialisation des extensions avec sélecteur
    db.init_app(app)
    mail.init_app(app)
    

    login_manager = LoginManager()
    login_manager.login_view = 'auth.login_fr'
    login_manager.init_app(app)

    # Blueprints
    from .auth import auth
    from .views import views
    app.register_blueprint(auth, url_prefix='/')
    app.register_blueprint(views, url_prefix='/')

    # Gestionnaire d’erreur 404 global
    @app.errorhandler(404)
    def handle_404(error):
        # Récupère la langue via ?lang=fr|en|ar, ou défaut 'fr'
        from flask import request, render_template
        lang = request.args.get('lang', 'fr').lower()
        if lang not in ('fr', 'en', 'ar'):
            lang = 'fr'
        # Affiche templates/FR/404.html ou EN/404.html ou AR/404.html
        return render_template(f"{lang}/404.html"), 404

    # Login
    from .models import Formulaire
    @login_manager.user_loader
    def load_user(id):
        return Formulaire.query.get(int(id))


    return app
