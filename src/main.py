"""
A simple bot that uses the cleverbot module to create a chat bot.
You can also take manual control of the bot for yourself.
"""

import asyncio
import os
import sqlite3
from dataclasses import dataclass

import discord
from discord.ext import commands
import cleverbot


@dataclass
class GuildSetting:
    """Contains settings for each guild that the bot is in."""

    guild: discord.Guild
    channel: discord.TextChannel
    mode: int
    convo: cleverbot.cleverbot.Conversation


class CommandsCog(commands.Cog):
    """Cog that contains all the functionality because idk how to make app commands work in a subclassed bot."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.guild_settings: dict[int, GuildSetting] = {}
        self.cb: cleverbot.Cleverbot = cleverbot.load('cleverbot.crag')
        self.db = sqlite3.connect('crag.sqlite')

    @commands.Cog.listener()
    async def on_ready(self):
        
        cursor = self.db.execute("SELECT * FROM guilds")
        guild_records = cursor.fetchall()

        for guild_record in guild_records:
            guild_id = guild_record[0]
            channel_id = guild_record[1]
            
            guild: discord.Guild = discord.utils.find(lambda g: g.id == guild_id, self.bot.guilds)
            channel: discord.TextChannel = discord.utils.find(lambda c: c.id == channel_id, guild.channels)
            mode = guild_record[2]
            conversation: cleverbot.cleverbot.Conversation = self.cb.conversations[str(guild.id)]

            self.guild_settings[guild.id] = GuildSetting(guild, channel, mode, conversation)

        await self.bot.tree.sync()
        print("crag.")

    @commands.Cog.listener()
    async def on_message(self, msg: discord.Message):
        if msg.author == self.bot.user:
            return

        if msg.guild.id in self.guild_settings.keys():
            guild_setting = self.guild_settings[msg.guild.id]

            if guild_setting.channel == msg.channel and guild_setting.mode == 1:
                response = guild_setting.convo.say(msg.content)
                self.cb.save('cleverbot.crag')

                async with msg.channel.typing():
                    await asyncio.sleep(2)
                await msg.channel.send(response)

    @commands.Cog.listener()
    async def on_guild_remove(self, guild: discord.Guild):
        
        if guild.id not in self.guild_settings.keys():
            return

        del self.guild_settings[guild.id]
        self.db.execute(f"DELETE FROM guilds WHERE guild_id = {guild.id}")
        self.db.commit()

    @discord.app_commands.command(name="mode", description="Change crag's mode. Manual will disable cleverbot. Then use /say.")
    @discord.app_commands.guild_only()
    @discord.app_commands.choices(mode=[
        discord.app_commands.Choice(name="Auto", value=1),
        discord.app_commands.Choice(name="Manual", value=2)
        ])
    async def crag_mode(self, interaction: discord.Interaction, mode: discord.app_commands.Choice[int]):
    
        if interaction.guild_id not in self.guild_settings.keys():
            await interaction.response.send_message("You have to set me up first! do /setchannel in any channel.", ephemeral=True)
            return
        
        if mode.value == 1:
            self.db.execute(f"UPDATE guilds SET mode = 1 WHERE guild_id = {interaction.guild_id}")
            self.guild_settings[interaction.guild_id].mode = 1
            await interaction.response.send_message("Changed to Auto", ephemeral=True)
            
        if mode.value == 2:
            self.db.execute(f"UPDATE guilds SET mode = 2 WHERE guild_id = {interaction.guild_id}")
            self.guild_settings[interaction.guild_id].mode = 2
            await interaction.response.send_message("Changed to manual. Using /say.", ephemeral=True)
            
        self.db.commit()

    @discord.app_commands.command(name="say", description="Make crag say something.")
    @discord.app_commands.guild_only()
    @discord.app_commands.describe(content="The thing crag should say.")
    async def crag_say(self, interaction: discord.Interaction, content: str):
        
        if interaction.guild_id not in self.guild_settings.keys():
            await interaction.response.send_message("You have to set me up first! do /setchannel in any channel.", ephemeral=True)
            return
        
        if self.guild_settings[interaction.guild_id].mode == 2:
            await interaction.channel.send(content)
            await interaction.response.send_message(".")
            await interaction.delete_original_response()
        else:
            await interaction.response.send_message("Change to manual mode first!", ephemeral=True)
    
    @discord.app_commands.command(name="setchannel", description="Change the channel that crag will live in to the current channel.")
    @discord.app_commands.guild_only()
    async def change_channel(self, interaction: discord.Interaction):
        
        if interaction.guild_id not in self.guild_settings.keys():
            self.db.execute(f"INSERT INTO guilds VALUES ({interaction.guild_id}, {interaction.channel_id}, 1)")
            conversation = self.cb.conversation(str(interaction.guild_id))
            self.guild_settings[interaction.guild_id] = GuildSetting(interaction.guild, interaction.channel, 1, conversation)
        else:    
            self.db.execute(f"UPDATE guilds SET channel_id = {interaction.channel_id} WHERE guild_id = {interaction.guild_id}")
            self.guild_settings[interaction.guild_id].channel = interaction.channel
        
        await interaction.response.send_message("Channel set up.", ephemeral=True)
        self.db.commit()


if __name__ == '__main__':
    
    crag = commands.Bot(
        command_prefix="NO PREFIX",
        help_command=None,
        intents=discord.Intents.all()
    )

    async def addcog():
        await crag.add_cog(CommandsCog(crag))
    asyncio.run(addcog())

    crag.run(os.getenv('CRAGTOKEN'))
