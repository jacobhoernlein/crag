import os
import cleverbot

cb = cleverbot.Cleverbot(os.getenv('CLEVERBOTAPITOKEN'))
cb.save('crag.cleverbot')
