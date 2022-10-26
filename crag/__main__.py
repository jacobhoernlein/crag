"""Runs the bot using the database and save file in argv."""

import os
import sys

from . import CragBot


crag = CragBot(sys.argv[1], sys.argv[2])
crag.run(os.getenv("CRAGTOKEN"))
