from flask import Flask, redirect, url_for
from auth import auth
from views import views

def create_app():
    app = Flask(__name__) 
    # Configuration de l'application
    app.config['SECRET_KEY'] = 'ton_secret_key'  # Remplace par une clé secrète pour la production
    # Enregistrement des blueprints
    app.register_blueprint(auth, url_prefix='/auth')  # Routes d'authentification
    app.register_blueprint(views, url_prefix='/views')  # Routes des vues (accueil, dashboard...)
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
