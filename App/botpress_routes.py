from flask import Blueprint, request, jsonify
import requests

bp_botpress = Blueprint('bp_botpress', __name__)

# Remplace par tes informations Botpress
BOT_ID = '7457a843-cc64-4320-92af-ae4379be8000'
WORKSPACE_ID = 'wkspace_01JTEN44EEZD4X2WD7069V1DDP'
BP_API_URL = f"https://api.botpress.cloud/v1/chat/{BOT_ID}/webchat"
BP_TOKEN = "YOUR_PAT_HERE"  # Ton Personal Access Token

@bp_botpress.route('/botpress/message', methods=['POST'])
def send_message_to_bot():
    user_message = request.json.get("message")
    user_id = request.json.get("userId", "anonymous")

    payload = {
        "text": user_message,
        "userId": user_id,
    }

    headers = {
        "Authorization": f"Bearer {BP_TOKEN}",
        "Content-Type": "application/json"
    }

    try:
        res = requests.post(f"{BP_API_URL}/send", json=payload, headers=headers)
        return jsonify(res.json())
    except Exception as e:
        return jsonify({"error": str(e)}), 500
