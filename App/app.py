from flask import Flask, redirect, url_for
from .auth import auth
from .views import views
from . import os 

def create_app():
    app = Flask(__name__) 
    # Configuration de l'application
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')  # Remplace par une clé secrète pour la production
    # Enregistrement des blueprints
    app.register_blueprint(auth, url_prefix='/auth')  # Routes d'authentification
    app.register_blueprint(views, url_prefix='/views')  # Routes des vues (accueil, dashboard...)
    @app.route('/')
    def index():
        return redirect(url_for('views.home_fr'))
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
