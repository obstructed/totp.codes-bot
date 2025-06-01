import discord
from discord import app_commands
import pyotp
import time
import asyncio
from dotenv import load_dotenv
import os

load_dotenv()
TOKEN = os.getenv("TOKEN")

class MyClient(discord.Client):
    def __init__(self):
        intents = discord.Intents.default()
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        await self.tree.sync()

client = MyClient()

class TOTPView(discord.ui.View):
    def __init__(self, secret: str):
        super().__init__(timeout=None)
        self.secret = secret
        self.totp = pyotp.TOTP(secret)
        self.otp = self.totp.now()
        self.message = None
        self.running = True

        self.regenerate_button = discord.ui.Button(
            label="Regenerate",
            style=discord.ButtonStyle.grey,
            disabled=True
        )
        self.regenerate_button.callback = self.regenerate
        self.add_item(self.regenerate_button)

    def get_embed(self, remaining: int):
        if remaining > 0:
            description = f"# `{self.otp}`\n-# expires in {remaining} seconds"
        else:
            description = "# Expired"
        embed = discord.Embed(
            title="totp.codes",
            description=description,
            color=0x000000 if remaining > 0 else 0x2f3136
        )
        embed.set_footer(text="Powered by https://totp.codes/")
        return embed

    async def start_updating(self, interaction: discord.Interaction):
        await interaction.response.send_message(embed=self.get_embed(self.get_remaining()), view=self, ephemeral=True)
        self.message = await interaction.original_response()
        await self.update_loop()

    def get_remaining(self) -> int:
        return int(self.totp.interval - (time.time() % self.totp.interval))

    async def regenerate(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        self.otp = self.totp.now()
        self.running = False
        self.running = True
        self.regenerate_button.disabled = True
        self.regenerate_button.style = discord.ButtonStyle.grey
        await self.message.edit(embed=self.get_embed(self.get_remaining()), view=self)
        asyncio.create_task(self.update_loop())

    async def update_loop(self):
        while self.running:
            remaining = self.get_remaining()
            if remaining <= 0:
                self.running = False
                self.regenerate_button.disabled = False
                self.regenerate_button.style = discord.ButtonStyle.grey
                await self.message.edit(embed=self.get_embed(0), view=self)
                break
            await self.message.edit(embed=self.get_embed(remaining), view=self)
            await asyncio.sleep(1)

@client.tree.command(
    name="totp",
    description="Generate a TOTP from your Base32 secret"
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
        view = TOTPView(secret)
        await view.start_updating(interaction)
    except Exception as e:
        print("Error generating TOTP:", e)
        await interaction.response.send_message(
            "Failed to generate OTP. Please check your secret is a valid Base32 string.",
            ephemeral=True
        )

client.run(TOKEN)
