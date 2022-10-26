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
                description="Set Crag's channel to this one.",
                callback=self.set_channel_callback))
        self.tree.add_command(
            discord.app_commands.Command(
                name="donate",
                description="Support Crag's creator (he is broke).",
                callback=self.donate_callback))

        self.__dbname = dbname
        self.__cbname = cbname
        self.db: aiosqlite.Connection = None
        self.cb: cleverbot.Cleverbot = None

    def run(self, token: str):
        
        try:
            self.cb = cleverbot.load(self.__cbname)
            self.cb.say()
        except (FileNotFoundError, cleverbot.APIError):
            print("ERROR: Couldn't load Cleverbot file. ", end=None)
            while True:
                token = input("Enter your Cleverbot API token: ")
                self.cb = cleverbot.Cleverbot(token)
                try:
                    self.cb.say()
                except cleverbot.APIError:
                    print("Invalid API key. Try again. ", end=None)
                else:
                    self.cb.save(self.__cbname)
                    break
        
        super().run(token)
        
        asyncio.run(self.db.close())
        self.cb.save(self.__cbname)

    async def on_ready(self):
        """Connects to the database and syncs the command tree."""
        
        self.db = await aiosqlite.connect(self.__dbname)
        query = """
            CREATE TABLE IF NOT EXISTS guilds (
                guild_id INTEGER,
                channel_id INTEGER)"""
        await self.db.execute(query)
        await self.db.commit()

        await self.tree.sync()
        
        response = self.cb.say("Hello!")
        print(response)

    async def on_message(self, msg: discord.Message):
        """Listens for messages in the channel set for the server then
        responds to the conversation.
        """
        await asyncio.sleep(1)  # Simulate bot "thinking" of response.

        query = f"""
            SELECT channel_id 
            FROM guilds 
            WHERE guild_id = {msg.guild.id}"""
        async with self.db.execute(query) as cursor:
            row = await cursor.fetchone()
        if (row is None
            or msg.channel.id != row[0]
            or msg.author == self.user):
            
            return
        
        try:
            convo = self.cb.conversations[str(msg.guild.id)]
        except (TypeError, KeyError):
            # cb.conversations is None type, can't subscript
            # or conversation does not exist for guild id
            convo = self.cb.conversation(str(msg.guild.id))
        response = convo.say(msg.content)
        
        async with msg.channel.typing():    # Simulate bot typing response.
            await asyncio.sleep(2)
        await msg.channel.send(response)
    
    @discord.app_commands.guild_only()
    async def set_channel_callback(self, interaction: discord.Interaction):
        """Sets up the bot to work in the channel the command was run
        in. Creates a record if it does not exist.
        """
        
        query = f"""
            SELECT *
            FROM guilds
            WHERE guild_id = {interaction.guild_id}"""
        async with self.db.execute(query) as cursor:
            row = await cursor.fetchone()

        if row:
            query = f"""
                UPDATE guilds
                SET channel_id = {interaction.channel_id}
                WHERE guild_id = {interaction.guild_id}"""
        else:
            query = f"""
                INSERT INTO guilds
                VALUES (
                    {interaction.guild_id},
                    {interaction.channel_id})"""
        await self.db.execute(query)
        await self.db.commit()

        await interaction.response.send_message(
            content="Channel Updated.", ephemeral=True)

    async def donate_callback(self, interaction: discord.Interaction):
        """Sends a link to the user that lets them donate to me."""        
        
        await interaction.response.send_message(
            "Please consider supporting my creator at https://paypal.me/jhoernlein")
