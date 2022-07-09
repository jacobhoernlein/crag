import os

import discord
from cleverbotfreeapi import cleverbot

crag = discord.Client()

@crag.event
async def on_message(msg:discord.Message):
    if msg.channel.id == 994482057336074341 and msg.author.id != 994430080275206184:
        response = cleverbot(msg.content, session="cragbot2022")
        await msg.channel.send(response)
    
@crag.event
async def on_ready():
    print("crag.")

crag.run(os.getenv('BOTTOKEN'))
