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
        self.cb = cleverbot.load('crag.cleverbot')

        await self.tree.sync()
        print("crag.")

    async def on_disconnect(self):
        await self.db.close()

    async def on_resumed(self):
        self.db = await aiosqlite.connect('crag.sqlite')
    
    async def on_message(self, msg: discord.Message):
        """Listens for messages in the channel set for the server then responds to the conversation."""

        if msg.author == self.user or msg.guild is None:
            return

        async with self.db.execute(f'SELECT channel_id FROM guilds WHERE guild_id = {msg.guild.id}') as cursor:
            record = await cursor.fetchone()
        if record is None:
            return
            
        if record[0] == msg.channel.id:

            convo = self.cb.conversations[str(msg.guild.id)]
            response = convo.say(msg.content)

            async with msg.channel.typing():
                await asyncio.sleep(2)
            await msg.channel.send(response)

            self.cb.save('crag.cleverbot')
                
    @discord.app_commands.guild_only()
    async def change_channel_callback(self, interaction: discord.Interaction):
        """Sets up the bot to work in the channel the command was run in. Creates a record if it does not exist."""

        if str(interaction.guild_id) in self.cb.conversations.keys():
            await self.db.execute(f'UPDATE guilds SET channel_id = {interaction.channel_id} WHERE guild_id = {interaction.guild_id}')
        else:    
            self.cb.conversation(str(interaction.guild_id))
            await self.db.execute(f'INSERT INTO guilds VALUES ({interaction.guild_id}, {interaction.channel_id})')
        
        await self.db.commit()
        await interaction.response.send_message("Channel set up.", ephemeral=True)
        
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
