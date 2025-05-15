import discord
import asyncio
import os
import threading
from flask import Flask

# === CONFIG ===
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")  # ✅ sécurisé
SOURCE_CHANNEL_ID = int(os.getenv("SOURCE_CHANNEL_ID"))
ALERT_CHANNEL_ID = int(os.getenv("ALERT_CHANNEL_ID"))
KEYWORDS = ["fnac", "151"]
CHECK_INTERVAL = 5  # secondes

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)
seen_message_ids = set()

async def check_messages():
    await client.wait_until_ready()
    print("🎯 Bot connecté et en surveillance")
    while not client.is_closed():
        try:
            source_channel = client.get_channel(SOURCE_CHANNEL_ID)
            alert_channel = client.get_channel(ALERT_CHANNEL_ID)
            if source_channel and alert_channel:
                messages = await source_channel.history(limit=10).flatten()
                for msg in messages:
                    if msg.id not in seen_message_ids:
                        content_lower = msg.content.lower()
                        if all(k in content_lower for k in KEYWORDS):
                            await alert_channel.send("Pokemon 151 Bundle Restock ! 🔥")
                            print(f"✅ Message détecté : {msg.content}")
                        seen_message_ids.add(msg.id)
            else:
                print("⚠️ Channels introuvables")
        except Exception as e:
            print(f"[ERREUR] {e}")
        await asyncio.sleep(CHECK_INTERVAL)

# === FLASK KEEP-ALIVE ===
app = Flask(__name__)

@app.route("/")
def index():
    return "🟢 Bot Discord 151 actif"

def run_flask():
    app.run(host="0.0.0.0", port=8080)

# === LANCEMENT MULTITHREAD ===
threading.Thread(target=run_flask).start()

@client.event
async def on_ready():
    print(f"🔗 Connecté en tant que {client.user}")
    client.loop.create_task(check_messages())

client.run(DISCORD_TOKEN)
