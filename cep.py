import gd
import discord
from discord.ext import commands
from db import *

gdclient = gd.Client()

# CONSTANTS
CHAR_SUCCESS = "✅"
CHAR_FAILED = "❌"

DUSERS_DBADMINS = ['172861416364179456']

DBPRELOAD_Users = [
	{
	'uID': 419346,
	'dID': 172861416364179456 ,
	'uName': 'GunnerBones',
	'uIsMod': 0
	},
	{
	'uID': 5151647,
	'dID': 193140036311449600,
	'uName': "Mooshhh",
	'uIsMod': 1
	}
	]

# ENUMERATIONS
async def response(ctx: commands.Context, react: str, static="", dynamic=""):
	""" Discord Bot responses. """
	r = {
		'SUCCESS': CHAR_SUCCESS,
		'FAILED': CHAR_FAILED
	}
	s = {
		'PERM_ADMIN': "You are not an Administrator of this server!",
		'PERM': "You do not have access to this command!"
	}
	await ctx.channel.send("**" + ctx.author.name + "**, " + (dynamic or s[static]))
	await ctx.message.add_reaction(r[react])

def embedLevel(level: gd.Level) -> discord.Embed:
	""" Converts a GD Level into a Discord Embed. """
	# RETURNS: discord.Embed
	pass

# PERMISSIONS
def pDiscordAdmin(ctx: commands.Context) -> bool:
	""" Returns True if Discord command user has Administrative privileges 
		in the server this command was executed. """
	# RETURNS: bool
	for member in ctx.guild.members:
		if str(member.id) == str(ctx.author.id):
			for role in member.roles:
				if role.permissions.administrator:
					return True
	return False

def pDBAdmin(did: int) -> bool:
	""" Returns True if Discord user has access to modifying the database. """
	# RETURNS: bool
	return str(did) in DUSERS_DBADMINS

async def pGDMod(ctx: commands.Context, database) -> bool:
	""" Returns True if Discord command user is a GD Moderator. """
	# RETURNS: bool
	uid = database.get_user_uid(int(ctx.author.id))
	if not uid:
		return False
	user = await gdclient.get_user(uid)
	user = await user.to_user()
	return user.is_mod()

async def pLink(ctx: commands.Context, database) -> bool:
	""" Returns True if Discord command user is a GD Moderator OR 
		they have access to modifying the databasse. """
	# RETURNS: bool
	dbadmin = pDBAdmin(int(ctx.author.id))
	if dbadmin:
		return True
	mod = await pGDMod(ctx, database)
	return mod
