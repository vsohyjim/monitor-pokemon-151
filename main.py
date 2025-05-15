import os
import discord
import asyncio
from flask import Flask

TOKEN = os.getenv("TOKEN")
GUILD_ID = int(os.getenv("GUILD_ID"))
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))
ALERT_CHANNEL_ID = int(os.getenv("ALERT"))

message_count = 0

class MyClient(discord.Client):
    async def on_ready(self):
        print(f'Connecté en tant que {self.user}')
        
    async def on_message(self, message):
        global message_count
        if message.channel.id == CHANNEL_ID:
            message_count += 1
            if "FNAC" in message.content and message_count == 151:
                alert_channel = self.get_channel(ALERT_CHANNEL_ID)
                await alert_channel.send("OK ! Mention détectée au 151e message.")

# Initialisation du bot Discord
intents = discord.Intents.default()
intents.messages = True
client = MyClient(intents=intents)

# Serveur Flask minimal pour Railway
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot Discord actif!"

async def run_discord_bot():
    await client.start(TOKEN)

def run_flask():
    app.run(host="0.0.0.0", port=8080)

# Exécution parallèle
if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.create_task(run_discord_bot())
    loop.run_until_complete(asyncio.sleep(1))
    run_flask()
