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

    def __init__(self):
        intents = discord.Intents.default()
        intents.guilds = True  # <-- ADD THIS LINE HERE
        
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
@app_commands.describe(platform="Choose the platform", amount="Enter how many times to execute (1-100)")
@app_commands.choices(platform=[
    app_commands.Choice(name="Mobile 📱", value="mobile"),
    app_commands.Choice(name="PC 💻", value="pc")
])
async def crash(interaction: discord.Interaction, platform: str, amount: int):
    logger.info(f"User {interaction.user} ({interaction.user.id}) called /crash | Platform: {platform} | Amount: {amount}")

    if client.is_locked and interaction.user.id != client.MY_USER_ID:
        logger.warning(f"/crash blocked: App is locked. Triggered by {interaction.user}")
        await interaction.response.send_message(" This app is currently locked by its creator!", ephemeral=True)
        return

    if amount <= 0 or amount > 100:
        logger.warning(f"/crash rejected: Amount {amount} out of bounds.")
        await interaction.response.send_message(" Amount must be between 1 and 100!", ephemeral=True)
        return

    await interaction.response.send_message("Ok bro", ephemeral=False)

    if platform == "mobile":
        mobile_image_url = "https://media3.giphy.com/media/v1.Y2lkPTc5MGI3NjExZXo3ZDdzNHpmejVzaXdhbnRkeDJmZ2d4eHZhOXZveTFkMnBkZ3d6ciZlcD12MV9naWZzX3NlYXJjaCZjdD1n/47JkhVe6O3gGsJSbTR/giphy.webp"
        payload = f"{mobile_image_url}\n" * amount
        if len(payload) > 2000:
            logger.warning(f"/crash mobile rejected: Payload size ({len(payload)}) over 2000 chars.")
            await interaction.followup.send("Total characters exceed Discord's 2000 limit. Reduce the amount! or i bomb ur os sir.", ephemeral=False)
        else:
            await interaction.followup.send(payload, ephemeral=False)
            logger.info(f"Successfully processed /crash mobile payload for {interaction.user}")
            
    elif platform == "desktop":
          pc_image_url = "https://media3.giphy.com/media/v1.Y2lkPTc5MGI3NjExZXo3ZDdzNHpmejVzaXdhbnRkeDJmZ2d4eHZhOXZveTFkMnBkZ3d6ciZlcD12MV9naWZzX3NlYXJjaCZjdD1n/47JkhVe6O3gGsJSbTR/giphy.webp"
          payload = f"{pc_image_url}\n" * amount
          if len(payload) > 2000:
          logger.warning(f"/crash desktop denied: Payload size ({len(payload)}) over 2000+ chars.")
          await interacton.followup.send("Total chars exceed 2000+. Reduce the amount or i call airstrike.", ephemeral=False)
        else:
        await interaction.followup.send(f" Executing PC protocol {amount} times...", ephemeral=False)
        logger.info(f"Successfully processed /crash PC payload for {interaction.user}")

    try:
        await interaction.delete_original_response()
    except discord.HTTPException as e:
        logger.error(f"Failed to delete initial 'Okay' message: {e}")


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

@client.tree.command(name="performance", description="Check live bot performance and system diagnostics")
async def performance(interaction: discord.Interaction):
    logger.info(f"User {interaction.user} checked bot diagnostics")

    if client.is_locked and interaction.user.id != client.MY_USER_ID:
        await interaction.response.send_message("❌ This app is currently locked!", ephemeral=True)
        return

    ping = round(client.latency * 1000)
    server_count = len(client.guilds)
    buffered_logs = len(LOG_BUFFER)
    
    process = psutil.Process(os.getpid())
    ram_usage = round(process.memory_info().rss / (1024 * 1024), 2)

    perf_card = (
        f"⚙️ **System Diagnostics Dashboard**\n"
        f"```yaml\n"
        f"Latency/Ping:  {ping}ms\n"
        f"Active Guilds: {server_count}\n"
        f"Log Queue:     {buffered_logs}/20 entries\n"
        f"RAM Allocation: {ram_usage} MB\n"
        f"```"
    )
    
    await interaction.response.send_message(perf_card, ephemeral=False)


    if client.is_locked and interaction.user.id != client.MY_USER_ID:
        await interaction.response.send_message("❌ This app is currently locked!", ephemeral=True)
        return

    ping = round(client.latency * 1000)
    server_count = len(client.guilds)
    buffered_logs = len(LOG_BUFFER)
    
    process = psutil.Process(os.getpid())
    ram_usage = round(process.memory_info().rss / (1024 * 1024), 2)

    perf_card = (
        f"⚙️ **System Diagnostics Dashboard**\n"
        f"```yaml\n"
        f"Latency/Ping:  {ping}ms\n"
        f"Active Guilds: {server_count}\n"
        f"Log Queue:     {buffered_logs}/20 entries\n"
        f"RAM Allocation: {ram_usage} MB\n"
        f"```"
    )
    
    await interaction.response.send_message(perf_card, ephemeral=False)
@client.tree.command(name="avatar", description="View the profile picture of a server member")
@app_commands.describe(user="The member whose avatar you want to see (Leave blank for yours)")
async def avatar(interaction: discord.Interaction, user: discord.User = None):
    target_user = user or interaction.user
    logger.info(f"User {interaction.user} checked the avatar of {target_user}")
    
    if client.is_locked and interaction.user.id != client.MY_USER_ID:
        await interaction.response.send_message("❌ This app is currently locked!", ephemeral=True)
        return
        
    avatar_url = target_user.display_avatar.url
    
    # 1. Create the Embed structure
    embed = discord.Embed(
        title=f"🖼️ Avatar for {target_user.name}", 
        color=discord.Color.blue()
    )
    embed.set_image(url=avatar_url)
    
    await interaction.response.send_message(embed=embed, ephemeral=False)

@client.tree.command(name="ghostping", description="Ping a user multiple times and vanish the messages instantly")
@app_commands.describe(user="The user you want to ghost ping", amount="How many times to ping (Max 10)")
async def ghostping(interaction: discord.Interaction, user: discord.User, amount: int):
    logger.info(f"User {interaction.user} ghost-pinged {user} | Amount: {amount}")

    if client.is_locked and interaction.user.id != client.MY_USER_ID:
        await interaction.response.send_message("❌ This app is currently locked!", ephemeral=True)
        return

    # Keep a tight limit so the bot doesn't get rate-limited or banned by Discord
    if amount <= 0 or amount > 10:
        await interaction.response.send_message("❌ Keep the pings between 1 and 10, bro!", ephemeral=True)
        return

    # Quiet confirmation to the user executing it
    await interaction.response.send_message(f"👻 Sending {amount} ghost pings to {user.mention}...", ephemeral=True)
    
    ping_channel = interaction.channel
    
    for _ in range(amount):
        # Fire and delete instantly
        try:
            ghost_msg = await ping_channel.send(user.mention)
            await ghost_msg.delete()
            # Micro-sleep to keep the order clean and prevent API hitting walls
            await asyncio.sleep(0.3)
        except discord.HTTPException as e:
            logger.error(f"Ghost ping cycle interrupted: {e}")
            break

# --- START THE BOT --- #
if __name__ == "__main__":
    TOKEN = os.getenv("DISCORD_TOKEN")
    if TOKEN:
        client.run(TOKEN)
    else:
        print("❌ Error: 'DISCORD_TOKEN' environment variable not found.")
