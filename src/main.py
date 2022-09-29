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
            conversation: cleverbot.cleverbot.Conversation = self.cb.conversations[str(guild.id)]

            self.guild_settings[guild.id] = GuildSetting(guild, channel, conversation)

        await self.bot.tree.sync()
        print("crag.")

    @commands.Cog.listener()
    async def on_message(self, msg: discord.Message):
        if msg.author == self.bot.user:
            return

        if msg.guild.id in self.guild_settings.keys():
            guild_setting = self.guild_settings[msg.guild.id]

            if guild_setting.channel == msg.channel:
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
    
    @discord.app_commands.command(name="setchannel", description="Change the channel that crag will live in to the current channel.")
    @discord.app_commands.guild_only()
    async def change_channel(self, interaction: discord.Interaction):
        
        if interaction.guild_id not in self.guild_settings.keys():
            self.db.execute(f"INSERT INTO guilds VALUES ({interaction.guild_id}, {interaction.channel_id})")
            conversation = self.cb.conversation(str(interaction.guild_id))
            self.guild_settings[interaction.guild_id] = GuildSetting(interaction.guild, interaction.channel, conversation)
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
