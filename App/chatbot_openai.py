# website/chatbot_openai.py
import os
import openai
from dotenv import load_dotenv
from flask import Blueprint, request, jsonify

# Charger les variables d'environnement
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

# Définir un blueprint pour le chatbot
chatbot_bp = Blueprint('chatbot', __name__)

def ask_openai(message, lang="fr"):
    prompt = {
        "fr": f"Tu es l'assistant officiel de l'application web CALC-DIFF. Réponds de manière claire, précise et conviviale. Question : {message}",
        "en": f"You are the official assistant of the CALC-DIFF web application. Answer clearly, precisely, and helpfully. Question: {message}",
        "ar": f"أنت المساعد الرسمي لتطبيق الويب CALC-DIFF. أجب بطريقة واضحة ومفيدة وودية. السؤال: {message}"
    }.get(lang, message)

    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=400,
            temperature=0.7
        )
        return response.choices[0].message["content"].strip()
    except Exception as e:
        return f"Une erreur est survenue : {str(e)}"

@chatbot_bp.route('/chatbot', methods=['POST'])
def chatbot_route():
    data = request.get_json() or {}
    message = data.get("message", "")
    lang = data.get("lang", "fr")
    if not message:
        return jsonify({'error': 'Aucun message reçu'}), 400

    reply = ask_openai(message, lang)
    return jsonify({'response': reply})
