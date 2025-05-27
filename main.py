import os
import requests
import discord
import asyncio
from discord.ext import commands

# === CONFIGURATION VIA ENVIRONNEMENT ===
BOT_TOKEN = os.environ.get("BOT_TOKEN")  # Ton bot officiel
USER_TOKEN = os.environ.get("USER_TOKEN")  # Ton token utilisateur (lecture uniquement)
SOURCE_CHANNEL_IDS = os.environ.get("SOURCE_CHANNEL_IDS").split(",")  # IDs à écouter
TARGET_CHANNEL_ID = int(os.environ.get("TARGET_CHANNEL_ID"))  # ID où ton bot envoie
BLOCKED_KEYWORDS = [kw.strip().lower() for kw in os.environ.get("BLOCKED_KEYWORDS", "").split(",")]

# === SETUP ===
last_message_ids = {channel_id: None for channel_id in SOURCE_CHANNEL_IDS}
headers = {
    "Authorization": USER_TOKEN,
    "User-Agent": "Mozilla/5.0",
    "Content-Type": "application/json"
}

intents = discord.Intents.default()
intents.messages = True
intents.guilds = True
bot = commands.Bot(command_prefix="!", intents=intents)


# === FILTRE MESSAGES BLOQUÉS ===
def is_blocked(msg):
    content = msg.get("content", "").lower()

    for keyword in BLOCKED_KEYWORDS:
        if keyword in content:
            print(f"🔕 Bloqué dans content : {keyword}")
            return True

    for embed in msg.get("embeds", []):
        fields_to_check = [
            embed.get("title", ""),
            embed.get("description", ""),
            embed.get("footer", {}).get("text", "")
        ]
        if "fields" in embed:
            fields_to_check += [f.get("name", "") + " " + f.get("value", "") for f in embed["fields"]]

        for field in fields_to_check:
            field_lower = field.lower()
            for keyword in BLOCKED_KEYWORDS:
                if keyword in field_lower:
                    print(f"🔕 Bloqué dans embed : {keyword}")
                    return True

    return False


# === TRANSFERT DU MESSAGE AVEC COULEUR ===
async def forward_to_discord_bot(msg, channel):
    embed_color = discord.Color(int("9c73cb", 16))  # Couleur violette #9c73cb

    embed = discord.Embed(
        description=msg.get("content", "") or "*Aucun contenu textuel*",
        color=embed_color
    )

    embeds = msg.get("embeds", [])
    if embeds:
        first = embeds[0]
        if first.get("title"):
            embed.title = first["title"]
        if first.get("description"):
            embed.description += f"\n\n{first['description']}"
        if first.get("url"):
            embed.url = first["url"]
        if first.get("thumbnail", {}).get("url"):
            embed.set_thumbnail(url=first["thumbnail"]["url"])
        if first.get("image", {}).get("url"):
            embed.set_image(url=first["image"]["url"])

    attachments = msg.get("attachments", [])
    for att in attachments:
        embed.add_field(name="📎 Fichier", value=att["url"], inline=False)

    await channel.send(embed=embed)


# === LECTURE DES MESSAGES (via USER_TOKEN) ===
async def fetch_messages():
    await bot.wait_until_ready()
    print(f"✅ Connecté en tant que {bot.user}")

    while True:
        for source_id in SOURCE_CHANNEL_IDS:
            try:
                url = f"https://discord.com/api/v9/channels/{source_id}/messages?limit=5"
                response = requests.get(url, headers=headers)

                if response.status_code != 200:
                    print(f"[{source_id}] ❌ Erreur API : {response.status_code}")
                    continue

                messages = response.json()
                messages.reverse()

                for msg in messages:
                    if last_message_ids[source_id] is None or msg["id"] > last_message_ids[source_id]:
                        if not is_blocked(msg):
                            target_channel = bot.get_channel(TARGET_CHANNEL_ID)
                            if target_channel:
                                await forward_to_discord_bot(msg, target_channel)
                            else:
                                print("❌ Channel destination introuvable.")
                        else:
                            print(f"[{source_id}] 🔕 Message ignoré.")
                        last_message_ids[source_id] = msg["id"]
            except Exception as e:
                print(f"[{source_id}] ⚠️ Erreur dans fetch_messages: {e}")
        await asyncio.sleep(1)


@bot.event
async def on_ready():
    bot.loop.create_task(fetch_messages())


# === LANCEMENT DU BOT ===
if __name__ == "__main__":
    bot.run(BOT_TOKEN)
