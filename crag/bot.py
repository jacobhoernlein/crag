"""A simple bot that uses the cleverbot module to create a chat bot.
Uses a sqlite database for multi-server support.

Version 2.
"""

import asyncio

import aiosqlite
import cleverbot
import discord
from discord.ext import commands


class CragBot(commands.Bot):
    """Subclassed commands.Bot that includes database and cleverbot API
    connections.
    """

    def __init__(self, dbname: str, cbname: str):
        super().__init__(
            command_prefix="NO PREFIX",
            help_command=None,
            intents=discord.Intents.all(),
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name="for /setchannel"))

        self.tree.add_command(
            discord.app_commands.Command(
                name="setchannel",
                description="Change the channel that crag will live in to the current channel.",
                callback=self.set_channel_callback))
        self.tree.add_command(
            discord.app_commands.Command(
                name="donate",
                description="Support the creator (he is broke).",
                callback=self.donate_callback))

        self.dbname = dbname
        self.cbname = cbname
        self.db: aiosqlite.Connection = None
        self.cb: cleverbot.Cleverbot = None

    def load_cb(self):
        """Tries to open the cleverbot file given in the init. If it
        fails prompts the user for a cleverbot token until it gets a
        valid one.
        """

        try:
            self.cb = cleverbot.load(self.cbname)
        except FileNotFoundError:
            
            while True:
                cleverbot_token = input("Enter your Cleverbot API token: ")
                self.cb = cleverbot.Cleverbot(cleverbot_token)

                try:
                    self.cb.say("TEST")
                except cleverbot.APIError:
                    print("Invalid API key. Try again. ")
                else:
                    self.cb.save(self.cbname)
                    break


    def get_convo(self, key: str) -> cleverbot.cleverbot.Conversation:
        """Returns a conversation with the given key; creates it if it
        doesn't exist.
        """
        
        try:
            convo = self.cb.conversations[key]
        except (TypeError, KeyError):
            # cb.conversations is None type, can't subscript
            # or conversation does not exist for guild id
            convo = self.cb.conversation(key)
        
        return convo

    async def on_ready(self):
        """Connects to the database and syncs the command tree."""
        
        self.db = await aiosqlite.connect(self.dbname)
        await self.db.execute("CREATE TABLE IF NOT EXISTS guilds (guild_id INTEGER, channel_id INTEGER)")
        await self.db.commit()

        await self.tree.sync()
        
        response = self.cb.say("Hello!")
        print(response)
    
    async def on_message(self, msg: discord.Message):
        """Listens for messages in the channel set for the server then
        responds to the conversation.
        """
        await asyncio.sleep(1)  # Simulate bot "thinking" of response.

        query = f"SELECT channel_id FROM guilds WHERE guild_id = {msg.guild.id}"
        async with self.db.execute(query) as cursor:
            record = await cursor.fetchone()
        if (record is None
            or msg.channel.id != record[0]
            or msg.author == self.user):
            
            return
        
        convo = self.get_convo(str(msg.guild.id))
        response = convo.say(msg.content)
        
        async with msg.channel.typing():    # Simulate bot typing response.
            await asyncio.sleep(2)
        await msg.channel.send(response)

        self.cb.save(self.cbname)
    
    @discord.app_commands.guild_only()
    async def set_channel_callback(self, interaction: discord.Interaction):
        """Sets up the bot to work in the channel the command was run
        in. Creates a record if it does not exist.
        """
        
        query = f"SELECT * FROM guilds WHERE guild_id = {interaction.guild_id}"
        async with self.db.execute(query) as cursor:
            record = await cursor.fetchone()

        if record:
            await self.db.execute(f"UPDATE guilds SET channel_id = {interaction.channel_id} WHERE guild_id = {interaction.guild_id}")
        else:
            await self.db.execute(f"INSERT INTO guilds VALUES ({interaction.guild_id}, {interaction.channel_id})")
        await self.db.commit()

        await interaction.response.send_message("Channel Updated.", ephemeral=True)

    async def donate_callback(self, interaction: discord.Interaction):
        """Sends a link to the user that lets them donate to me."""        
        
        await interaction.response.send_message("Please consider supporting my creator at https://paypal.me/jhoernlein")
