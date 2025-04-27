import re, os
from flask import Blueprint, render_template, current_app, request
from flask_login import login_required, current_user
from .unifac_diffusion import unifac_diffusion
from .models import Calculation
from flask import make_response
from . import db
from .Dic import compound_translations
from weasyprint import HTML
from datetime import datetime


views = Blueprint('views', __name__, template_folder=os.path.join(os.path.pardir, 'templates'), static_folder=os.path.abspath("static"))
# Fonction pour valider l'email
def is_valid_email(email):
    """ Vérifie si l'email est au format valide """
    return re.match(r"[^@]+@[^@]+\.[^@]+", email) is not None
# ------------------- PAGE D'ACCUEIL FR ------------------- #
@views.route('/')
def home_fr():
    current_app.logger.info("Rendering Home_fr.html template ...")
    # Vérification de l'email de l'utilisateur actuel
    if current_user.is_authenticated and not is_valid_email(current_user.email):
        current_app.logger.warning("Email non valide pour l'utilisateur connecté")
    return render_template("FR/Home_fr.html", user=current_user)

@views.route('/dashboard_fr', methods=['GET', 'POST'])
@login_required
def dashboard_fr():
    # On passe le dictionnaire complet pour afficher les noms traduits
    compounds = {key: compound_translations[key]["fr"] for key in compound_translations}
    if request.method == 'POST':
        try:
            compound_A = request.form['compound_A']
            compound_B = request.form['compound_B']
            x_A = float(request.form['x_A'].replace(',', '.'))
            T = float(request.form['T'])
            D_exp = float(request.form['D_exp'])
            # Convertir le nom affiché en nom technique (anglais)
            compound_A_english = translate_to_english(compound_A, 'fr')
            compound_B_english = translate_to_english(compound_B, 'fr')
            if compound_A_english is None or compound_B_english is None:
                raise ValueError("Composé inconnu ou traduction non trouvée")
            D_AB, error = unifac_diffusion(compound_A_english, compound_B_english, x_A, T, D_exp)
            result = {'D_AB': round(D_AB, 6), 'error': round(error, 2)}
            new_calc = Calculation(user_id=current_user.id, compound_A=compound_A, compound_B=compound_B, x_A=x_A, T=T, D_exp=D_exp, D_calc=D_AB, error=error)
            db.session.add(new_calc)
            db.session.commit()
            return render_template("FR/Dashboard_fr.html", user=current_user, result=result, compounds=compounds)
        except Exception as e:
            return render_template("FR/Dashboard_fr.html", user=current_user, error_message=str(e), compounds=compounds)
    return render_template("FR/Dashboard_fr.html", user=current_user, compounds=compounds)
# ------------------- DASHBOARD EN ------------------- #
@views.route('/home_en')
def home_en():
    # Vérification de l'email de l'utilisateur actuel
    if current_user.is_authenticated and not is_valid_email(current_user.email):
        current_app.logger.warning("Invalid email for the logged-in user")
    return render_template("EN/Home_en.html", user=current_user)

@views.route('/dashboard_en', methods=['GET', 'POST'])
@login_required
def dashboard_en():
    # Dictionnaire complet pour afficher les noms traduits en anglais
    compounds = {key: compound_translations[key]["en"] for key in compound_translations}
    if request.method == 'POST':
        try:
            compound_A = request.form['compound_A']
            compound_B = request.form['compound_B']
            x_A = float(request.form['x_A'].replace(',', '.'))
            T = float(request.form['T'])
            D_exp = float(request.form['D_exp'])
            # Convertir le nom affiché en nom technique (anglais)
            compound_A_english = translate_to_english(compound_A, 'en')
            compound_B_english = translate_to_english(compound_B, 'en')
            if compound_A_english is None or compound_B_english is None:
                raise ValueError("Unknown compound or translation not found")
            D_AB, error = unifac_diffusion(compound_A_english, compound_B_english, x_A, T, D_exp)
            result = {'D_AB': round(D_AB, 6), 'error': round(error, 2)}
            new_calc = Calculation(user_id=current_user.id, compound_A=compound_A, compound_B=compound_B, x_A=x_A, T=T, D_exp=D_exp, D_calc=D_AB, error=error)
            db.session.add(new_calc)
            db.session.commit()
            return render_template("EN/Dashboard_en.html", user=current_user, result=result, compounds=compounds)
        except Exception as e:
            return render_template("EN/Dashboard_en.html", user=current_user, error_message=str(e), compounds=compounds)
    return render_template("EN/Dashboard_en.html", user=current_user, compounds=compounds)
# ------------------- DASHBOARD AR ------------------- #
@views.route('/home_ar')
def home_ar():
    # Vérification de l'email de l'utilisateur actuel
    if current_user.is_authenticated and not is_valid_email(current_user.email):
        current_app.logger.warning("البريد الإلكتروني غير صالح للمستخدم المتصل")
    return render_template("AR/Home_ar.html", user=current_user)

@views.route('/dashboard_ar', methods=['GET', 'POST'])
@login_required
def dashboard_ar():
    # Dictionnaire complet pour afficher les noms traduits en arabe
    compounds = {key: compound_translations[key]["ar"] for key in compound_translations}
    if request.method == 'POST':
        try:
            compound_A = request.form['compound_A']
            compound_B = request.form['compound_B']
            x_A = float(request.form['x_A'].replace(',', '.'))
            T = float(request.form['T'])
            D_exp = float(request.form['D_exp'])
            # Convertir le nom affiché en nom technique (anglais)
            compound_A_english = translate_to_english(compound_A, 'ar')
            compound_B_english = translate_to_english(compound_B, 'ar')
            if compound_A_english is None or compound_B_english is None:
                raise ValueError("مركب غير معروف أو الترجمة غير موجودة")
            D_AB, error = unifac_diffusion(compound_A_english, compound_B_english, x_A, T, D_exp)
            result = {'D_AB': round(D_AB, 6), 'error': round(error, 2)}
            new_calc = Calculation(user_id=current_user.id, compound_A=compound_A, compound_B=compound_B, x_A=x_A, T=T, D_exp=D_exp, D_calc=D_AB, error=error)
            db.session.add(new_calc)
            db.session.commit()
            return render_template("AR/Dashboard_ar.html", user=current_user, result=result, compounds=compounds)
        except Exception as e:
            return render_template("AR/Dashboard_ar.html", user=current_user, error_message=str(e), compounds=compounds)  
    return render_template("AR/Dashboard_ar.html", user=current_user, compounds=compounds)
#....................Historiques Calcul.....................#
@views.route('/calculs_history_fr')
@login_required
def calculshistory_fr():
    from .models import Calculation
    user_calculations = Calculation.query.filter_by(user_id=current_user.id).order_by(Calculation.timestamp.desc()).all()
    return render_template("FR/Calculations_History.html", user=current_user, calculations=user_calculations)
@views.route('/calculs_history_en')
@login_required
def calculshistory_en():
    from .models import Calculation
    user_calculations = Calculation.query.filter_by(user_id=current_user.id).order_by(Calculation.timestamp.desc()).all()
    return render_template("EN/Calculations_History.html", user=current_user, calculations=user_calculations)
@views.route('/calculs_history_ar')
@login_required
def calculshistory_ar():
    from .models import Calculation
    user_calculations = Calculation.query.filter_by(user_id=current_user.id).order_by(Calculation.timestamp.desc()).all()
    return render_template("AR/Calculations_History.html", user=current_user, calculations=user_calculations)
#....................Export/pdf.....................#
@views.route('/export_pdf')
@login_required
def export_pdf():
    calculations = Calculation.query.filter_by(user_id=current_user.id)\
                                     .order_by(Calculation.timestamp.desc())\
                                     .all()
    html = render_template(
      "pdf.html",
      user=current_user,
      calculations=calculations,
      now=datetime.now()
    )
    pdf = HTML(string=html).write_pdf()
    response = make_response(pdf)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] =\
        'attachment; filename=historique_diffusion.pdf'
    return response
#..................translate...........................#
def translate_to_english(compound_name, language='en'):
    inverse_translations = {"fr": {v["fr"]: k for k, v in compound_translations.items()}, "ar": {v["ar"]: k for k, v in compound_translations.items()},"en": {v["en"]: k for k, v in compound_translations.items()},}
    return inverse_translations.get(language, {}).get(compound_name, None)

# --- Simulation de diffusion de gaz ---

@views.route('/simulation')
def simulation():
    return render_template("FR/simulation.html")
@views.route('/simulation_en')
def simulation_en():
    return render_template("EN/simulation.html")
@views.route('/simulation_ar')
def simulation_ar():
    return render_template("AR/simulation.html")
