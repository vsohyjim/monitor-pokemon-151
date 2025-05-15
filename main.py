import requests
import time
import os
import threading
from flask import Flask

# Variables d’environnement (injetées par Railway)
USER_TOKEN = os.environ.get("USER_TOKEN")
SOURCE_CHANNEL_ID = os.environ.get("SOURCE_CHANNEL_ID")
WEBHOOK_URL = os.environ.get("WEBHOOK_URL")

last_message_id = None

headers = {
    "Authorization": USER_TOKEN,
    "User-Agent": "Mozilla/5.0",
    "Content-Type": "application/json"
}

def fetch_messages():
    global last_message_id
    while True:
        try:
            url = f"https://discord.com/api/v9/channels/{SOURCE_CHANNEL_ID}/messages?limit=10"
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                messages = response.json()
                messages.reverse()
                for msg in messages:
                    if last_message_id is None or msg["id"] > last_message_id:
                        content = msg["content"].lower()
                        if "151" in content and "fnac" in content:
                            send_to_webhook()
                        last_message_id = msg["id"]
            else:
                print(f"Erreur {response.status_code}: {response.text}")
        except Exception as e:
            print(f"Erreur dans fetch_messages: {e}")
        time.sleep(5)

def send_to_webhook():
    payload = {
        "content": (
            "**Restock Bundle 151 sur le Fnac !**\n"
            "🔗 Lien : https://www.fnac.com/Cartes-a-collectionner-Pokemon-EV3-5-Bundle-de-6-boosters-Ecarlate-et-Violet-151/a17884060/w-4"
        )
    }
    requests.post(WEBHOOK_URL, json=payload)

# ---- Serveur Flask minimal pour Railway + UptimeRobot ----

app = Flask(__name__)

@app.route("/")
def index():
    return "Bot actif ✅", 200

if __name__ == "__main__":
    # Lance le bot dans un thread séparé
    thread = threading.Thread(target=fetch_messages)
    thread.start()

    # Lance le serveur web
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 3000)))
