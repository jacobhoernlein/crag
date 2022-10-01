# crag

Crag is a discord chat bot that uses discord.py, cleverbot.py, and a sqlite3 database.

In order for the bot to work correctly, you must first make a save file titled 'crag.cleverbot'.
To do so, execute the python code below in the repo's root, inserting your Cleverbot API token as needed:

```
import cleverbot
cb = cleverbot.Cleverbot('YOUR_CLEVERBOT_API_TOKEN')
cb.save('crag.cleverbot')
```
