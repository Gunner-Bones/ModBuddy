import gd
import time
import sys
import os
import json
from json_abs import *
from db import *
from cep import *
import discord
from discord.ext import commands

F_CONFIG = 'config'
F_SQL = 'modbuddy.sqlite'

intents = discord.Intents.default()
intents.members = True
bot_prefix = "!!"
client = commands.Bot(command_prefix=bot_prefix, intents=intents)
client.remove_command("help")
secret = j_value(F_CONFIG, 'secret')

gdclient = gd.Client()

database = None

# BACKEND
def loadDatabase():
	global database
	if os.path.exists(F_SQL):
		print("[db] Loading database...")
		database = LevelDatabase(F_SQL)
	else:
		print("[db] Creating new database...")
		database = LevelDatabase(F_SQL)
		database.create_tables()
	print("[db] Database ONLINE.")
	print("[db] Path=" + F_SQL)

# UTILITY
def localDiscordClient() -> commands.Bot:
	return client

def localDatabase() -> LevelDatabase:
	return database

# DISCORD.PY
@client.event
async def on_ready():
	print("[discord.py] Connecting...")
	await client.wait_until_ready()
	print("[discord.py] Bot ONLINE.")
	print("[discord.py] Name=" + client.user.name + ", ID=" + str(client.user.id))
	loadDatabase()

@client.command(pass_context=True)
async def linkmod(ctx, linkdid, linkuid):
	""" Links a Discord ID to an in-game ID. """
	# SCOPE: DB Admins
	if await pLink(ctx=ctx, database=database):
		if linkdid.isdigit():
			linkdid = int(linkdid)
			if linkuid.isdigit():
				linkuid = int(linkuid)
				discord_user = client.get_user(linkdid)
				if discord_user:
					gd_user = await gdclient.get_user(linkuid)
					if gd_user:
						resp = await database.new_user(uid=linkuid, did=linkdid)
						if resp:
							await response(ctx=ctx, react="SUCCESS", 
								dynamic="Discord user `" + str(linkdid) + "` (" + discord_user.name + ") linked to `" + \
								str(linkuid) + "` (" + gd_user.name + ")")
						else:
							await response(ctx=ctx, react="FAILED", dynamic="User already linked!")
					else:
						await response(ctx=ctx, react="FAILED", dynamic="No GD user found with ID `" + str(linkuid) + "`")
				else:
					await response(ctx=ctx, react="FAILED", dynamic="No Discord user found with ID `" + str(linkdid) + "`")
			else:
				await response(ctx=ctx, react='FAILED', dynamic="`GD User ID` parameter must be an ID!")
		else:
			await response(ctx=ctx, react='FAILED', dynamic="`Discord ID` parameter must be an ID!")
	else:
		await response(ctx=ctx, react="FAILED", static="PERM")

@client.command(pass_context=True)
async def request(ctx, reqlid):
	pass

try:
	client.run(secret)
except discord.errors.LoginFailure:
	print("[ERROR] Invalid Bot secret! Exiting in 5s.")
	time.sleep(5)
	sys.exit()