import os
import asyncio
import threading

import discord
from cleverbotfreeapi import cleverbot

crag = discord.Client()

def auto():
    @crag.event
    async def on_message(msg:discord.Message):
        if msg.channel.id == 994482057336074341 and msg.author.id != 994430080275206184:
            response = cleverbot(msg.content, session="cragbot2022")
            await msg.channel.send(response)
        
    @crag.event
    async def on_ready():
        print("crag.")

    crag.run(os.getenv('BOTTOKEN'))

async def manual():
    await crag.login(os.getenv('BOTTOKEN'))
    channel = await crag.fetch_channel('994482057336074341')
    
    while True:
        try:
            message = input("> ")
        except KeyboardInterrupt:
            await crag.close()
            exit()
        else:
            await channel.send(message)

if __name__ == '__main__':
    mode = input("Select mode. 1 = Auto, 2 = Manual: ")

    if int(mode) == 1:
        auto()
    elif int(mode) == 2:
        asyncio.run(manual())


