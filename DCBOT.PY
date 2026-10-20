import discord
from discord import app_commands
import os
import logging
import sys
from collections import deque
import asyncio
import time
import psutil

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
        intents = discord.Intents.default()
        intents.guilds = True
        
        super().__init__(intents=intents)
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

@client.tree.command(name="checklogs", description="View the logs (Owner only)")
async def checklogs(interaction: discord.Interaction):
    if interaction.user.id != client.MY_USER_ID:
        logger.warning(f"Unauthorized /checklogs access attempt by {interaction.user} ({interaction.user.id})")
        await interaction.response.send_message(" You are not the owner of this app.❌❌", ephemeral=True)
        return

    if not LOG_BUFFER:
        await interaction.response.send_message(" Log buffer is empty.📭", ephemeral=True)
        return

    logs_joined = "\n".join(LOG_BUFFER)
    log_payload = f"```text\n{logs_joined}\n```"
    
    if len(log_payload) > 2000:
        log_payload = f"```text\n...[Truncated]...\n{logs_joined[-1800:]}\n```"
        
    await interaction.response.send_message(f" **Recent Logs ({len(LOG_BUFFER)} entries):**\n{log_payload}", ephemeral=True)


@client.tree.command(name="clearlogs", description="Delete all made logs.❗ (Owner only)")
async def clearlogs(interaction: discord.Interaction):
    if interaction.user.id != client.MY_USER_ID:
        logger.warning(f"Unauthorized /clearlogs attempt by {interaction.user} ({interaction.user.id})")
        await interaction.response.send_message(" You are not the owner of this app⛔", ephemeral=True)
        return

    LOG_BUFFER.clear()
    logger.info(f"Internal memory log buffer cleared by owner ({interaction.user}).")
    await interaction.response.send_message(" **Log history cleared successfully!** Future activities will show fresh.", ephemeral=True)


# --- GENERAL BOT COMMANDS --- #

@client.tree.command(name="lockapp", description="Prevent users from using it.📛(Owner only)")
async def lockapp(interaction: discord.Interaction):
    logger.info(f"User {interaction.user} ({interaction.user.id}) attempted to use /lockapp")

    if interaction.user.id != client.MY_USER_ID:
        logger.warning(f"Unauthorized /lockapp attempt by {interaction.user}")
        await interaction.response.send_message(" You are not the owner of this app!", ephemeral=True)
        return

    client.is_locked = not client.is_locked
    status = "LOCKED" if client.is_locked else "UNLOCKED"
    logger.info(f"App lock status changed to: {status} by owner.")
    await interaction.response.send_message(f"App status updated: {status}", ephemeral=True)

# --- PURGE COMMAND --- #
@client.tree.command(name="purge", description="delete messages in the current channel")
@app_commands.describe(amount="Number of messages to purge (1-100)")
@app_commands.checks.has_permissions(manage_messages=True)
async def purge(interaction: discord.Interaction, amount: int):
    logger.info(f"User {interaction.user} ({interaction.user.id}) called /purge | Amount: {amount}")

    # Lock check
    if client.is_locked and interaction.user.id != client.MY_USER_ID:
        logger.warning(f"/purge blocked: App is locked. Triggered by {interaction.user}")
        await interaction.response.send_message("❌ This app is currently locked by its creator!", ephemeral=True)
        return

    # Range check
    if amount < 1 or amount > 100:
        logger.warning(f"/purge rejected: Amount {amount} out of bounds.")
        await interaction.response.send_message(" Please enter an amount between 1 and 100, bro!", ephemeral=True)
        return

    # Acknowledge the command quickly to prevent timeouts
    await interaction.response.defer(ephemeral=True)

    try:
        deleted = await interaction.channel.purge(limit=amount)
        logger.info(f"Successfully purged {len(deleted)} messages in channel {interaction.channel.id}")
        await interaction.followup.send(f" **Successfully purged {len(deleted)} messages!**", ephemeral=True)
    except discord.Forbidden:
        logger.error("Failed to execute purge: Bot lacks 'Manage Messages' permission.")
        await interaction.followup.send("Enable manage messages in order to engage command.", ephemeral=True)
    except discord.HTTPException as e:
        logger.error(f"Purge operation encountered an error: {e}")
        await interaction.followup.send(" Something went wrong while attempting to delete messages.", ephemeral=True)

# Handle permission errors cleanly when users lack authority to run it
@purge.error
async def purge_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    if isinstance(error, app_commands.MissingPermissions):
        await interaction.response.send_message(" You lack the **Manage Messages** permission to use this command!", ephemeral=True)

@client.tree.command(name="spam", description="Spam messages within Discord user limits")
@app_commands.describe(amount="How much (Max 50)", message="The text to spam")
async def spam(interaction: discord.Interaction, amount: int, message: str):
    logger.info(f"User {interaction.user} ({interaction.user.id}) called /spam | Amount: {amount} | Msg: '{message}'")

    if client.is_locked and interaction.user.id != client.MY_USER_ID:
        logger.warning(f"/spam blocked: App is locked. Triggered by {interaction.user}")
        await interaction.response.send_message(" This app is currently locked by its founder!", ephemeral=True)
        return

    if amount > 50:
        logger.warning(f"/spam rejected: Amount {amount} exceeds max rule of 50.")
        await interaction.response.send_message(" Keep it under 50! GREEDY BOY", ephemeral=True)
        return

    spam_block = f"{message}\n" * amount
    if len(spam_block) > 2000:
        logger.warning(f"/spam rejected: Payload total length ({len(spam_block)} chars) exceeds Discord limit.")
        await interaction.response.send_message("Bro,I think that sentence u tried to send was a little bit long.", ephemeral=True)
        return

    await interaction.response.send_message("Okay.", ephemeral=False)
    await interaction.followup.send(spam_block, ephemeral=False)
    logger.info(f"Successfully processed /spam payload for {interaction.user}")
    
    try:
        await interaction.delete_original_response()
    except discord.HTTPException as e:
        logger.error(f"Failed to delete initial 'Okay' message: {e}")

@client.tree.command(name="crash", description="Select a platform target and amount directly")
@app_commands.describe(platform="Choose the platform", amount="Enter how many times")
@app_commands.choices(platform=[
    app_commands.Choice(name="PC / Desktop", value="pc"),
    app_commands.Choice(name="Mobile iOS/Android", value="mobile")
])
async def crash(interaction: discord.Interaction, platform: app_commands.Choice[str], amount: int):
    logger.info(f"User {interaction.user} ({interaction.user.id}) called /crash | Platform: {platform.value} | Amount: {amount}")

    if client.is_locked and interaction.user.id != client.MY_USER_ID:
        logger.warning(f"/crash blocked: App is locked. Triggered by {interaction.user}")
        await interaction.response.send_message(" This app is currently locked by its founder!", ephemeral=True)
        return

    # Caps the max amount so your bot doesn't get rate-limited
    if amount > 50:
        await interaction.response.send_message("Keep it under 50 times, bro!", ephemeral=True)
        return

    # Quick response acknowledgment to stop Discord from timing out
    await interaction.response.send_message(f"Executing {platform.name} protocol...", ephemeral=False)

    # Assign correct image link based on dropdown selection value
    if platform.value == "pc":
        image_url = "https://giphy.com"
    elif platform.value == "mobile":
        # Put your mobile specific crashing GIF link right here
        image_url = "https://giphy.com"

    # Safely loop through whichever image link was selected above
    for _ in range(amount):
        await interaction.channel.send(image_url)
        await asyncio.sleep(0.4)

    logger.info(f"Successfully processed /crash {platform.value} payload {amount} times for {interaction.user}")

    try:
        await interaction.delete_original_response()
    except discord.HTTPException as e:
        logger.error(f"Failed to delete initial processing message: {e}")



# --- START BOT --- #
# Make sure your token is securely placed in your environment variables on Railway
if __name__ == "__main__":
    TOKEN = os.getenv("DISCORD_TOKEN")
    if TOKEN:
        client.run(TOKEN)
    else:
        logger.critical("No DISCORD_TOKEN found in environment variables!")
