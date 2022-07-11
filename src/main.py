import os
import asyncio

import discord


class CragBot(discord.Client):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.channel = None

    async def on_ready(self):
        self.channel = await self.fetch_channel('994482057336074341')
        print("crag.")


async def send_messages(bot:CragBot):
    await bot.login(os.getenv('BOTTOKEN'))
    channel = await bot.fetch_channel('994482057336074341')

    while True:
        try:
            message = input("> ")
        except KeyboardInterrupt:
            await bot.close()
            break
        else:
            await channel.send(message)
    
if __name__ == '__main__':
    crag = CragBot(intents=discord.Intents.all())

    mode = input("Select mode. 1) Cleverbot, 2) DMs, 3) Terminal: ")

    # Auto Mode. Uses Cleverbot API.
    if int(mode) == 1:
        from cleverbot import async_ as cleverbot
        cb = cleverbot.load('cleverbot.crag')
        
        @crag.event
        async def on_message(msg:discord.Message):
            if str(msg.channel.id) == '994482057336074341' \
            and str(msg.author.id) != '994430080275206184':
                response = await cb.say(msg.content)
                cb.save('cleverbot.crag')
                await msg.channel.send(response)

        crag.run(os.getenv('BOTTOKEN'))
        asyncio.run(cb.close())

    # Manual Mode. Uses Jacob's DMs.
    elif int(mode) == 2:
        @crag.event
        async def on_message(msg:discord.Message):
            if msg.channel.type == discord.ChannelType.private \
            and str(msg.author.id) == '243845903146811393':
                await crag.channel.send(msg.content)

        crag.run(os.getenv('BOTTOKEN'))

    # Terminal Mode. Does not show bot as Online.
    elif int(mode) == 3:
        asyncio.run(send_messages(crag))
