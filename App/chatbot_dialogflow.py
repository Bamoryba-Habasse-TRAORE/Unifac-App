import os
import uuid
import json
import tempfile
from google.cloud import dialogflow_v2 as dialogflow
from google.oauth2 import service_account
from dotenv import load_dotenv
from flask import Blueprint, request, jsonify, current_app
import traceback

load_dotenv()

dialogflow_bp = Blueprint('dialogflow', __name__)
PROJECT_ID = os.getenv("DIALOGFLOW_PROJECT_ID")
raw_credentials = os.getenv("GOOGLE_APPLICATION_CREDENTIALS_JSON", "")
# Mapping des langues supportées
LANG_MAP = {"fr": "fr-FR", "en": "en-US", "ar": "ar-X"}

def detect_intent_texts(session_id, text, language_code="fr-FR"):
    # Vérification basique
    if not raw_credentials:
        raise ValueError("La variable GOOGLE_APPLICATION_CREDENTIALS_JSON est vide ou non définie.")

    try:
        creds_dict = json.loads(raw_credentials)
    except json.JSONDecodeError as e:
        current_app.logger.error(f"Format JSON invalide pour GOOGLE_APPLICATION_CREDENTIALS_JSON : {e}")
        raise

    try:
                # Write the raw JSON credentials to a temp file so that pem newlines are preserved
        fd, credentials_path = tempfile.mkstemp(suffix=".json")
        with os.fdopen(fd, 'w') as tmp:
            tmp.write(raw_credentials)
        credentials = service_account.Credentials.from_service_account_file(credentials_path)
        os.remove(credentials_path)
    except Exception as e:
        current_app.logger.error(f"Impossible de charger la clé privée : {e}")
        raise

    session_client = dialogflow.SessionsClient(credentials=credentials)
    session = session_client.session_path(PROJECT_ID, session_id)

    text_input = dialogflow.TextInput(text=text, language_code=language_code)
    query_input = dialogflow.QueryInput(text=text_input)
    response = session_client.detect_intent(request={
        "session": session,
        "query_input": query_input
    })
    return response.query_result.fulfillment_text

@dialogflow_bp.route("/chatbot", methods=["POST"])
def chatbot():
    try:
        data = request.get_json() or {}
        message = data.get("message", "").strip()
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
