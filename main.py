import os
import requests
import discord
import asyncio
from discord.ext import commands
from datetime import datetime

# === CONFIGURATION ===
BOT_TOKEN = os.environ.get("BOT_TOKEN")
USER_TOKEN = os.environ.get("USER_TOKEN")
SOURCE_CHANNEL_IDS = os.environ.get("SOURCE_CHANNEL_IDS").split(",")
TARGET_CHANNEL_ID = int(os.environ.get("TARGET_CHANNEL_ID"))
BLOCKED_KEYWORDS = [kw.strip().lower() for kw in os.environ.get("BLOCKED_KEYWORDS", "").split(",")]

last_message_ids = {channel_id: None for channel_id in SOURCE_CHANNEL_IDS}

headers = {
    "Authorization": USER_TOKEN,
    "User-Agent": "Mozilla/5.0",
    "Content-Type": "application/json"
}

# === DISCORD BOT SETUP ===
intents = discord.Intents.default()
intents.messages = True
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents)


# === FILTRE MOTS INTERDITS ===
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


# === TRANSFERT DU MESSAGE AVEC REBRANDING ===
async def forward_to_discord_bot(msg, channel):
    now = datetime.now().strftime("%H:%M")
    guild_icon = channel.guild.icon.url if channel.guild.icon else None
    embed_color = discord.Color(int("9c73cb", 16))  # violet

    for original in msg.get("embeds", []):
        embed = discord.Embed(
            title=original.get("title", discord.Embed.Empty),
            description=original.get("description", discord.Embed.Empty),
            url=original.get("url", discord.Embed.Empty),
            color=embed_color
        )

        # Champs personnalisés
        if "fields" in original:
            for field in original["fields"]:
                embed.add_field(
                    name=field.get("name", "—"),
                    value=field.get("value", "—"),
                    inline=field.get("inline", True)
                )

        # Images
        if original.get("image", {}).get("url"):
            embed.set_image(url=original["image"]["url"])
        if original.get("thumbnail", {}).get("url"):
            embed.set_thumbnail(url=original["thumbnail"]["url"])

        # Footer rebrandé
        embed.set_footer(
            text=f"YVORA • {now}",
            icon_url=guild_icon
        )

        await channel.send(embed=embed)

    # Texte brut (hors embed)
    if msg.get("content"):
        await channel.send(msg["content"])

    # Fichiers joints
    for att in msg.get("attachments", []):
        await channel.send(f"📎 {att['url']}")


# === SCRAP DES MESSAGES VIA TOKEN UTILISATEUR ===
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
                            print(f"[{source_id}] 🔕 Message bloqué.")
                        last_message_ids[source_id] = msg["id"]
            except Exception as e:
                print(f"[{source_id}] ⚠️ Erreur dans fetch_messages: {e}")
        await asyncio.sleep(1)


@bot.event
async def on_ready():
    bot.loop.create_task(fetch_messages())


# === DÉMARRAGE DU BOT ===
if __name__ == "__main__":
    bot.run(BOT_TOKEN)
