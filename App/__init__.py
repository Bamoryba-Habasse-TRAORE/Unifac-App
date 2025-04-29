import os
from flask import Flask, request, render_template, current_app
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_mail import Mail
from flask_babel import Babel, get_locale
from jinja2 import TemplateNotFound
from dotenv import load_dotenv

db = SQLAlchemy()
mail = Mail()
babel = Babel()
load_dotenv()


def select_locale():
    """
    Callback pour Flask-Babel :
    1) si l'URL contient ?lang=fr|en|ar, on l'utilise
    2) sinon on se base sur l'en-tête Accept-Language du navigateur
    """
    lang = request.args.get('lang', type=str)
    if lang in ['fr', 'en', 'ar']:
        return lang
    return request.accept_languages.best_match(['fr', 'en', 'ar'])


def create_app():
    app = Flask(__name__, template_folder="templates", static_folder="static")

    # Configurations générales
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER')
    app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT', 0))
    app.config['MAIL_USE_SSL'] = os.getenv('MAIL_USE_SSL') == 'True'
    app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
    app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
    app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_DEFAULT_SENDER')

    # Configuration Babel
    app.config['BABEL_DEFAULT_LOCALE'] = 'fr'
    app.config['BABEL_SUPPORTED_LOCALES'] = ['fr', 'en', 'ar']

    db.init_app(app)
    mail.init_app(app)
    babel.init_app(app, locale_selector=select_locale)

    # Setup de Flask-Login
    login_manager = LoginManager()
    login_manager.login_view = 'auth.login_fr'
    login_manager.init_app(app)

    # Enregistrement des blueprints
    from .auth import auth
    from .views import views
    app.register_blueprint(auth, url_prefix='/')
    app.register_blueprint(views, url_prefix='/')

    @app.errorhandler(404)
    def handle_404(error):
        """
        Handler pour les 404 :
        - sélectionne la locale via flask_babel.get_locale()
        - tente de rendre templates/FR/404.html, EN/404.html ou AR/404.html
        - en cas d'absence, fallback sur templates/404.html générique
        """
        code = str(get_locale()).upper().split('_')[0]  # ex. "fr_FR" -> "FR"
        template_path = f"{code}/404.html"
        try:
            return render_template(template_path, lang_code=code.lower(), path=request.path), 404
        except TemplateNotFound:
            current_app.logger.warning(f"[404 handler] Template introuvable : {template_path}")
            return render_template("404.html", lang_code=code.lower(), path=request.path), 404

    from .models import Formulaire

    @login_manager.user_loader
    def load_user(user_id):
        return Formulaire.query.get(int(user_id))

    return app
