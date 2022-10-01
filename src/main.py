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
        """Connects to the database and syncs the command tree."""
        
        self.db = await aiosqlite.connect('crag.sqlite')
        await self.db.execute('CREATE TABLE IF NOT EXISTS guilds (guild_id INTEGER, channel_id INTEGER)')
        await self.db.commit()

        await self.tree.sync()
        
        response = self.cb.say("Hello!")
        print(response)
    
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

        await interaction.response.send_message("Channel Updated.", ephemeral=True)

    async def donate_command_callback(self, interaction: discord.Interaction):
        """Sends a link to the user that lets them donate to me."""        
        
        await interaction.response.send_message("Please consider supporting my creator at https://paypal.me/jhoernlein")


def prep(bot: CragBot):
    """Ensures the cleverbot is connected to the API either by a save file or API token."""
    
    try:
        bot.cb = cleverbot.load('crag.cleverbot')
    except FileNotFoundError:
        
        while True:
            cleverbot_token = input("Enter your Cleverbot API token: ")
            bot.cb = cleverbot.Cleverbot(cleverbot_token)

            try:
                bot.cb.say('TEST')
            except cleverbot.APIError:
                print("Invalid API key. Try again. ")
            else:
                bot.cb.save('crag.cleverbot')
                break

async def cleanup(bot: CragBot):
    """Closes the connections to the database if not already done."""
    
    try:
        await bot.db.close()
    except ValueError:
        # Connection already closed
        pass
    

if __name__ == '__main__':

    crag = CragBot(
        command_prefix='NO PREFIX',
        help_command=None,
        intents=discord.Intents.all(),
        activity=discord.Activity(type=discord.ActivityType.watching, name="for /setchannel")
    )
    
    prep(crag)
    crag.run(os.getenv('CRAGTOKEN'))
    asyncio.run(cleanup(crag))
