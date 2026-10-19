import discord
from discord import app_commands
import os
import logging
import sys
from collections import deque
import asyncio
import time

# --- LOG MEMORY BUFFER --- #
# Stores the last 20 log entries in memory
LOG_BUFFER = deque(maxlen=20)

class BufferLogHandler(logging.Handler):
    def emit(self, record):
        log_entry = self.format(record)
        LOG_BUFFER.append(log_entry)

# --- RAILWAY STREAM LOGGING CONFIGURATION --- #
log_formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s', datefmt='%H:%M:%S')

# Stream to Railway Console
stdout_handler = logging.StreamHandler(sys.stdout)
stdout_handler.setFormatter(log_formatter)

# Stream to Memory Buffer
buffer_handler = BufferLogHandler()
buffer_handler.setFormatter(log_formatter)

logger = logging.getLogger('discord_bot')
logger.setLevel(logging.INFO)
logger.addHandler(stdout_handler)
logger.addHandler(buffer_handler)


class MyClient(discord.Client):
    def __init__(self):
        super().__init__(intents=discord.Intents.default())
        self.tree = app_commands.CommandTree(self)
        self.MY_USER_ID = 1240560087681073205
        self.is_locked = False

    async def setup_hook(self):
        logger.info("Syncing slash commands...")
        await self.tree.sync()
        logger.info("✅ Slash commands successfully synced globally!")

    async def on_ready(self):
        logger.info(f"Logged in as {self.user}!")


client = MyClient()

# --- OWNER LOGS MANAGEMENT COMMANDS --- #

@client.tree.command(name="checklogs", description="View the latest bot activity logs (Owner only)")
async def checklogs(interaction: discord.Interaction):
    if interaction.user.id != client.MY_USER_ID:
        logger.warning(f"Unauthorized /checklogs access attempt by {interaction.user} ({interaction.user.id})")
        await interaction.response.send_message("❌ You are not the owner of this app!", ephemeral=True)
        return

    if not LOG_BUFFER:
        await interaction.response.send_message("ℹ️ Log buffer is currently empty.", ephemeral=True)
        return

    logs_joined = "\n".join(LOG_BUFFER)
    log_payload = f"```text\n{logs_joined}\n```"
    
    if len(log_payload) > 2000:
        log_payload = f"```text\n...[Truncated]...\n{logs_joined[-1800:]}\n```"
        
    await interaction.response.send_message(f"📋 **Recent Bot Logs ({len(LOG_BUFFER)} entries):**\n{log_payload}", ephemeral=True)


@client.tree.command(name="clearlogs", description="Completely wipe the stored memory log history (Owner only)")
async def clearlogs(interaction: discord.Interaction):
    if interaction.user.id != client.MY_USER_ID:
        logger.warning(f"Unauthorized /clearlogs attempt by {interaction.user} ({interaction.user.id})")
        await interaction.response.send_message("❌ You are not the owner of this app!", ephemeral=True)
        return

    LOG_BUFFER.clear()
    logger.info(f"🧹 Internal memory log buffer cleared by owner ({interaction.user}).")
    await interaction.response.send_message("🧹 **Log history wiped successfully!** Future activities will populate fresh.", ephemeral=True)


# --- GENERAL BOT COMMANDS --- #

@client.tree.command(name="lockapp", description="Toggle the app lock state (Owner only)")
async def lockapp(interaction: discord.Interaction):
    logger.info(f"User {interaction.user} ({interaction.user.id}) attempted to use /lockapp")
    if interaction.user.id != client.MY_USER_ID:
        logger.warning(f"Unauthorized /lockapp attempt by {interaction.user}")
        await interaction.response.send_message("❌ You are not the owner of this app!", ephemeral=True)
        return

    client.is_locked = not client.is_locked
    status = "🔒 LOCKED" if client.is_locked else "🔓 UNLOCKED"
    logger.info(f"App lock status changed to: {status} by owner.")
    await interaction.response.send_message(f"App status updated: {status}", ephemeral=True)


@client.tree.command(name="spam", description="Spam messages within Discord user limits")
@app_commands.describe(amount="How much (Max 50)", message="The text to spam")
async def spam(interaction: discord.Interaction, amount: int, message: str):
    logger.info(f"User {interaction.user} ({interaction.user.id}) called /spam | Amount: {amount} | Msg: '{message}'")
    
    if client.is_locked and interaction.user.id != client.MY_USER_ID:
        logger.warning(f"/spam blocked: App is locked. Triggered by {interaction.user}")
        await interaction.response.send_message("❌ This app is currently locked by its creator!", ephemeral=True)
        return

    if amount > 50:
        logger.warning(f"/spam rejected: Amount {amount} exceeds max rule of 50.")
        await interaction.response.send_message("❌ Keep it under 50! GREEDY BOY", ephemeral=True)
        return

    spam_block = f"{message}\n" * amount
    if len(spam_block) > 2000:
        logger.warning(f"/spam rejected: Payload total length ({len(spam_block)} chars) exceeds Discord limit.")
        await interaction.response.send_message("❌ Total characters exceed Discord's 2000 limit!", ephemeral=True)
        return

    await interaction.response.send_message("Ok bro", ephemeral=False)
    await interaction.followup.send(spam_block, ephemeral=False)
    logger.info(f"Successfully processed /spam payload for {interaction.user}")
    
    try:
        await interaction.delete_original_response()
    except discord.HTTPException as e:
        logger.error(f"Failed to delete initial 'Ok bro' message: {e}")


@client.tree.command(name="crash", description="Select a platform target and amount directly")
@app_commands.describe(platform="Choose the platform", amount="Enter how many times to execute (1-100)")
@app_commands.choices(platform=[
    app_commands.Choice(name="Mobile 📱", value="mobile"),
    app_commands.Choice(name="PC 💻", value="pc")
])
async def crash(interaction: discord.Interaction, platform: str, amount: int):
    logger.info(f"User {interaction.user} ({interaction.user.id}) called /crash | Platform: {platform} | Amount: {amount}")
    
    if client.is_locked and interaction.user.id != client.MY_USER_ID:
        logger.warning(f"/crash blocked: App is locked. Triggered by {interaction.user}")
        await interaction.response.send_message("❌ This app is currently locked by its creator!", ephemeral=True)
        return

    if amount <= 0 or amount > 100:
        logger.warning(f"/crash rejected: Amount {amount} out of bounds.")
        await interaction.response.send_message("❌ Amount must be between 1 and 100!", ephemeral=True)
        return

    await interaction.response.send_message("Ok bro", ephemeral=False)

    if platform == "mobile":
        mobile_image_url = "https://discordapp.com"
        payload = f"{mobile_image_url}\n" * amount
        if len(payload) > 2000:
            logger.warning(f"/crash mobile rejected: Payload size ({len(payload)}) over 2000 chars.")
            await interaction.followup.send("❌ Total characters exceed Discord's 2000 limit. Reduce the amount!", ephemeral=False)
        else:
            await interaction.followup.send(payload, ephemeral=False)
            logger.info(f"Successfully processed /crash mobile payload for {interaction.user}")
            
    elif platform == "pc":
        await interaction.followup.send(f"💻 Executing PC protocol {amount} times...", ephemeral=False)
        logger.info(f"Successfully processed /crash PC payload for {interaction.user}")

    try:
        await interaction.delete_original_response()
    except discord.HTTPException as e:
        logger.error(f"Failed to delete initial 'Ok bro' message: {e}")


@client.tree.command(name="self_destruct", description="Send a temporary message that deletes itself")
@app_commands.describe(seconds="How many seconds before it disappears (Max 60)", message="The secret message")
async def self_destruct(interaction: discord.Interaction, seconds: int, message: str):
    logger.info(f"User {interaction.user} ({interaction.user.id}) called /self_destruct | Time: {seconds}s")

    if client.is_locked and interaction.user.id != client.MY_USER_ID:
        logger.warning(f"/self_destruct blocked: App is locked. Triggered by {interaction.user}")
        await interaction.response.send_message("❌ This app is currently locked by its creator!", ephemeral=True)
        return

    if seconds <= 0 or seconds > 60:
        await interaction.response.send_message("❌ Keep the timer between 1 and 60 seconds!", ephemeral=True)
        return

    target_time = int(time.time()) + seconds
    countdown_text = f"💣 **TOP SECRET:** {message}\n\n*This message will vanish <t:{target_time}:R>...*"

    await interaction.response.send_message(countdown_text, ephemeral=False)
    await asyncio.sleep(seconds)

    try:
        await interaction.delete_original_response()
        logger.info(f"💥 Successfully self-destructed message from {interaction.user}")
    except discord.HTTPException as e:
        logger.error(f"Failed to self-destruct message: {e}")


# --- START THE BOT --- #
    TOKEN = os.getenv("DISCORD_TOKEN")
    else:
        print("❌ Error: 'DISCORD_TOKEN' environment variable not found.")
