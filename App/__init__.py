import os
from flask import Flask, request, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_mail import Mail
from flask_babel import Babel, get_locale
from dotenv import load_dotenv

db = SQLAlchemy()
mail = Mail()
babel = Babel()
load_dotenv()

def get_locale():
    return request.accept_languages.best_match(['fr', 'en', 'ar'])

def create_app():
    app = Flask(__name__, template_folder="templates", static_folder="static")

    # Configurations
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER')
    app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT'))
    app.config['MAIL_USE_SSL'] = os.getenv('MAIL_USE_SSL') == 'True'
    app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
    app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
    app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_DEFAULT_SENDER')
    app.config['BABEL_DEFAULT_LOCALE'] = 'fr'
    app.config['BABEL_SUPPORTED_LOCALES'] = ['fr', 'en', 'ar']

    db.init_app(app)
    mail.init_app(app)
    babel.init_app(app, locale_selector=get_locale)

    login_manager = LoginManager()
    login_manager.login_view = 'auth.login_fr'
    login_manager.init_app(app)

    from .auth import auth
    from .views import views
    app.register_blueprint(auth, url_prefix='/')
    app.register_blueprint(views, url_prefix='/')

    @app.errorhandler(404)
    def handle_404(error):
        lang = str(get_locale())
        return render_template(f"{lang}/404.html"), 404

    from .models import Formulaire
    @login_manager.user_loader
    def load_user(user_id):
        return Formulaire.query.get(int(user_id))

    return app
