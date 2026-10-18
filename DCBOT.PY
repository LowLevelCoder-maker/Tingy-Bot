import discord
from discord import app_commands
import os

class SpamButton(discord.ui.View):
    def __init__(self, client):
        super().__init__(timeout=None) # timeout=None makes the button last forever
        self.client = client

    # 1. The Stealth Button
    @discord.ui.button(label="🚀 Trigger Spam", style=discord.ButtonStyle.danger, custom_id="stealth_spam_btn")
    async def spam_button_click(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Guard check: If the app is locked AND the person isn't you, block them!
        if self.client.is_locked and str(interaction.user.id) != self.client.MY_USER_ID:
            await interaction.response.send_message("❌ This app is currently locked by its creator!", ephemeral=True)
            return

        # Hardcoded payload settings since buttons can't take user inputs directly
        amount = 15
        message = "Get spammed! 💀"
        
        spam_block = f"{message}\n" * amount
        
        # This sends the spam block normally to the channel. 
        # Because it's a button response, Discord WILL NOT show a "used a command" banner!
        await interaction.channel.send(spam_block)
        
        # Silently acknowledge the button press to the clicker so Discord doesn't say "Interaction Failed"
        await interaction.response.defer(ephemeral=True)

class MyClient(discord.Client):
    def __init__(self):
        super().__init__(intents=discord.Intents.default())
        self.tree = app_commands.CommandTree(self)
        
        # ⚠️ PASTE YOUR COPIED USER ID NUMBER BELOW BETWEEN THE QUOTES
        self.MY_USER_ID = "1240560087681073205"
        self.TEST_GUILD_ID = 123456789012345678  # Change this to your server ID
        
        self.is_locked = False 

    async def on_ready(self):
        print(f'Logged in as {self.user}!')
        
        # Registers the button listener so it still works even if the bot restarts
        self.add_view(SpamButton(self))
        
        guild = discord.Object(id=self.TEST_GUILD_ID)
        self.tree.copy_global_to(guild=guild)
        await self.tree.sync(guild=guild)
        print("✅ Slash commands successfully synced!")

client = MyClient()

# 2. Setup Command to spawn the Button Panel
@client.tree.command(name="spawn_button", description="Spawn the stealth spam button (Owner only)")
async def spawn_button(interaction: discord.Interaction):
    if str(interaction.user.id) != client.MY_USER_ID:
        await interaction.response.send_message("❌ Owner only!", ephemeral=True)
        return
        
    # Send the button into the channel
    view = SpamButton(client)
    await interaction.response.send_message("Click the button below to spam anonymously:", view=view)

# 3. Toggle Lock Command
@client.tree.command(name="lockapp", description="Toggle the app lock state (Owner only)")
async def lockapp(interaction: discord.Interaction):
    if str(interaction.user.id) != client.MY_USER_ID:
        await interaction.response.send_message("❌ Owner only!", ephemeral=True)
        return

    client.is_locked = not client.is_locked
    status = "🔒 LOCKED" if client.is_locked else "🔓 UNLOCKED"
    await interaction.response.send_message(f"Status: {status}", ephemeral=True)

BOT_TOKEN = os.environ.get('DISCORD_TOKEN')
if BOT_TOKEN is not None:
    client.run(BOT_TOKEN)
