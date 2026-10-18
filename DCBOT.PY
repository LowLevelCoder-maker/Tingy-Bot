import discord
from discord import app_commands
import os

class MyClient(discord.Client):
    def __init__(self):
        super().__init__(intents=discord.Intents.default())
        self.tree = app_commands.CommandTree(self)
        
        # ⚠️ PASTE YOUR COPIED USER ID NUMBER BELOW BETWEEN THE QUOTES
        self.MY_USER_ID = "1240560087681073205"
        
        # This is your toggle switch! (True = Locked, False = Unlocked)
        self.is_locked = False 

    async def on_ready(self):
        print(f'Logged in as {self.user}!')
        await self.tree.sync()
        print("✅ Slash commands successfully synced to your profile!")

client = MyClient()

# 1. The Toggle Control Command
@client.tree.command(name="lockapp", description="Toggle the app lock state (Owner only)")
async def lockapp(interaction: discord.Interaction):
    # Security check: Only allow YOU to flip the switch
    if str(interaction.user.id) != client.MY_USER_ID:
        await interaction.response.send_message("❌ You are not the owner of this app!", ephemeral=True)
        return

    # Flip the True/False state
    client.is_locked = not client.is_locked
    
    status = "🔒 LOCKED (Only you can use it)" if client.is_locked else "🔓 UNLOCKED (Anyone can use it)"
    await interaction.response.send_message(f"App status updated: {status}", ephemeral=True)


# 2. Your Protected Spam Command
@client.tree.command(name="spam", description="Spam messages within Discord user limits")
@app_commands.describe(amount="How many times to repeat (Max 30)", message="The text to spam")
async def spam(interaction: discord.Interaction, amount: int, message: str):
    # Guard check: If the app is locked AND the person isn't you, block them!
    if client.is_locked and str(interaction.user.id) != client.MY_USER_ID:
        await interaction.response.send_message("❌ This app is currently locked by its creator!", ephemeral=True)
        return

    if amount > 100:
        await interaction.response.send_message("❌ Keep it under 100 to prevent text from cutting off!", ephemeral=True)
        return

    spam_block = f"{message}\n" * amount
    await interaction.response.send_message(spam_block)


# 3. New Protected Crash Command with Platform Dropdown
@client.tree.command(name="crash", description="Select a platform target")
@app_commands.describe(platform="Choose whether the target is on Mobile or PC")
@app_commands.choices(platform=[
    app_commands.Choice(name="Mobile", value="mobile"),
    app_commands.Choice(name="PC", value="pc")
])
async def crash(interaction: discord.Interaction, platform: app_commands.Choice[str]):
    # Guard check: If the app is locked AND the person isn't you, block them!
    if client.is_locked and str(interaction.user.id) != client.MY_USER_ID:
        await interaction.response.send_message("❌ This app is currently locked by its creator!", ephemeral=True)
        return

    # Get the value selected from the dropdown menu
    selected_platform = platform.value

    if selected_platform == "mobile":
        # Direct URL to the GIF image payload
        mobile_image_url = "https://cdn.discordapp.com/attachments/1559201133036314716/1561416786266558665/giphy.gif?ex=6ad64633&is=6ad4f4b3&hm=eb58358036ff2842ed47acffa0943900d0bd9e978da661352eae098054882a53&"
        await interaction.response.send_message(mobile_image_url)
        
    elif selected_platform == "pc":
        await interaction.response.send_message("💻 Executing PC protocol...")


BOT_TOKEN = os.environ.get('DISCORD_TOKEN')
if BOT_TOKEN is not None:
    client.run(BOT_TOKEN)
