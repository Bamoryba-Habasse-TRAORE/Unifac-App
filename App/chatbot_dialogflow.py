import os
import uuid
from flask import Blueprint, request, jsonify
from google.cloud import dialogflow_v2 as dialogflow
from dotenv import load_dotenv

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

@dialogflow_bp.route('/chatbot', methods=['POST'])
def chatbot_route():
    data = request.get_json() or {}
    message = data.get("message", "").strip()
    raw_lang = data.get("lang", "fr")
    # Conversion en format Dialogflow
    language_code = LANG_MAP.get(raw_lang, raw_lang)
    # Session ID unique
    session_id = data.get("session_id") or str(uuid.uuid4())

    if not message:
        return jsonify({"error": "Aucun message reçu"}), 400

    try:
        response_text = detect_intent_texts(session_id, message, language_code=language_code)
        return jsonify({
            "response": response_text,
            "session_id": session_id
        })
    except Exception as e:
        return jsonify({"error": f"Dialogflow error: {e}"}), 500
