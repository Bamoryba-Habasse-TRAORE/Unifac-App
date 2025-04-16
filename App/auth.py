import re, os
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_user, login_required, logout_user, current_user
from werkzeug.security import check_password_hash, generate_password_hash
from .models import Formulaire, db
from flask_mail import Message
from . import mail
import secrets
from datetime import datetime, timedelta
from flask_babel import get_locale
from itsdangerous import URLSafeTimedSerializer as Serializer, BadSignature, SignatureExpired

auth = Blueprint('auth', __name__, template_folder=os.path.join(os.path.pardir, 'templates'), static_folder=os.path.abspath("static"))
RESET_SALT = os.environ.get("RESET_SALT", "reset_password-salt")

# ----------------- Fonctions pour la gestion du token ----------------- #
def generate_reset_token(email):  # ici
    s = Serializer(current_app.config['SECRET_KEY'], salt=RESET_SALT)
    return s.dumps({'user_email': email})

def verify_reset_token(token, expires_sec=3600):
    s = Serializer(current_app.config['SECRET_KEY'], salt=RESET_SALT)
    try:
        data = s.loads(token, max_age=expires_sec)  # ← ici on vérifie bien le délai
    except Exception:
        return None
    return data.get('user_email')


# ----------------- Fonction pour vérifier l'expiration d'un token (si besoin) ----------------- #
def is_token_expired(token_timestamp):
    """ Vérifie si le token est expiré (expiration après 24 heures) """
    expiration_time = timedelta(hours=0.166666667)  # environ 10 minutes (0.1666 h)
    return datetime.utcnow() > token_timestamp + expiration_time

# ----------------- Envoi de l'email de réinitialisation (fonction supplémentaire) ----------------- #
def send_reset_email(email, token=None, language='fr'):
    # Sécurité : force une langue valide
    supported_languages = ['fr', 'en', 'ar']
    lang = language if language in supported_languages else 'fr'

    # Construction de l'URL
    try:
        reset_url = url_for(f'auth.reset_password_{lang}', token=token, _external=True)
    except Exception as e:
        print(f"[ERREUR URL RESET] Langue: {lang} | Exception: {e}")
        reset_url = url_for('auth.reset_password_fr', token=token, _external=True)

    subjects = {
        'fr': "Réinitialisation de votre mot de passe",
        'en': "Reset your password",
        'ar': "إعادة تعيين كلمة المرور الخاصة بك"
    }

    bodies = {
        'fr': f"Bonjour,\n\nPour réinitialiser votre mot de passe, cliquez sur le lien suivant :\n\n{reset_url}\n\nSi vous n'avez pas fait cette demande, ignorez simplement cet e-mail.",
        'en': f"Hello,\n\nTo reset your password, click the following link:\n\n{reset_url}\n\nIf you did not request this, just ignore this email.",
        'ar': f"مرحبًا،\n\nلإعادة تعيين كلمة المرور الخاصة بك، انقر فوق الرابط التالي:\n\n{reset_url}\n\nإذا لم تطلب ذلك، تجاهل هذا البريد الإلكتروني."
    }

    msg = Message(
        subject=subjects.get(lang, subjects['fr']),
        sender=current_app.config['MAIL_DEFAULT_SENDER'],
        recipients=[email]
    )
    msg.body = bodies.get(lang, bodies['fr'])

    try:
        mail.send(msg)
    except Exception as e:
        print(f"Erreur lors de l'envoi de l'e-mail de réinitialisation : {e}")
        
# ----------------- Fonctions de validation d'email et de mot de passe ----------------- #
def is_valid_email(email):
    """ Vérifie si l'email est au format valide """
    return re.match(r"[^@]+@[^@]+\.[^@]+", email) is not None

def is_valid_password(password):
    """
    Vérifie si le mot de passe est valide (au moins 8 caractères, contient une majuscule, 
    une minuscule, un chiffre et un caractère spécial)
    """
    if len(password) < 8:
        return False, "Le mot de passe doit comporter au moins 8 caractères."
    if not re.search(r"[A-Z]", password):
        return False, "Le mot de passe doit contenir au moins une lettre majuscule."
    if not re.search(r"[a-z]", password):
        return False, "Le mot de passe doit contenir au moins une lettre minuscule."
    if not re.search(r"\d", password):
        return False, "Le mot de passe doit contenir au moins un chiffre."
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        return False, "Le mot de passe doit contenir au moins un caractère spécial."
    return True, ""

# ----------------- Gestion de l'inscription ----------------- #
def handle_signup(email, username, password1, password2, language):
    """ Fonction pour gérer l'inscription d'un utilisateur avec validation de l'email """
    if not is_valid_email(email):
        flash('L\'email n\'est pas valide.' if language == 'fr' else 
              'The email is not valid.' if language == 'en' else 
              'البريد الإلكتروني غير صالح.', category='error')
        return None

    existing_username = Formulaire.query.filter_by(username=username).first()
    if existing_username:
        flash('Ce nom d\'utilisateur est déjà pris.' if language == 'fr' else 
              'This username is already taken.' if language == 'en' else 
              'اسم المستخدم هذا مستعمل بالفعل.', category='error')
        return None

    valid, message = is_valid_password(password1)
    if not valid:
        flash(message, category='error')
        return None

    if password1 != password2:
        flash('Les mots de passe ne correspondent pas.' if language == 'fr' else 
              'Passwords do not match.' if language == 'en' else 
              'كلمتا المرور غير متطابقتين.', category='error')
        return None

    user = Formulaire.query.filter_by(email=email).first()
    if user:
        flash('Un compte avec cet email existe déjà.' if language == 'fr' else 
              'An account with this email already exists.' if language == 'en' else 
              'يوجد حساب بهذا البريد الإلكتروني.', category='error')
    else:
        try:
            new_user = Formulaire(email=email, username=username)
            new_user.set_password(password1)
            confirmation_code = generate_confirmation_code()
            new_user.confirmation_code = confirmation_code
            new_user.is_confirmed = False
            new_user.confirmation_sent_at = datetime.utcnow()

            db.session.add(new_user)
            db.session.commit()

            send_confirmation_email(email, confirmation_code)
            login_user(new_user, remember=True)
            
            
            return redirect(url_for(f'auth.confirm_{language}'))
            
        except ValueError as ve:
            flash(str(ve), category='error')

    return None
# ----------------- Routes FRANÇAIS ----------------- #
@auth.route('/login_fr', methods=['GET', 'POST'])
def login_fr():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = Formulaire.query.filter_by(email=email).first()

        if user and not user.is_confirmed:
            flash('Votre compte n\'est pas encore confirmé.', category='error')
            return redirect(url_for('auth.confirm_fr'))

        if user:
            return handle_login(user, password, 'fr')  # tu peux passer la langue ici
        else:
            flash('Email ou mot de passe incorrect.', category='error')

    return render_template("FR/Connexion_fr.html", user=current_user)

@auth.route('/inscription_fr', methods=['GET', 'POST'])
def inscription_fr():
    if request.method == 'POST':
        email = request.form['email']
        username = request.form['username']
        password1 = request.form['password']
        password2 = request.form['confirm_password']
        result = handle_signup(email, username, password1, password2, 'fr')
        if result:
            return result
    return render_template("FR/Formulaire_fr.html", user=current_user)

# ----------------- Routes ENGLISH ----------------- #
@auth.route('/login_en', methods=['GET', 'POST'])
def login_en():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = Formulaire.query.filter_by(email=email).first()
        if user and not user.is_confirmed:
            flash('Your account is not yet confirmed.', category='error')
            return redirect(url_for('auth.confirm_en'))  # ou la version langue
        if user:
            return handle_login(user, password, 'en')  # tu peux passer la langue ici
        else:
            flash('Incorrect email or password.', category='error')
    return render_template("EN/Connexion_en.html", user=current_user)

@auth.route('/signup_en', methods=['GET', 'POST'])
def signup_en():
    if request.method == 'POST':
        email = request.form['email']
        username = request.form['username']
        password1 = request.form['password']
        password2 = request.form['confirm_password']
        result = handle_signup(email, username, password1, password2, 'en')
        if result:
            return result
    return render_template("EN/Formulaire_en.html", user=current_user)

# ----------------- Routes ARABE ----------------- #
@auth.route('/login_ar', methods=['GET', 'POST'])
def login_ar():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = Formulaire.query.filter_by(email=email).first()
        if user and not user.is_confirmed:
            flash("لم يتم تأكيد حسابك بعد.", category='error')
            return redirect(url_for('auth.confirm_ar'))  # ou la version langue
        if user:
            return handle_login(user, password, 'ar') 
        else:
            flash('البريد الإلكتروني أو كلمة المرور غير صحيحة', category='error')
    return render_template("AR/Connexion_ar.html", user=current_user)

@auth.route('/signup_ar', methods=['GET', 'POST'])
def signup_ar():
    if request.method == 'POST':
        email = request.form['email']
        username = request.form['username']
        password1 = request.form['password']
        password2 = request.form['confirm_password']
        result = handle_signup(email, username, password1, password2, 'ar')
        if result:
            return result
    return render_template("AR/Formulaire_ar.html", user=current_user)

# ----------------- Autres routes ----------------- #
@auth.route('/logout')
@login_required
def logout():
    user_language = request.args.get('lang', 'fr')
    logout_user()
    if user_language == 'en':
        return redirect(url_for('views.home_en'))
    elif user_language == 'ar':
        return redirect(url_for('views.home_ar'))
    else:
        return redirect(url_for('views.home_fr'))

# ----------------- Envoi de l'email de confirmation et autres fonctions ----------------- #
def send_confirmation_email(user_email, confirmation_code):
    locale = str(get_locale())
    subjects = {
        'fr': "Confirmation de compte",
        'en': "Account Confirmation",
        'ar': "تأكيد الحساب"
    }
    plain_texts = {
        'fr': f"Bonjour,\n\nVotre compte a été créé avec succès. Veuillez utiliser le code suivant pour confirmer votre compte : {confirmation_code}\n\nMerci de votre confiance,\nL'équipe Calc-Diff",
        'en': f"Hello,\n\nYour account has been successfully created. Please use the following code to confirm your account: {confirmation_code}\n\nThank you for trusting us,\nThe Calc-Diff Team",
        'ar': f"مرحبًا,\n\nتم إنشاء حسابك بنجاح. الرجاء استخدام الرمز التالي لتأكيد حسابك: {confirmation_code}\n\nشكرًا لثقتك بنا،\nفريق Calc-Diff"
    }
    html_body = render_template('msg.html', code=confirmation_code, lang=locale)
    msg = Message(subject=subjects.get(locale, subjects['fr']),
                  sender='habassetraore36@gmail.com',
                  recipients=[user_email])
    msg.body = plain_texts.get(locale, plain_texts['fr'])
    msg.html = html_body
    try:
        mail.send(msg)
    except Exception as e:
        print(f"Erreur lors de l'envoi de l'e-mail de confirmation : {e}")

def generate_confirmation_code():
    return ''.join(secrets.choice('0123456789') for _ in range(6))

def is_confirmation_code_expired(sent_time, expiry_minutes=10):
    if not sent_time:
        return True
    return datetime.utcnow() > sent_time + timedelta(minutes=expiry_minutes)

@auth.route('/confirm_fr', methods=['GET', 'POST'])
@login_required
def confirm_fr():
    if request.method == 'POST':
        email = current_user.email
        entered_code = request.form['confirmation_code']
        user = Formulaire.query.filter_by(email=email).first()
        if is_confirmation_code_expired(user.confirmation_sent_at):
            flash("Le code de confirmation a expiré. Un nouveau code vous a été envoyé.", "error")
            user.confirmation_code = generate_confirmation_code()
            user.confirmation_sent_at = datetime.utcnow()
            db.session.commit()
            send_confirmation_email(user.email, user.confirmation_code)
            return redirect(url_for('auth.confirm_fr'))
        if user and user.confirmation_code == entered_code:
            user.is_confirmed = True
            db.session.commit()
            flash('Votre compte a été confirmé avec succès.', 'success')
            return redirect(url_for('views.dashboard_fr'))
        else:
            flash('Code de confirmation incorrect.', 'error')
    return render_template("FR/Confirm_fr.html")

@auth.route('/confirm_en', methods=['GET', 'POST'])
@login_required
def confirm_en():
    if request.method == 'POST':
        email = current_user.email
        entered_code = request.form['confirmation_code']
        user = Formulaire.query.filter_by(email=email).first()
        if is_confirmation_code_expired(user.confirmation_sent_at):
            flash("The confirmation code has expired. A new code has been sent to you.", "error")
            user.confirmation_code = generate_confirmation_code()
            user.confirmation_sent_at = datetime.utcnow()
            db.session.commit()
            send_confirmation_email(user.email, user.confirmation_code)
            return redirect(url_for('auth.confirm_en'))
        if user and user.confirmation_code == entered_code:
            user.is_confirmed = True
            db.session.commit()
            flash('Your account has been successfully confirmed.', 'success')
            return redirect(url_for('views.dashboard_en'))
        else:
            flash('Incorrect confirmation code.', 'error')
    return render_template("EN/Confirm_en.html")

@auth.route('/confirm_ar', methods=['GET', 'POST'])
@login_required
def confirm_ar():
    if request.method == 'POST':
        email = current_user.email
        entered_code = request.form['confirmation_code']
        user = Formulaire.query.filter_by(email=email).first()
        if is_confirmation_code_expired(user.confirmation_sent_at):
            flash("انتهت صلاحية رمز التأكيد. تم إرسال رمز جديد إليك.", "error")
            user.confirmation_code = generate_confirmation_code()
            user.confirmation_sent_at = datetime.utcnow()
            db.session.commit()
            send_confirmation_email(user.email, user.confirmation_code)
            return redirect(url_for('auth.confirm_fr'))
        if user and user.confirmation_code == entered_code:
            user.is_confirmed = True
            db.session.commit()
            flash('تم تأكيد حسابك بنجاح.', 'success')
            return redirect(url_for('views.dashboard_ar'))
        else:
            flash('رمز التأكيد غير صحيح.', 'error')
    return render_template("AR/Confirm_ar.html")

#..................Route verify......................#
@auth.route('/verify', methods=['POST'])
@login_required
def verify():
    # Récupérer le code entré dans le formulaire
    entered_code = request.form.get('confirmation_code')
    email = current_user.email
    user = Formulaire.query.filter_by(email=email).first()
    locale = str(get_locale())

    if user and user.confirmation_code == entered_code:
        user.is_confirmed = True
        db.session.commit()

        if locale.startswith('en'):
            flash('Your account has been confirmed successfully.', 'success')
            return redirect(url_for('views.dashboard_en'))
        elif locale.startswith('ar'):
            flash('تم تأكيد حسابك بنجاح.', 'success')
            return redirect(url_for('views.dashboard_ar'))
        else:
            flash('Votre compte a été confirmé avec succès.', 'success')
            return redirect(url_for('views.dashboard_fr'))
    else:
        flash('Code de confirmation incorrect.', 'error')
        if locale.startswith('en'):
            return redirect(url_for('auth.confirm_en'))
        elif locale.startswith('ar'):
            return redirect(url_for('auth.confirm_ar'))
        else:
            return redirect(url_for('auth.confirm_fr'))

#.....................Renvoie de code...................#
@auth.route('/resend_confirmation_<lang>', methods=['GET'])
@login_required
def resend_confirmation(lang):
    user = current_user
    if not user.is_confirmed:
        user.confirmation_code = generate_confirmation_code()
        db.session.commit()
        send_confirmation_email(user.email, user.confirmation_code)
        messages = {
            'fr': "Un nouveau code de confirmation a été envoyé.",
            'en': "A new confirmation code has been sent.",
            'ar': "تم إرسال رمز تأكيد جديد."
        }
        flash(messages.get(lang, messages['fr']), category='info')
    return redirect(url_for(f'auth.confirm_{lang}'))

#........................Limite de Tentatives.................#
def handle_login(user, password_input, lang='fr'):
    now = datetime.utcnow()

    # Blocage temporaire
    if user.lockout_time and now < user.lockout_time:
        wait_minutes = int((user.lockout_time - now).total_seconds() / 60)

        if lang == 'en':
            flash(f"Account temporarily locked. Try again in {wait_minutes} minute(s).", "danger")
        elif lang == 'ar':
            flash(f"تم قفل الحساب مؤقتًا. حاول مرة أخرى خلال {wait_minutes} دقيقة.", "danger")
        else:  # fr
            flash(f"Compte temporairement bloqué. Réessayez dans {wait_minutes} minute(s).", "danger")

        return redirect(url_for(f"auth.login_{lang}"))

    # Vérification du mot de passe
    if check_password_hash(user.password, password_input):
        user.failed_attempts = 0
        user.lockout_time = None
        user.lockout_level = 0
        db.session.commit()
        login_user(user)

        return redirect(url_for(f"views.dashboard_{lang}"))

    # Mot de passe incorrect
    user.failed_attempts += 1
    if user.failed_attempts >= 3:
        user.lockout_level += 1
        lock_durations = [5, 10, 15]  # en minutes
        lock_minutes = lock_durations[min(user.lockout_level - 1, len(lock_durations) - 1)]
        user.lockout_time = now + timedelta(minutes=lock_minutes)
        user.failed_attempts = 0

        if lang == 'en':
            flash(f"Too many attempts. Account locked for {lock_minutes} minutes.", "danger")
        elif lang == 'ar':
            flash(f"عدد كبير من المحاولات. تم قفل الحساب لمدة {lock_minutes} دقيقة.", "danger")
        else:
            flash(f"Trop de tentatives. Compte bloqué {lock_minutes} minutes.", "danger")

    else:
        if lang == 'en':
            flash("Incorrect password. Attempt failed.", "warning")
        elif lang == 'ar':
            flash("كلمة المرور غير صحيحة. المحاولة فشلت.", "warning")
        else:
            flash("Mot de passe incorrect. Tentative échouée.", "warning")

    db.session.commit()
    return redirect(url_for(f"auth.login_{lang}"))

# -------------------- Fonction pour le reset password en français -------------------- #
@auth.route('/reset_password_fr', methods=['GET', 'POST'])
def reset_password_fr():
    if request.method == 'POST':
        email = request.form.get('email')
        user = Formulaire.query.filter_by(email=email).first()
        
        if user:
            # Générer un token de réinitialisation
            s = Serializer(current_app.config['SECRET_KEY'])
            token = s.dumps(user.email, salt='password-reset-salt')
            reset_url = url_for('auth.reset_password_token_fr', token=token, _external=True)

            # Envoi de l'e-mail
            msg = Message(
                "Réinitialisation de votre mot de passe", 
                sender=current_app.config['MAIL_DEFAULT_SENDER'],
                recipients=[user.email]
            )
            msg.body = f"Bonjour,\n\nCliquez sur le lien suivant pour réinitialiser votre mot de passe : {reset_url}\n\nSi vous n'avez rien demandé, ignorez cet email."
            mail.send(msg)

        flash("Si cet email existe, un lien de réinitialisation a été envoyé.", "info")
        return redirect(url_for('auth.reset_password_fr'))
    
    return render_template('FR/Password.html')

# -------------------- Fonction pour le reset password avec token en français -------------------- #
@auth.route('/reset_password_fr/<token>', methods=['GET', 'POST'])
def reset_password_token_fr(token):
    try:
        # Vérification du token et récupération de l'email
        s = Serializer(current_app.config['SECRET_KEY'])
        email = s.loads(token, salt='password-reset-salt', max_age=3600)
    except SignatureExpired:
        flash("Le lien a expiré.", "danger")
        return redirect(url_for('auth.reset_password_fr'))
    except BadSignature:
        flash("Lien invalide.", "danger")
        return redirect(url_for('auth.reset_password_fr'))

    if request.method == 'POST':
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        if password != confirm_password:
            flash("Les mots de passe ne correspondent pas.", "danger")
            return redirect(url_for('auth.reset_password_token_fr', token=token))

        user = Formulaire.query.filter_by(email=email).first()
        if user:
            user.password = generate_password_hash(password)
            db.session.commit()
            flash("Votre mot de passe a été mis à jour.", "success")
            return redirect(url_for('auth.login_fr'))

    return render_template('FR/Reset_password.html', token=token)

# -------------------- Fonction pour le reset password en anglais -------------------- #
@auth.route('/reset_password_en', methods=['GET', 'POST'])
def reset_password_en():
    if request.method == 'POST':
        email = request.form.get('email')
        user = Formulaire.query.filter_by(email=email).first()
        
        if user:
            # Générer un token de réinitialisation
            s = Serializer(current_app.config['SECRET_KEY'])
            token = s.dumps(user.email, salt='password-reset-salt')
            reset_url = url_for('auth.reset_password_token_en', token=token, _external=True)

            # Envoi de l'e-mail
            msg = Message(
                "Password Reset Request", 
                sender=current_app.config['MAIL_DEFAULT_SENDER'],
                recipients=[user.email]
            )
            msg.body = f"Hello,\n\nClick on the following link to reset your password: {reset_url}\n\nIf you did not request this, please ignore this email."
            mail.send(msg)

        flash("If the email exists, a reset link has been sent.", "info")
        return redirect(url_for('auth.reset_password_en'))
    
    return render_template('EN/Password.html')

# -------------------- Fonction pour le reset password avec token en anglais -------------------- #
@auth.route('/reset_password_en/<token>', methods=['GET', 'POST'])
def reset_password_token_en(token):
    try:
        # Vérification du token et récupération de l'email
        s = Serializer(current_app.config['SECRET_KEY'])
        email = s.loads(token, salt='password-reset-salt', max_age=3600)
    except SignatureExpired:
        flash("The link has expired.", "danger")
        return redirect(url_for('auth.reset_password_en'))
    except BadSignature:
        flash("Invalid link.", "danger")
        return redirect(url_for('auth.reset_password_en'))

    if request.method == 'POST':
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        if password != confirm_password:
            flash("Passwords do not match.", "danger")
            return redirect(url_for('auth.reset_password_token_en', token=token))

        user = Formulaire.query.filter_by(email=email).first()
        if user:
            user.password = generate_password_hash(password)
            db.session.commit()
            flash("Your password has been updated.", "success")
            return redirect(url_for('auth.login_en'))

    return render_template('EN/Reset_password.html', token=token)

# -------------------- Fonction pour le reset password en arabe -------------------- #
@auth.route('/reset_password_ar', methods=['GET', 'POST'])
def reset_password_ar():
    if request.method == 'POST':
        email = request.form.get('email')
        user = Formulaire.query.filter_by(email=email).first()
        
        if user:
            # Générer un token de réinitialisation
            s = Serializer(current_app.config['SECRET_KEY'])
            token = s.dumps(user.email, salt='password-reset-salt')
            reset_url = url_for('auth.reset_password_token_ar', token=token, _external=True)

            # Envoi de l'e-mail
            msg = Message(
                "طلب إعادة تعيين كلمة المرور", 
                sender=current_app.config['MAIL_DEFAULT_SENDER'],
                recipients=[user.email]
            )
            msg.body = f"مرحباً،\n\nانقر على الرابط التالي لإعادة تعيين كلمة المرور: {reset_url}\n\nإذا لم تطلب هذا، يرجى تجاهل هذا البريد الإلكتروني."
            mail.send(msg)

        flash("إذا كان هذا البريد الإلكتروني موجودًا، تم إرسال رابط لإعادة تعيين كلمة المرور.", "info")
        return redirect(url_for('auth.reset_password_ar'))
    
    return render_template('AR/Password.html')

# -------------------- Fonction pour le reset password avec token en arabe -------------------- #
@auth.route('/reset_password_ar/<token>', methods=['GET', 'POST'])
def reset_password_token_ar(token):
    try:
        # Vérification du token et récupération de l'email
        s = Serializer(current_app.config['SECRET_KEY'])
        email = s.loads(token, salt='password-reset-salt', max_age=3600)
    except SignatureExpired:
        flash("انتهت صلاحية الرابط.", "danger")
        return redirect(url_for('auth.reset_password_ar'))
    except BadSignature:
        flash("رابط غير صالح.", "danger")
        return redirect(url_for('auth.reset_password_ar'))

    if request.method == 'POST':
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        if password != confirm_password:
            flash("كلمات المرور غير متطابقة.", "danger")
            return redirect(url_for('auth.reset_password_token_ar', token=token))

        user = Formulaire.query.filter_by(email=email).first()
        if user:
            user.password = generate_password_hash(password)
            db.session.commit()
            flash("تم تحديث كلمة المرور الخاصة بك.", "success")
            return redirect(url_for('auth.login_ar'))

    return render_template('AR/Reset_password.html', token=token)