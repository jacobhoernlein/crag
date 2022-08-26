import asyncio
import os
import discord
from discord.ext import commands
import cleverbot


class CragBot(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.channel:discord.TextChannel = None
        self.mode = 1
        self.cb = cleverbot.load('cleverbot.crag')

    async def on_ready(self):
        self.channel = await self.fetch_channel('1010692822128672829')
        await self.tree.sync()
        print("crag.")

    async def on_message(self, msg:discord.Message):
        if self.mode == 1 \
        and msg.channel == self.channel \
        and msg.author != self.user:
            response = self.cb.say(msg.content)
            self.cb.save('cleverbot.crag')
            
            async with msg.channel.typing():
                await asyncio.sleep(2)
            await msg.channel.send(response)
    

crag = CragBot(command_prefix="NO PREFIX", intents=discord.Intents.all())

@crag.tree.command(name="mode", description="Change crag's mode. Manual will disable cleverbot. Then use /say")
@discord.app_commands.guild_only()
@discord.app_commands.choices(mode=[
    discord.app_commands.Choice(name="Auto", value=1),
    discord.app_commands.Choice(name="Manual", value=2)
    ])
async def crag_mode(interaction:discord.Interaction, mode:discord.app_commands.Choice[int]):
    if mode.value == 1:
        crag.mode = 1
        await interaction.response.send_message("Changed to Auto", ephemeral=True)
        await crag.change_presence(status=discord.Status.online)
    if mode.value == 2:
        crag.mode = 2
        await interaction.response.send_message("Changed to manual. Using /say.", ephemeral=True)
        await crag.change_presence(status=discord.Status.do_not_disturb)

@crag.tree.command(name="say", description="Make crag say something.")
@discord.app_commands.guild_only()
@discord.app_commands.describe(content="The thing crag should say.")
async def crag_say(interaction:discord.Interaction, content:str):
    if crag.mode == 2:
        await interaction.channel.send(content)
        await interaction.response.send_message("Done.")
        await interaction.delete_original_response()
    else:
        await interaction.response.send_message("Change to manual mode first!", ephemeral=True)

crag.run(os.getenv('CRAGTOKEN'))
