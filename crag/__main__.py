"""Runs the bot using the database and save file in argv."""

import asyncio
import os
import sys

from . import CragBot


crag = CragBot(sys.argv[1], sys.argv[2])
crag.load_cb()

crag.run(os.getenv("CRAGTOKEN"))
asyncio.run(crag.db.close())
