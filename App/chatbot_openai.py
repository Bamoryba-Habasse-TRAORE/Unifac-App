# website/chatbot_openai.py

import os
from dotenv import load_dotenv
from flask import Blueprint, request, jsonify
from openai import OpenAI, OpenAIError

# 1. Charger les variables d'environnement AU PLUS TOT
load_dotenv()

# 2. Récupération de la clé
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise RuntimeError(
        "La variable d'environnement OPENAI_API_KEY n'est pas définie. "
        "Veuillez l'ajouter à votre .env ou à votre configuration d'environnement."
    )

# 3. Instanciation du client
client = OpenAI(api_key=api_key)

# Définir un blueprint pour le chatbot
chatbot_bp = Blueprint('chatbot', __name__)

def ask_openai(message, lang="fr"):
    prompt = {
        "fr": f"Tu es l'assistant officiel de l'application web CALC-DIFF. Réponds de manière claire, précise et conviviale. Question : {message}",
        "en": f"You are the official assistant of the CALC-DIFF web application. Answer clearly, precisely, and helpfully. Question: {message}",
        "ar": f"أنت المساعد الرسمي لتطبيق الويب CALC-DIFF. أجب بطريقة واضحة ومفيدة وودية. السؤال: {message}"
    }.get(lang, message)

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=400,
            temperature=0.7
        )
        return response.choices[0].message.content.strip()
    except OpenAIError as e:
        # Erreur liée à l'API OpenAI
        return f"Une erreur OpenAI est survenue : {e}"
    except Exception as e:
        # Toute autre erreur
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
