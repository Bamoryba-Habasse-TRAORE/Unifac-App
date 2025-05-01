import os
import uuid
from google.cloud import dialogflow_v2 as dialogflow
from dotenv import load_dotenv
from flask import Blueprint, request, jsonify, current_app
import traceback
load_dotenv()

dialogflow_bp = Blueprint('dialogflow', __name__)
PROJECT_ID = os.getenv("DIALOGFLOW_PROJECT_ID")

# Map pour standardiser les codes de langue
LANG_MAP = {"fr": "fr-FR", "en": "en-US", "ar": "ar-X"}

def detect_intent_texts(session_id, text, language_code="fr-FR"):
    session_client = dialogflow.SessionsClient()
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
        data = request.get_json()
        message = data.get("message")
        # ton code de traitement ici (appel Dialogflow, etc.)
        return jsonify({"response": "Réponse temporaire"}), 200
    except Exception as e:
        current_app.logger.error(f"Erreur dans /chatbot: {e}")
        current_app.logger.error(traceback.format_exc())
        return jsonify({"error": "Erreur serveur"}), 500