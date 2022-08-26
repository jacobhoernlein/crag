import os
import discord
from discord.ext import commands
import cleverbot


class CragBot(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.channel:discord.TextChannel = None
        self.mode = 1
        self.authed_users = ['243845903146811393', '534939215855878151']
        self.cb = cleverbot.load('cleverbot.crag')

    async def on_ready(self):
        self.channel = await self.fetch_channel('1010692822128672829')
        await self.tree.sync()
        print("crag.")

    async def on_message(self, msg:discord.Message):
        if self.mode == 1:
            if msg.channel == self.channel \
            and msg.author != self.user:
                response = self.cb.say(msg.content)
                self.cb.save('cleverbot.crag')
                await msg.channel.send(response)
        
        if self.mode == 2:
            if msg.channel.type == discord.ChannelType.private \
            and str(msg.author.id) in crag.authed_users:
                await crag.channel.send(msg.content)

crag = CragBot(command_prefix="crag.", intents=discord.Intents.all())

@crag.tree.command(name="mode", description="Does nothing.")
async def change_mode(interaction:discord.Interaction):
    if str(interaction.user.id) not in crag.authed_users:
        await interaction.response.send_message("No.", ephemeral=True)
        return
    if crag.mode == 1:
        crag.mode = 2
        await interaction.response.send_message("Changed to Manual.", ephemeral=True)
        return
    if crag.mode == 2:
        crag.mode = 1
        await interaction.response.send_message("Changed to Auto.", ephemeral=True)
        return

crag.run(os.getenv('CRAGTOKEN'))
