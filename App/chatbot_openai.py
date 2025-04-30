# website/chatbot_openai.py

import os
from dotenv import load_dotenv
from flask import Blueprint, request, jsonify
from openai import OpenAI, OpenAIError

# Charger les variables d'environnement
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise RuntimeError(
        "La variable d'environnement OPENAI_API_KEY n'est pas définie."
    )

client = OpenAI(api_key=api_key)
chatbot_bp = Blueprint('chatbot', __name__)

# Dictionnaire de prompts système enrichis
system_prompts = {
    "fr": (
        "Tu es l’assistant officiel de CALC-DIFF, une application web dédiée au calcul du "
        "coefficient de diffusion à l’aide de la méthode UNIFAC. Tu aides les utilisateurs à comprendre : "
        "le formulaire de calcul, les champs à remplir (température, pression, solvant, groupes fonctionnels), "
        "le modèle UNIFAC, les résultats (coefficients, facteurs d’activité), et le fonctionnement général. "
        "Tu es aussi capable d’expliquer l’authentification, les langues disponibles (FR, EN, AR), "
        "le tableau de bord, l'enregistrement et la consultation des résultats, le téléchargement PDF et l’usage du chatbot. "
        "Sois toujours clair, utile, et convivial."
    ),
    "en": (
        "You are the official assistant of CALC-DIFF, a web app for calculating diffusion coefficients using the UNIFAC method. "
        "You help users with form input (temperature, pressure, solvent, functional groups), the theory of UNIFAC, interpreting results "
        "(coefficients, activity factors), and how to use the app in general. You also explain login/signup, language switching (FR, EN, AR), "
        "dashboard usage, saving results, PDF export, and how the chatbot works. Always be clear, helpful, and friendly."
    ),
    "ar": (
        "أنت المساعد الرسمي لتطبيق CALC-DIFF لحساب معامل الانتشار باستخدام طريقة UNIFAC. "
        "تساعد المستخدمين في إدخال البيانات (درجة الحرارة، الضغط، المذيب، المجموعات الوظيفية)، شرح طريقة UNIFAC، "
        "فهم النتائج (المعاملات، عوامل النشاط)، وطريقة استخدام التطبيق بشكل عام. "
        "توضح أيضًا تسجيل الدخول والتسجيل، تغيير اللغة (FR، EN، AR)، استخدام لوحة التحكم، حفظ النتائج، تحميلها كملف PDF، "
        "واستخدام الشات بوت. كن دائمًا واضحًا، مفيدًا وودودًا."
    )
}

def ask_openai(message, lang="fr"):
    system_prompt = system_prompts.get(lang, system_prompts["fr"])
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": message}
            ],
            max_tokens=400,
            temperature=0.7
        )
        return response.choices[0].message.content.strip()
    except OpenAIError as e:
        return f"Une erreur OpenAI est survenue : {e}"
    except Exception as e:
        return f"Une erreur est survenue : {e}"

@chatbot_bp.route('/chatbot', methods=['POST'])
def chatbot_route():
    data = request.get_json() or {}
    message = data.get("message", "")
    lang = data.get("lang", "fr")
    if not message:
        return jsonify({'error': 'Aucun message reçu'}), 400

    reply = ask_openai(message, lang)
    return jsonify({'response': reply})
