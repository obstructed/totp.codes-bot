import discord
from discord import app_commands
import pyotp
import time
import asyncio

TOKEN = 'MTM3ODQ5ODU0OTU2OTgxODY2NQ.G7w1ve.K5ykbldQ7qd05cYZbfjMMdzoy5oZljo65FOUSQ'

class MyClient(discord.Client):
    def __init__(self):
        intents = discord.Intents.default()
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        await self.tree.sync()

client = MyClient()

@client.tree.command(
    name="totp",
    description="Generate a TOTP from your Base32 secret",
)
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
@app_commands.user_install()
@app_commands.describe(secret="Your Base32 secret code")
async def totp(interaction: discord.Interaction, secret: str):
    secret = secret.replace(" ", "").upper()
    if len(secret) < 16 or len(secret) > 40:
        await interaction.response.send_message(
            "Secret length must be between 16 and 40 characters.",
            ephemeral=True
        )
        return

    try:
        totp_obj = pyotp.TOTP(secret)
        otp = totp_obj.now()
        current_time = time.time()
        interval = totp_obj.interval
        time_remaining = int(interval - (current_time % interval))
        await interaction.response.send_message(
            f"Your current OTP is: `{otp}`\nExpires in: **{time_remaining}** seconds",
            ephemeral=True
        )
        await asyncio.sleep(time_remaining)
        await interaction.followup.send(
            "This TOTP has expired.",
            ephemeral=True
        )
    except Exception as e:
        print("Error generating TOTP:", e)
        await interaction.response.send_message(
            "Failed to generate OTP. Please check your secret is a valid Base32 string.",
            ephemeral=True
        )

client.run(TOKEN)
