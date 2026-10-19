import discord
from discord import app_commands
import os

class MyClient(discord.Client):
    def __init__(self):
        super().__init__(intents=discord.Intents.default())
        self.tree = app_commands.CommandTree(self)
        self.MY_USER_ID = 1240560087681073205  
        self.is_locked = False

    async def setup_hook(self):
        print("Syncing slash commands...")
        await self.tree.sync()
        print("✅ Slash commands successfully synced globally!")

    async def on_ready(self):
        print(f'Logged in as {self.user}!')

client = MyClient()

# --- SLASH COMMANDS ---

@client.tree.command(name="lockapp", description="Toggle the app lock state (Owner only)")
async def lockapp(interaction: discord.Interaction):
    if interaction.user.id != client.MY_USER_ID:
        await interaction.response.send_message("❌ You are not the owner of this app!", ephemeral=True)
        return

    client.is_locked = not client.is_locked
    status = "🔒 LOCKED (Only you can use it)" if client.is_locked else "🔓 UNLOCKED (Anyone can use it)"
    await interaction.response.send_message(f"App status updated: {status}", ephemeral=True)


@client.tree.command(name="spam", description="Spam messages within Discord user limits")
@app_commands.describe(amount="How much (Max 2000)", message="The text to spam")
async def spam(interaction: discord.Interaction, amount: int, message: str):
    if client.is_locked and interaction.user.id != client.MY_USER_ID:
        await interaction.response.send_message("❌ This app is currently locked by its creator!", ephemeral=True)
        return

    if amount > 2000:
        await interaction.response.send_message("❌ Keep it under 2000!", ephemeral=True)
        return

    spam_block = f"{message}\n" * amount
    if len(spam_block) > 2000:
        await interaction.response.send_message("❌ Exceeds Discord's 2000 character limit!", ephemeral=True)
        return

    # 1. Send the first public message response "Ok bro"
    await interaction.response.send_message("Ok bro", ephemeral=False)
    initial_msg = await interaction.original_response()
    
    # 2. Send the payload via public followup
    await interaction.followup.send(spam_block, ephemeral=False)

    # 3. Instantly delete the "Ok bro" message
    try:
        await initial_msg.delete()
    except discord.HTTPException:
        pass


@client.tree.command(name="crash", description="Select a platform target and amount directly")
@app_commands.describe(
    platform="Choose the platform", 
    amount="Enter how many times to execute (1-100)"
)
@app_commands.choices(platform=[
    app_commands.Choice(name="Mobile 📱", value="mobile"),
    app_commands.Choice(name="PC 💻", value="pc")
])
async def crash(interaction: discord.Interaction, platform: str, amount: int):
    if client.is_locked and interaction.user.id != client.MY_USER_ID:
        await interaction.response.send_message("❌ This app is currently locked by its creator!", ephemeral=True)
        return

    if amount <= 0 or amount > 100:
        await interaction.response.send_message("❌ Amount must be between 1 and 100!", ephemeral=True)
        return

    # 1. Send the first public message response "Ok bro"
    await interaction.response.send_message("Ok bro", ephemeral=False)
    initial_msg = await interaction.original_response()

    # 2. Build payload and send via public followup
    if platform == "mobile":
        mobile_image_url = "https://discordapp.com"
        payload = f"{mobile_image_url}\n" * amount
        if len(payload) > 2000:
            await interaction.followup.send("❌ Total characters exceed Discord's 2000 limit. Reduce the amount!", ephemeral=False)
        else:
            await interaction.followup.send(payload, ephemeral=False)
    elif platform == "pc":
        await interaction.followup.send(f"💻 Executing PC protocol {amount} times...", ephemeral=False)

    # 3. Instantly delete the "Ok bro" message
    try:
        await initial_msg.delete()
    except discord.HTTPException:
        pass


# --- RUN BOT ---
BOT_TOKEN = os.environ.get('DISCORD_TOKEN')
if BOT_TOKEN is not None:
    client.run(BOT_TOKEN)
else:
    print("❌ Error: 'DISCORD_TOKEN' environment variable is missing!")
