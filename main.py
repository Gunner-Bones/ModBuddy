import gd
import time
import sys
import json
from json_abs import *
import db
import discord
from discord.ext import commands

CHAR_SUCCESS = "✅"
CHAR_FAILED = "❌"
F_CONFIG = 'config.json'

intents = discord.Intents.default()
intents.members = True
bot_prefix = "!!"
client = commands.Bot(command_prefix=bot_prefix, intents=intents)
client.remove_command("help")
secret = j_value(F_CONFIG, 'secret')

client.event
async def on_ready():
	print("[discord.py] Connecting...")
	await client.wait_until_ready()
	print("[discord.py] Bot ONLINE.")
	print("[discord.py] Name=" + client.user.name + ", ID=" + str(client.user.id))


try:
	client.run(BOT_SECRET)
except discord.errors.LoginFailure:
	print("[ERROR] Invalid BOT_SECRET! Exiting in 5s.")
	time.sleep(5)
	sys.exit()