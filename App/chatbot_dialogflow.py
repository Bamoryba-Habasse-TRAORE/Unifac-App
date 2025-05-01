import os
import uuid
from google.cloud import dialogflow_v2 as dialogflow
from dotenv import load_dotenv
from flask import Blueprint, request, jsonify, current_app
import traceback

load_dotenv()

dialogflow_bp = Blueprint('dialogflow', __name__)
PROJECT_ID = os.getenv("DIALOGFLOW_PROJECT_ID")
credentials_json = os.getenv("GOOGLE_APPLICATION_CREDENTIALS_JSON")
# Mapping des langues supportées
LANG_MAP = {"fr": "fr-FR", "en": "en-US", "ar": "ar-X"}  # Remplace "ar-X" par le bon code Dialogflow si nécessaire

def detect_intent_texts(session_id, text, language_code="fr-FR"):
    try:
        session_client = dialogflow.SessionsClient()
        session = session_client.session_path(PROJECT_ID, session_id)

        text_input = dialogflow.TextInput(text=text, language_code=language_code)
        query_input = dialogflow.QueryInput(text=text_input)

        response = session_client.detect_intent(request={
            "session": session,
            "query_input": query_input
        })
        return response.query_result.fulfillment_text

    except Exception as e:
        current_app.logger.error(f"Erreur Dialogflow: {e}")
        raise

@dialogflow_bp.route("/chatbot", methods=["POST"])
def chatbot():
    try:
        data = request.get_json()
        message = data.get("message")
        lang = data.get("lang", "fr").lower()

        if not message:
            return jsonify({"error": "Message manquant"}), 400

        language_code = LANG_MAP.get(lang, "fr-FR")
        session_id = str(uuid.uuid4())

        response_text = detect_intent_texts(session_id, message, language_code)
        if not response_text.strip():
            response_text = "Je n'ai pas compris. Peux-tu reformuler ?"

        return jsonify({"response": response_text}), 200

    except Exception as e:
        current_app.logger.error(f"Erreur dans /chatbot: {e}")
        current_app.logger.error(traceback.format_exc())
        return jsonify({"error": "Erreur serveur"}), 500
