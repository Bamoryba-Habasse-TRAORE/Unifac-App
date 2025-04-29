from flask import Flask, redirect, url_for
from .auth import auth
from .views import views
from . import os 
from flask_login import LoginManager
from .models import Formulaire

def create_app():
    app = Flask(__name__) 
    # Configuration de l'application
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')  # Remplace par une clé secrète pour la production
    login_manager = LoginManager()
    login_manager.login_view = 'auth.login_fr'  # ou la route de login de ton choix
    login_manager.init_app(app)
    @login_manager.user_loader
    def load_user(user_id):
        return Formulaire.query.get(int(user_id))
    # (Optionnel) Attacher le login_manager à l'application pour pouvoir y accéder via current_app
    app.login_manager = login_manager
    # Enregistrement des blueprints
    app.register_blueprint(auth, url_prefix='/auth')  # Routes d'authentification
    app.register_blueprint(views, url_prefix='/views')  # Routes des vues (accueil, dashboard...)
    @app.route('/')
    def index():
        return redirect(url_for('views.home_fr'))
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=False)