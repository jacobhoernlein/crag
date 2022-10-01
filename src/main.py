"""
A simple bot that uses the cleverbot module to create a chat bot.
Uses a sqlite database for multi-server support.

Version 2.
"""

import asyncio
import os

import aiosqlite
import cleverbot
import discord
from discord.ext import commands


class CragBot(commands.Bot):
    """Subclassed commands.Bot that includes database and cleverbot api connections."""

    db: aiosqlite.Connection
    cb: cleverbot.Cleverbot

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.tree.add_command(
            discord.app_commands.Command(
                name="setchannel",
                description="Change the channel that crag will live in to the current channel.",
                callback=self.change_channel_callback
            )
        )
        self.tree.add_command(
            discord.app_commands.Command(
                name="donate",
                description="Support the creator (he is broke).",
                callback=self.donate_command_callback
            )
        )

    async def on_ready(self):
        self.db = await aiosqlite.connect('crag.sqlite')

        await self.db.execute('CREATE TABLE IF NOT EXISTS guilds (guild_id INTEGER, channel_id INTEGER)')
        await self.db.commit()

        try:
            self.cb = cleverbot.load('crag.cleverbot')
        except FileNotFoundError:
            print("No cleverbot save file found. Create a new one manually and save as 'crag.cleverbot'")
            print("Visit https://pypi.org/project/cleverbot.py/ to learn how.")
            await self.close()

        await self.tree.sync()
        print("crag.")

    async def on_disconnect(self):
        await self.db.close()

    async def on_resumed(self):
        self.db = await aiosqlite.connect('crag.sqlite')
    
    def get_convo(self, key: str) -> cleverbot.cleverbot.Conversation:
        """Returns a conversation with the given key; creates it if it doesn't exist."""
        
        try:
            convo = self.cb.conversations[key]
        except (TypeError, KeyError):
            # cb.conversations is None type, can't subscript
            # or conversation does not exist for guild id
            convo = self.cb.conversation(key)
        
        return convo

    async def on_message(self, msg: discord.Message):
        """Listens for messages in the channel set for the server then responds to the conversation."""

        try:
            async with self.db.execute(f'SELECT channel_id FROM guilds WHERE guild_id = {msg.guild.id}') as cursor:
                crag_channel_id = (await cursor.fetchone())[0]
        except (AttributeError, TypeError):
            # Guild object has no id attribute or
            # No record exists, can't subscript None type
            return
        
        if msg.author == self.user or msg.channel.id != crag_channel_id:
            return

        convo = self.get_convo(str(msg.guild.id))
        response = convo.say(msg.content)
        async with msg.channel.typing():
            await asyncio.sleep(2)
        await msg.channel.send(response)

        self.cb.save('crag.cleverbot')
                
    @discord.app_commands.guild_only()
    async def change_channel_callback(self, interaction: discord.Interaction):
        """Sets up the bot to work in the channel the command was run in. Creates a record if it does not exist."""
        
        async with self.db.execute(f'SELECT * FROM guilds WHERE guild_id = {interaction.guild_id}') as cursor:
            record = await cursor.fetchone()

        if record is None:
            await self.db.execute(f'INSERT INTO guilds VALUES ({interaction.guild_id}, {interaction.channel_id})')
        else:
            await self.db.execute(f'UPDATE guilds SET channel_id = {interaction.channel_id} WHERE guild_id = {interaction.guild_id}')
        await self.db.commit()

        convo = self.get_convo(str(interaction.guild_id))
        response = convo.say('Tell me something interesting.')
        await interaction.response.send_message(response)

        self.cb.save('crag.cleverbot')
        
    async def donate_command_callback(self, interaction: discord.Interaction):
        """Sends a link to the user that lets them donate to me."""        
        
        await interaction.response.send_message("Please consider supporting my creator at https://paypal.me/jhoernlein")


if __name__ == '__main__':

    crag = CragBot(
        command_prefix='NO PREFIX',
        help_command=None,
        intents=discord.Intents.all(),
        activity=discord.Activity(type=discord.ActivityType.watching, name="for /setchannel")
    )
    
    crag.run(os.getenv('CRAGTOKEN'))
    
    try:
        asyncio.run(crag.db.close())
    except ValueError:
        pass
