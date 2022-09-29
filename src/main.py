"""
A simple bot that uses the cleverbot module to create a chat bot.
Uses a sqlite database for multi-server support.

Version 2.
"""

import asyncio
from dataclasses import dataclass
import os
import sqlite3

import cleverbot
import discord
from discord.ext import commands


@dataclass
class GuildSetting:
    """Contains settings for each guild that the bot is in."""

    channel: discord.TextChannel
    convo: cleverbot.cleverbot.Conversation


class CommandsCog(commands.Cog):
    """Cog that contains all the functionality because idk how to make app commands work in a subclassed bot."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.cb: cleverbot.Cleverbot = cleverbot.load('cleverbot.crag')

        self.db = sqlite3.connect('crag.sqlite')
        self.guild_dict: dict[int, GuildSetting] = {}
        
    @commands.Cog.listener()
    async def on_ready(self):
        """Creates guildsettings for each record in the table then adds them to the dictionary."""

        cursor = self.db.execute("SELECT * FROM guilds")
        guild_records = cursor.fetchall()
        
        for guild_record in guild_records:
            
            guild_id = guild_record[0]
            channel_id = guild_record[1]
            
            guild: discord.Guild = discord.utils.find(lambda g: g.id == guild_id, self.bot.guilds)
            channel: discord.TextChannel = discord.utils.find(lambda c: c.id == channel_id, guild.channels)
            conversation: cleverbot.cleverbot.Conversation = self.cb.conversations[str(guild_id)]

            self.guild_dict[guild_id] = GuildSetting(channel, conversation)

        await self.bot.tree.sync()
        print("crag.")

    @commands.Cog.listener()
    async def on_message(self, msg: discord.Message):
        """Listens for messages in the channel set for the server then responds to the conversation."""

        if msg.author == self.bot.user:
            return

        if msg.guild.id in self.guild_dict.keys():
            guild_setting = self.guild_dict[msg.guild.id]
            
            if msg.channel == guild_setting.channel:
                
                response = guild_setting.convo.say(msg.content)
                async with msg.channel.typing():
                    await asyncio.sleep(2)
                await msg.channel.send(response)

                self.cb.save('cleverbot.crag')

    @commands.Cog.listener()
    async def on_guild_remove(self, guild: discord.Guild):
        """Removes the guild's entry from the database and server dictionary."""

        if guild.id not in self.guild_dict.keys():
            return

        del self.guild_dict[guild.id]
        self.db.execute(f"DELETE FROM guilds WHERE guild_id = {guild.id}")
        self.db.commit()
    
    @discord.app_commands.command(name="setchannel", description="Change the channel that crag will live in to the current channel.")
    @discord.app_commands.guild_only()
    async def change_channel(self, interaction: discord.Interaction):
        """Sets up the bot to work in the channel the command was run in. Creates a record if it does not exist."""

        if interaction.guild_id not in self.guild_dict.keys():
            conversation = self.cb.conversation(str(interaction.guild_id))
            self.guild_dict[interaction.guild_id] = GuildSetting(interaction.channel, conversation)
            self.db.execute(f"INSERT INTO guilds VALUES ({interaction.guild_id}, {interaction.channel_id})")
        else:    
            self.guild_dict[interaction.guild_id].channel = interaction.channel
            self.db.execute(f"UPDATE guilds SET channel_id = {interaction.channel_id} WHERE guild_id = {interaction.guild_id}")
        
        self.db.commit()

        await interaction.response.send_message("Channel set up.", ephemeral=True)
        
    @discord.app_commands.command(name="donate", description="Support the creator (he is broke).")
    async def donate_command(self, interaction: discord.Interaction):
        """Sends a link to the user that lets them donate to me."""        
        
        await interaction.response.send_message("Please consider supporting my creator at https://paypal.me/jhoernlein")


if __name__ == '__main__':
    
    crag = commands.Bot(
        command_prefix="NO PREFIX",
        help_command=None,
        intents=discord.Intents.all()
    )
    asyncio.run(crag.add_cog(CommandsCog(crag)))
    crag.run(os.getenv('CRAGTOKEN'))
