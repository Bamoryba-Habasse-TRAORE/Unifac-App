import os
from flask import Flask, request, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_mail import Mail
from flask_babel import Babel, get_locale
from dotenv import load_dotenv

db      = SQLAlchemy()
mail    = Mail()
babel   = Babel()
load_dotenv()

def create_app():
    app = Flask(__name__, template_folder="templates", static_folder="static")

    # — Configurations (SECRET_KEY, DB, Mail…) —
    app.config['SECRET_KEY']               = os.getenv('SECRET_KEY')
    app.config['SQLALCHEMY_DATABASE_URI']  = os.getenv('DATABASE_URL')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['MAIL_SERVER']              = os.getenv('MAIL_SERVER')
    app.config['MAIL_PORT']                = int(os.getenv('MAIL_PORT'))
    app.config['MAIL_USE_SSL']             = os.getenv('MAIL_USE_SSL') == 'True'
    app.config['MAIL_USERNAME']            = os.getenv('MAIL_USERNAME')
    app.config['MAIL_PASSWORD']            = os.getenv('MAIL_PASSWORD')
    app.config['MAIL_DEFAULT_SENDER']      = os.getenv('MAIL_DEFAULT_SENDER')

    # — Babel / Langues —
    app.config['BABEL_DEFAULT_LOCALE']      = 'fr'
    app.config['BABEL_SUPPORTED_LOCALES']   = ['fr', 'en', 'ar']
    db.init_app(app)
    mail.init_app(app)
    babel.init_app(app)

    # Sélecteur automatique de la langue
    @babel.localeselector
    def select_locale():
        return request.accept_languages.best_match(app.config['BABEL_SUPPORTED_LOCALES'])

    # — Login Manager —
    login_manager = LoginManager()
    login_manager.login_view = 'auth.login_fr'
    login_manager.init_app(app)

    # — Blueprints —
    from .auth  import auth
    from .views import views
    app.register_blueprint(auth, url_prefix='/')
    app.register_blueprint(views, url_prefix='/')

    # — Handler 404 sans ?lang= —
    @app.errorhandler(404)
    def handle_404(error):
        lang = str(get_locale())  # 'fr', 'en' ou 'ar'
        return render_template(f"{lang}/404.html"), 404

    # — User loader —
    from .models import Formulaire
    @login_manager.user_loader
    def load_user(user_id):
        return Formulaire.query.get(int(user_id))

    return app
