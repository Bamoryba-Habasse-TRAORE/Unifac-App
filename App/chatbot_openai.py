# website/chatbot_openai.py
import os
import openai
from dotenv import load_dotenv

load_dotenv()  
openai.api_key = os.getenv("OPENAI_API_KEY")  # Ajoute ta clé dans les variables d’environnement

def ask_openai(message, lang="fr"):
    prompt = {
        "fr": f"Tu es l'assistant officiel de l'application web CALC-DIFF. Réponds de manière claire, précise et conviviale. Question : {message}",
        "en": f"You are the official assistant of the CALC-DIFF web application. Answer clearly, precisely, and helpfully. Question: {message}",
        "ar": f"أنت المساعد الرسمي لتطبيق الويب CALC-DIFF. أجب بطريقة واضحة ومفيدة وودية. السؤال: {message}"
    }.get(lang, message)

    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",  # Ou gpt-4 si tu y as accès
            messages=[{"role": "user", "content": prompt}],
            max_tokens=400,
            temperature=0.7
        )
        return response.choices[0].message["content"].strip()
    except Exception as e:
        return f"Une erreur est survenue : {str(e)}"
