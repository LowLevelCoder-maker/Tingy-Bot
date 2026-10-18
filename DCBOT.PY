import discord
from discord import app_commands
import os

class MyClient(discord.Client):
    def __init__(self):
        super().__init__(intents=discord.Intents.default())
        self.tree = app_commands.CommandTree(self)

    async def on_ready(self):
        print(f'Logged in as {self.user}!')
        await self.tree.sync()
        print("✅ Slash commands successfully synced to your profile!")

client = MyClient()

@client.tree.command(name="spam", description="Spam messages within Discord user limits")
@app_commands.describe(amount="How many times to repeat (Max 50)", message="The text to spam")
async def spam(interaction: discord.Interaction, amount: int, message: str):
    if amount > 50:
        await interaction.response.send_message(" Keep it under 50 to prevent text from exploding!", ephemeral=True)
        return

    spam_block = f"{message}\n" * amount
    await interaction.response.send_message(spam_block)

# This reads your token safely from Railway's settings panel
client.run(os.environ.get('DISCORD_TOKEN'))
