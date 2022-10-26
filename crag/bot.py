"""A simple bot that uses the cleverbot module to create a chat bot.
Uses a sqlite database for multi-server support.

Version 2.
"""

import asyncio

import aiosqlite
import cleverbot
import discord
from discord.ext import commands


class SetChannelCommand(discord.app_commands.Command):
    """Configures Crag to run in the channel the command was run in."""

    def __init__(self, bot: "CragBot", *args, **kwargs):
        super().__init__(
            name="setchannel",
            description="Set Crag's channel to this one.",
            callback=self.callback, *args, **kwargs)
        self.on_error = self.error
        self.bot = bot

    @discord.app_commands.guild_only()
    @discord.app_commands.checks.has_permissions(administrator=True)
    async def callback(self, interaction: discord.Interaction):
        
        query = f"""
            SELECT *
            FROM guilds
            WHERE guild_id = {interaction.guild_id}"""
        async with self.bot.db.execute(query) as cursor:
            row = await cursor.fetchone()
        # Checks to see if the Guild has a configured channel.
        if row is not None:
            # Updates it if there is one.
            query = f"""
                UPDATE guilds
                SET channel_id = {interaction.channel_id}
                WHERE guild_id = {interaction.guild_id}"""
        else:
            # Adds one if there isn't.
            query = f"""
                INSERT INTO guilds
                VALUES (
                    {interaction.guild_id},
                    {interaction.channel_id})"""
        await self.bot.db.execute(query)
        await self.bot.db.commit()

        await interaction.response.send_message(
            content="Channel Updated.", ephemeral=True)

    async def error(
            self, _, interaction: discord.Interaction,
            error: discord.app_commands.AppCommandError):
        if isinstance(error, discord.app_commands.MissingPermissions):
            await interaction.response.send_message(
                "You must be a server administrator to set Crag's channel.",
                ephemeral=True)
        else:
            raise error


class DonateCommand(discord.app_commands.Command):
    """Sends a link to the user that lets them donate to me."""

    def __init__(self, *args, **kwargs):
        super().__init__(
            name="donate",
            description="Support Crag's creator (he is broke).",
            callback=self.callback, *args, **kwargs)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_message(
            "Please consider supporting my creator at https://paypal.me/jhoernlein")


class CragBot(commands.Bot):
    """Subclassed commands.Bot that includes database and cleverbot API
    connections, and talks to users in a specified channel.
    """

    def __init__(self, dbname: str, cbname: str):
        super().__init__(
            command_prefix="NO PREFIX",
            help_command=None,
            intents=discord.Intents.all(),
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name="for /setchannel"))

        self.tree.add_command(SetChannelCommand(self))
        self.tree.add_command(DonateCommand())

        self.__dbname = dbname
        self.__cbname = cbname
        self.db: aiosqlite.Connection = None
        self.cb: cleverbot.Cleverbot = None

    def run(self, token: str):
        # Does the same as the superclass's .run() method, but includes
        # neccessary setups and cleanups for the bot to work.

        try:
            # Tries to load the given file. If that works, queries the
            # API to make sure the token is correct.
            self.cb = cleverbot.load(self.__cbname)
            self.cb.say()
        except (FileNotFoundError, cleverbot.APIError):
            # If the file wasn't found or something was wrong with the
            # file (wrong token), prompts user for the right one.
            print("ERROR: Couldn't load Cleverbot file. ", end=None)
            while True:
                # Keeps prompting until a valid token is found.
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
        
        # Closes the aiosqlite.Connection and saves the
        # cleverbot.Cleverbot state to the cb file.
        asyncio.run(self.db.close())
        self.cb.save(self.__cbname)

    async def on_ready(self):
        # Does some setup that can only be done once within the
        # event loop, then confirms once connected.

        # Connects to the database and creates the needed tables
        # if they don't already exist.
        self.db = await aiosqlite.connect(self.__dbname)
        query = """
            CREATE TABLE IF NOT EXISTS guilds (
                guild_id INTEGER,
                channel_id INTEGER)"""
        await self.db.execute(query)
        await self.db.commit()

        # Adds a loop to the bot to make it save the cleverbot
        # state every 2.5 minutes.
        async def save_loop():
            while not self.is_closed():
                self.cb.save(self.__cbname)
                await asyncio.sleep(150)
        self.loop.create_task(save_loop())
        
        await self.tree.sync()

        response = self.cb.say("Hello!")
        print(response)

    async def on_message(self, msg: discord.Message):
        # Replies to messages in configured channels.

        if msg.author == self.user:
            return

        query = f"""
            SELECT channel_id 
            FROM guilds 
            WHERE guild_id = {msg.guild.id}"""
        async with self.db.execute(query) as cursor:
            row = await cursor.fetchone()
        if row is None or msg.channel.id != row[0]:
            return
        
        try:
            # Tries to get the Guild's conversation from the
            # Cleverbot's conversation dictionary.
            convo = self.cb.conversations[str(msg.guild.id)]
        except (TypeError, KeyError):
            # Creates a new one if it does not exist or if 
            # the dictionary is empty.
            convo = self.cb.conversation(str(msg.guild.id))
        response = convo.say(msg.content)
        
        await asyncio.sleep(1)              # Simulate bot "thinking" of response.
        async with msg.channel.typing():    # Simulate bot typing response.
            await asyncio.sleep(2)
        await msg.channel.send(response)
    