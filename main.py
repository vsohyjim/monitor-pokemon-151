import requests
import time
import os
import threading
from flask import Flask

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
            url = f"https://discord.com/api/v9/channels/{SOURCE_CHANNEL_ID}/messages?limit=5"
            response = requests.get(url, headers=headers)

            if response.status_code == 200:
                messages = response.json()
                messages.reverse()

                for msg in messages:
                    if last_message_id is None or msg["id"] > last_message_id:
                        send_full_message_to_webhook(msg)
                        last_message_id = msg["id"]
            else:
                print(f"Erreur {response.status_code}: {response.text}")
        except Exception as e:
            print(f"Erreur dans fetch_messages: {e}")
        time.sleep(1)

def send_full_message_to_webhook(msg):
    content = msg.get("content", "")
    author = msg["author"]["username"]
    avatar_url = msg["author"]["avatar"]
    user_id = msg["author"]["id"]

    avatar = f"https://cdn.discordapp.com/avatars/{user_id}/{avatar_url}.png" if avatar_url else None

    payload = {
        "username": author,
        "avatar_url": avatar,
        "content": content,
    }

    # Gérer les embeds (comme liens Amazon/Dealabs)
    embeds = msg.get("embeds", [])
    if embeds:
        payload["embeds"] = embeds

    # Gérer les fichiers joints
    attachments = msg.get("attachments", [])
    for att in attachments:
        payload["content"] += f"\n📎 {att['url']}"

    requests.post(WEBHOOK_URL, json=payload)

# Serveur pour Railway
app = Flask(__name__)

@app.route("/")
def index():
    return "Bot actif ✅", 200

if __name__ == "__main__":
    thread = threading.Thread(target=fetch_messages)
    thread.start()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 3000)))
