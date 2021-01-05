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
bot_prefix = "??"
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

	dft = DBDEFAULT_ServerSettings
	count = 0
	for guild in client.guilds:
		if database.new_server(stid=guild.id, stname=guild.name,
			requests=dft['requests'], allowedChannels=dft['allowedChannels'],
			allowedRoles=dft['allowedRoles'], requestCooldown=dft['requestCooldown']):
			count += 1
			print("[db] cep.py: New Server found: " + guild.name)
	if count:
		print("[db] cep.py: Generated DEFAULT ServerSettings for " + str(count) + " new Servers.")
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
	retry = 5
	while True:
		try:
			loadDatabase()
			break
		except sqlite3.OperationalError:
			if retry > 0:
				print("[WARNING] Database is locked. Retrying (" + str(retry) + ")...")
				retry -= 1
				time.sleep(1)
				continue
			else:
				print('[ERROR] Database could not be accessed. (Is someone modifying it?)')
				time.sleep(5)
				sys.exit()

@client.command(pass_context=True)
async def linkmod(ctx, linkdid, linkuid):
	""" Links a Discord ID to an in-game ID. """
	# SCOPE: DB Admins, GD Moderators
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
	""" Requests a Level. """
	# SCOPE: Anyone


@client.command(pass_context=True)
async def debug_request(ctx, reqlid):
	""" Debug command for Requesting. """
	# SCOPE: DB Admins, GD Moderators
	if await pLink(ctx=ctx, database=database):
		reqlid = int(reqlid)
		level = await database.new_level(reqlid)
		if level:
			await response(ctx=ctx, react="SUCCESS", dynamic="Level added.")
			await ctx.send(embed=embedLevel(level))
		else:
			await response(ctx=ctx, react="FAILED", dynamic="Could not add level.")

try:
	client.run(secret)
except discord.errors.LoginFailure:
	print("[ERROR] Invalid Bot secret! Exiting in 5s.")
	time.sleep(5)
	sys.exit()