import os
import uuid
from flask import Blueprint, request, jsonify, current_app, render_template
from chatterbot import ChatBot
from chatterbot.trainers import ListTrainer, ChatterBotCorpusTrainer
import traceback

# Blueprint Flask pour le bot
chatbot_bp = Blueprint('chatbot', __name__, url_prefix='/dialogflow')

# Instanciation du ChatBot avec stockage SQLite
bot = ChatBot(
    'CalcBot',
    storage_adapter='chatterbot.storage.SQLStorageAdapter',
    database_uri='sqlite:///calcbot.sqlite3',
    logic_adapters=['chatterbot.logic.BestMatch'],
    preprocessors=['chatterbot.preprocessors.clean_whitespace']
)

# Entraînement du bot via ListTrainer pour paires spécifiques à CALC-DIFF
trainer = ListTrainer(bot)
trainer.train([
    # Français
    "Bonjour", "Salut ! Comment puis-je t'aider aujourd'hui ?",
    "Comment calculer UNIFAC ?", "Tu peux utiliser le formulaire sur le Dashboard pour calculer le coefficient de diffusion avec la méthode UNIFAC.",
    "Où trouver l'historique des calculs ?", "Clique sur l'onglet Historique dans la barre latérale pour accéder à l'historique.",
    "Comment changer la langue en anglais ?", "Utilise le menu Langues et sélectionne Anglais pour basculer l'interface en English.",
    "Je reçois une erreur", "Peux-tu préciser le message d'erreur ? Je t'aiderai à le résoudre.",
    
    # English
    "Hello", "Hi! How can I assist you today?",
    "How to calculate using UNIFAC?", "Use the form on the Dashboard to compute the diffusion coefficient via the UNIFAC method.",
    "Where is my calculation history?", "Click on the History tab in the sidebar to view your past calculations.",
    "How do I switch to French?", "Open the Languages menu and choose Français to switch the interface to French.",
    "I get an error", "Could you provide the exact error message? I'll help you troubleshoot.",
    
    # العربية
    "مرحبا", "أهلاً! كيف يمكنني مساعدتك اليوم؟",
    "كيف أحسب باستخدام UNIFAC؟", "استخدم النموذج في لوحة التحكم لحساب معامل الانتشار باستخدام طريقة UNIFAC.",
    "أين أجد سجل الحسابات؟", "انقر على تبويب السجل في الشريط الجانبي لعرض حساباتك السابقة.",
    "كيف أغير اللغة إلى الإنجليزية؟", "افتح قائمة اللغات واختر English لتغيير الواجهة إلى اللغة الإنجليزية.",
    "تلقيت خطأ", "هل يمكنك تزويدي برسالة الخطأ المحددة؟ سأساعدك في حلها."
])

# Entraînement sur corpus prédéfinis pour anglais
corpus_trainer = ChatterBotCorpusTrainer(bot)
corpus_trainer.train(
    'chatterbot.corpus.english.greetings',
    'chatterbot.corpus.english.conversations',
    'chatterbot.corpus.english.ai',
    'chatterbot.corpus.english.botprofile'
)

# Route d'affichage du chat intégré (optionnel)
@chatbot_bp.route('/chat', methods=['GET'])
def chat_ui():
    # On utilise la même variable 'lang' qu'ailleurs dans l'app
    lang = request.args.get('lang', 'fr')
    return render_template('chat.html', lang=lang)

# API de discussion adaptée à la route front-end existante
@chatbot_bp.route('/chatbot', methods=['POST'])
def chat_api():
    try:
        data = request.get_json() or {}
        msg = data.get('message', '').strip()
        lang = data.get('lang', 'fr').lower()

        if not msg:
            return jsonify({'error': 'Message manquant'}), 400

        # Réponse du bot, peut être enrichie selon lang si besoin
        response = bot.get_response(msg)
        return jsonify({'response': str(response)}), 200

    except Exception as e:
        current_app.logger.error(f"Erreur dans /dialogflow/chatbot: {e}")
        current_app.logger.error(traceback.format_exc())
        return jsonify({'error': 'Erreur serveur'}), 500
