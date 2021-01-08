import gd
import time
import datetime
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

	count = 0
	for guild in client.guilds:
		if database.generate_default_server(stid=guild.id, stname=guild.name):
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
	await database.preload_tables()

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
	if reqlid.isdigit():
		reqlid = int(reqlid)
		requester = database.get_requester(rdid=ctx.author.id, rname=ctx.author.name)
		server_settings = database.get_server(stid=ctx.guild.id, stname=ctx.guild.name)
		crq = server_settings.canRequest(ctx=ctx, rq=requester)
		request_cases = {
			1: "You are banned from requesting!",
			2: "Requests are disabled for this Server!",
			3: "You are not allowed to request in this Channel.",
			4: "You do not have the required Role(s) to request.",
			5: "Woah, slow down! You can request again in "
		}
		if not crq:
			rqr = database.requester_rq(rdid=ctx.author.id, lid=reqlid, rname=ctx.author.name)
			if not rqr:
				level = await database.new_level(lid=reqlid)
				if level:
					await response(ctx=ctx, react='SUCCESS', dynamic="Level REQUESTED!")
					await ctx.send(embed=embedLevel(level))
				else:
					await response(ctx=ctx, react='FAILED', dynamic="No GD Level found with ID `" + str(reqlid) + "`") 
			else:
				await response(ctx=ctx, react='FAILED', dynamic="You've already requested this level!")
		else:
			extra = ""
			if crq == 5:
				xtt = datetime.timedelta(seconds=server_settings.onCooldown(rq=requester))
				extra = "`" + DatetimeToRelative(dtt=xtt)[:-4] + "`"
			await response(ctx=ctx, react='FAILED', dynamic=request_cases[crq] + extra)
	else:
		await response(ctx=ctx, react='FAILED', dynamic="`Level ID` parameter must be an ID!")


@client.command(pass_context=True)
async def check_requests_new(ctx):
	""" Checks requested levels by recently-added. """
	# SCOPE: DB Admin, GD Moderators
	if await pLink(ctx=ctx, database=database):
		all_levels = database.get_all_levels()
		choice = await paginate(client=client, ctx=ctx, 
			inp=all_levels, t='level', dsc=True, sb='recent')
		if choice:
			level = database.get_level(lid=choice)
			if level:
				await ctx.send(embed=embedLevel(level))
			else:
				await response(ctx=ctx, react='FAILED', dynamic="No GD Level found with ID `" + str(reqlid) + "`") 
	else:
		await response(ctx=ctx, react='FAILED', static='PERM')


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

@client.command(pass_context=True)
async def debug_test(ctx):
	if pDBAdmin(ctx.author.id):
		await ctx.send(":one:")

try:
	client.run(secret)
except discord.errors.LoginFailure:
	print("[ERROR] Invalid Bot secret! Exiting in 5s.")
	time.sleep(5)
	sys.exit()