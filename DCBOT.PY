
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
        await interaction.response.send_message(" You are not the owner of this app😭", ephemeral=True)
        return

    # Flip the True/False state
    client.is_locked = not client.is_locked
    
    status = "🔒 LOCKED (Only you can use it)" if client.is_locked else "🔒 UNLOCKED (Anyone can use it)"
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
        await interaction.response.send_message("❌ Keep it under 100 to prevent text from exploding off!", ephemeral=True)
        return

    spam_block = f"{message}\n" * amount
    await interaction.response.send_message(spam_block)

BOT_TOKEN = os.environ.get('DISCORD_TOKEN')
if BOT_TOKEN is not None:
    client.run(BOT_TOKEN)
