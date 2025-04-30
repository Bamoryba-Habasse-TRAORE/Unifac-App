import os
from dotenv import load_dotenv
from flask import Blueprint, request, jsonify
from openai import OpenAI, OpenAIError

# Charger les variables d'environnement
load_dotenv()

# Récupération de la clé API
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise RuntimeError(
        "La variable d'environnement OPENAI_API_KEY n'est pas définie. "
        "Veuillez l'ajouter à votre .env ou à votre configuration d'environnement."
    )

# Instanciation du client OpenAI (v1.x)
client = OpenAI(api_key=api_key)

# Définition du blueprint pour le chatbot
chatbot_bp = Blueprint('chatbot', __name__)


def ask_openai(message, lang="fr"):
    # Sélection du prompt selon la langue
    prompt = {
        "fr": f"Tu es l'assistant officiel de l'application web CALC-DIFF. Réponds de manière claire, précise et conviviale. Question : {message}",
        "en": f"You are the official assistant of the CALC-DIFF web application. Answer clearly, precisely, and helpfully. Question: {message}",
        "ar": f"أنت المساعد الرسمي لتطبيق الويب CALC-DIFF. أجب بطريقة واضحة ومفيدة وودية. السؤال: {message}"
    }.get(lang, message)

    try:
        # Réduire max_tokens pour économiser le quota
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=200,
            temperature=0.7
        )
        return response.choices[0].message.content.strip()

    except OpenAIError as e:
        # Gestion spécifique de l'erreur de quota
        if getattr(e, 'status_code', None) == 429:
            return (
                "Le quota OpenAI est épuisé. "
                "Veuillez vérifier votre plan et vos détails de facturation sur platform.openai.com."
            )
        return f"Une erreur OpenAI est survenue : {e}"

    except Exception as e:
        return f"Une erreur inattendue est survenue : {e}"


@chatbot_bp.route('/chatbot', methods=['POST'])
def chatbot_route():
    data = request.get_json() or {}
    message = data.get("message", "")
    lang = data.get("lang", "fr")

    if not message:
        return jsonify({'error': 'Aucun message reçu'}), 400

    reply = ask_openai(message, lang)
    return jsonify({'response': reply})
