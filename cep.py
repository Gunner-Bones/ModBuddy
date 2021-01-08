import gd
import discord
import datetime
import asyncio
from discord.ext import commands
from db import *

gdclient = gd.Client()

# CONSTANTS
CHAR_SUCCESS = "✅"
CHAR_FAILED = "❌"
CHAR_BACK = "◀️"
CHAR_FORWARD = "▶️"
CHAR_STOP = "⏹️"
CHAR_ONE = "1️⃣"
CHAR_TWO = "2️⃣"
CHAR_THREE = "3️⃣"
CHAR_FOUR = "4️⃣"
CHAR_FIVE = "5️⃣"

EMOTE_RATING_NA ="<:na:795811083641946154>"
EMOTE_RATING_AUTO = "<:auto:795811083360665661>"
EMOTE_RATING_EASY = "<:easy:795811083624382514>"
EMOTE_RATING_NORMAL = "<:normal:795811083859787806>"
EMOTE_RATING_HARD = "<:hard:795811083431444553>"
EMOTE_RATING_HARDER = "<:harder:795811083889147914>"
EMOTE_RATING_INSANE = "<:insane:795811083440095284>"
EMOTE_RATING_DEMON_EASY = "<:demon_easy:795811083415584798>"
EMOTE_RATING_DEMON_MEDIUM ="<:demon_medium:795811083737890846>"
EMOTE_RATING_DEMON_HARD = "<:demon_hard:795811083880759306>"
EMOTE_RATING_DEMON_INSANE ="<:demon_insane:795811083306795009>"
EMOTE_RATING_DEMON_EXTREME ="<:demon_extreme:795811083603410975>"
COLOR_RATING_NA = 0xAAAAAA
COLOR_RATING_AUTO = 0xFFCC66
COLOR_RATING_EASY = 0x00BBFF
COLOR_RATING_NORMAL = 0x00FF22
COLOR_RATING_HARD = 0xFFDD00
COLOR_RATING_HARDER = 0xFF5500
COLOR_RATING_INSANE = 0xFF66DD
COLOR_RATING_DEMON_EASY = 0x9944EE
COLOR_RATING_DEMON_MEDIUM = 0xDD33CC
COLOR_RATING_DEMON_HARD = 0xFF3344
COLOR_RATING_DEMON_INSANE = 0xEE2222
COLOR_RATING_DEMON_EXTREME = 0xAA0000
IMAGE_RATING_NA = "https://cdn.discordapp.com/attachments/795780617408479292/795784499216252958/na.png"
IMAGE_RATING_AUTO = "https://cdn.discordapp.com/attachments/795780617408479292/795784485970378812/auto.png"
IMAGE_RATING_EASY = "https://cdn.discordapp.com/attachments/795780617408479292/795784474511278110/easy.png"
IMAGE_RATING_NORMAL = "https://cdn.discordapp.com/attachments/795780617408479292/795784459076632586/normal.png"
IMAGE_RATING_HARD = "https://cdn.discordapp.com/attachments/795780617408479292/795784432602185748/hard.png"
IMAGE_RATING_HARDER = "https://cdn.discordapp.com/attachments/795780617408479292/795784417766539294/harder.png"
IMAGE_RATING_INSANE = "https://cdn.discordapp.com/attachments/795780617408479292/795784405959442452/insane.png"
IMAGE_RATING_DEMON_EASY = "https://cdn.discordapp.com/attachments/795780617408479292/795784387283124254/demon_easy.png"
IMAGE_RATING_DEMON_MEDIUM = "https://cdn.discordapp.com/attachments/795780617408479292/795784377246285864/demon_medium.png"
IMAGE_RATING_DEMON_HARD = "https://cdn.discordapp.com/attachments/795780617408479292/795784366508212244/demon_hard.png"
IMAGE_RATING_DEMON_INSANE = "https://cdn.discordapp.com/attachments/795780617408479292/795784340243873822/demon_insane.png"
IMAGE_RATING_DEMON_EXTREME = "https://cdn.discordapp.com/attachments/795780617408479292/795780666829701121/demon_extreme.png"
IMAGE_STATUS_RATED_NORMAL = "https://cdn.discordapp.com/attachments/795780617408479292/795788008628158515/rated_normal.png"
IMAGE_STATUS_RATED_DEMON = "https://cdn.discordapp.com/attachments/795780617408479292/795788030728339516/rated_demon.png"
IMAGE_STATUS_NOT_RATED = "https://cdn.discordapp.com/attachments/795780617408479292/795788039238320198/not_rated.png"

DUSERS_DBADMINS = [172861416364179456]

DBPRELOAD_Users = [
	#{
	#'uID': 419346,
	#'dID': 172861416364179456 ,
	#'uName': 'GunnerBones',
	#'uIsMod': 0
	#},
	{
	'uID': 5151647,
	'dID': 193140036311449600,
	'uName': "Mooshhh",
	'uIsMod': 1
	}
	]
DBPRELOAD_Levels = [ # first dozen random magic levels I found lol
	{
	'lID': 66280253,
	'lName': "Back on Past"
	},
	{
	'lID': 66279859,
	'lName': "Place On Fire"
	},
	{
	'lID': 66278041,
	'lName': "PURITY"
	},
	{
	'lID': 66276680,
	'lName': "Insurrection"
	},
	{
	'lID': 66274814,
	'lName': "Downward Dog"
	},
	{
	'lID': 66273244,
	'lName': "Magic Bounce"
	},
	{
	'lID': 66273220,
	'lName': "Electricity"
	},
	{
	'lID': 66271329,
	'lName': "Multiplayer mode II"
	},
	{
	'lID': 66268977,
	'lName': "Ferfette"
	},
	{
	'lID': 66267175,
	'lName': "Skull"
	},
	{
	'lID': 66265322,
	'lName': "Q"
	},
	{
	'lID': 66259721,
	'lName': "MECHANICAL FORCE"
	},
	{
	'lID': 66257000,
	'lName': "Eli IV"
	}
]

DBDEFAULT_ServerSettings = {
	'requests': True,
	'allowedChannels': [],
	'allowedRoles': [],
	'requestCooldown': 3600
	}

# ENUMERATIONS
def StrToListInts(data: str) -> list:
	""" Converts a string to a list of integers. """
	# RETURNS: list<int>
	if data.replace(" ","") == "[]":
		return []
	return [int(entry) for entry in data.replace("[","").replace("]","").replace(" ","").split(",")]

def UNIXToDatetime(unx: int) -> datetime.datetime:
	""" Converts a UNIX timestamp int to a datetime.datetime object. """
	# RETURNS: datetime.datetime
	return datetime.datetime.fromtimestamp(unx)

def DatetimeToRelative(dt=None, dtt=None) -> str:
	""" Formats a datetime.datetime object to relative time. """
	# RETURNS: str
	# I'd like to give a standing ovation to the makers of the datetime
	# library for having timedelta only include seconds and days :D
	dlt = None
	if dt:
		now = datetime.datetime.now()
		dlt = now - dt
	elif dtt:
		dlt = dtt
	else:
		return ""
	s = "s ago"
	if dlt.seconds < 60:
		if dlt.seconds == 1:
			s = " ago"
		return str(dlt.seconds) + " second" + s
	if dlt.seconds < 3600:
		if 120 > dlt.seconds >= 60:
			s = " ago"
		return str(int(dlt.seconds / 60)) + " minute" + s
	if dlt.days == 0:
		if 7200 > dlt.seconds >= 3600:
			s = " ago"
		return str(int(dlt.seconds / 3600)) + " hour" + s
	if dlt.days == 1:
		return "Yesterday"
	if dlt.days < 7:
		if dlt.days == 1:
			s = " ago"
		return str(dlt.days) + " day" + s
	if 14 > dlt.days >= 7:
		return "Last week"
	if dlt.days < 30:
		return str(int(dlt.days / 7)) + " weeks ago"
	if 60 > dlt.days >= 30:
		return "Last month"
	return "Months ago"

def eGDDifficulty(diff: int, dmn=0) -> str:
	""" Enumeration for GD API Level Difficulty. """
	# RETURNS: str
	normal = {
		0: 'na',
		-1: 'na',
		-3: 'auto',
		1: 'easy',
		2: 'normal',
		3: 'hard',
		4: 'harder',
		5: 'insane',
		-2: 'demon'
	}
	demon = {
		0: 'demon',
		-1: 'demon',
		1: 'demon_easy',
		2: 'demon_medium',
		3: 'demon_hard',
		4: 'demon_insane',
		5: 'demon_extreme'
	}
	if diff not in normal.keys():
		return None
	if diff == -2:
		if dmn not in demon.keys():
			return None
		return demon[dmn]
	return normal[diff]

def eGDLength(lng: int) -> str:
	""" Enumeration for GD API Level Length. """
	# RETURNS: str
	atr = {
		-1: 'nA',
		0: 'tiny',
		1: 'short',
		2: 'medium',
		3: 'long',
		4: 'xL'
	}
	if lng not in atr.keys():
		return None
	return atr[lng]

def eRatingsToImage(inp: str) -> str:
	""" Enumeration for Level Difficulty and Rating icons. """
	# RETURNS: str
	atr = {
		'na': IMAGE_RATING_NA,
		'auto': IMAGE_RATING_AUTO,
		'easy': IMAGE_RATING_EASY,
		'normal': IMAGE_RATING_NORMAL,
		'hard': IMAGE_RATING_HARD,
		'harder': IMAGE_RATING_HARDER,
		'insane': IMAGE_RATING_INSANE,
		'demon': IMAGE_RATING_DEMON_HARD,
		'demon_easy': IMAGE_RATING_DEMON_EASY,
		'demon_medium': IMAGE_RATING_DEMON_MEDIUM,
		'demon_hard': IMAGE_RATING_DEMON_HARD,
		'demon_insane': IMAGE_RATING_DEMON_INSANE,
		'demon_extreme': IMAGE_RATING_DEMON_EXTREME,
		'rated_normal': IMAGE_STATUS_RATED_NORMAL,
		'rated_demon': IMAGE_STATUS_RATED_DEMON,
		'not_rated': IMAGE_STATUS_NOT_RATED
	}
	if inp not in atr.keys():
		return None
	return atr[inp]

def eRatingsToColor(inp: str) -> int:
	""" Enumeration for Level Difficulty colors. """
	# RETURNS: int (Hex)
	atr = {
		'na': COLOR_RATING_NA,
		'auto': COLOR_RATING_AUTO,
		'easy': COLOR_RATING_EASY,
		'normal': COLOR_RATING_NORMAL,
		'hard': COLOR_RATING_HARD,
		'harder': COLOR_RATING_HARDER,
		'insane': COLOR_RATING_INSANE,
		'demon': COLOR_RATING_DEMON_HARD,
		'demon_easy': COLOR_RATING_DEMON_EASY,
		'demon_medium': COLOR_RATING_DEMON_MEDIUM,
		'demon_hard': COLOR_RATING_DEMON_HARD,
		'demon_insane': COLOR_RATING_DEMON_INSANE,
		'demon_extreme': COLOR_RATING_DEMON_EXTREME
	}
	if inp not in atr.keys():
		return None
	return atr[inp]

def eRatingsToEmote(inp: str) -> str:
	""" Enumeration for Level Difficulty emotes. """
	# RETURNS: str (Emote)
	atr = {
		'na': EMOTE_RATING_NA,
		'auto': EMOTE_RATING_AUTO,
		'easy': EMOTE_RATING_EASY,
		'normal': EMOTE_RATING_NORMAL,
		'hard': EMOTE_RATING_HARD,
		'harder': EMOTE_RATING_HARDER,
		'insane': EMOTE_RATING_INSANE,
		'demon': EMOTE_RATING_DEMON_HARD,
		'demon_easy': EMOTE_RATING_DEMON_EASY,
		'demon_medium': EMOTE_RATING_DEMON_MEDIUM,
		'demon_hard': EMOTE_RATING_DEMON_HARD,
		'demon_insane': EMOTE_RATING_DEMON_INSANE,
		'demon_extreme': EMOTE_RATING_DEMON_EXTREME
	}
	if inp not in atr.keys():
		return None
	return atr[inp]

def eNumberToEmote(inp: int) -> str:
	""" Enumeration for Number emotes. """
	# RETURNS: str (Emote)
	atr = {
		1: CHAR_ONE,
		2: CHAR_TWO,
		3: CHAR_THREE,
		4: CHAR_FOUR,
		5: CHAR_FIVE
	}
	if inp not in atr.keys():
		return None
	return atr[inp]

def eEmoteToNumber(inp: str) -> int:
	""" Enumeration for Numbers from Emotes. """
	# RETURNS: int
	atr = {
		CHAR_ONE: 1,
		CHAR_TWO: 2,
		CHAR_THREE: 3,
		CHAR_FOUR: 4,
		CHAR_FIVE: 5
	}
	if inp not in atr.keys():
		return None
	return atr[inp]

async def discordRemoveAllReactions(message):
	""" Removes all Reactions on a Message. """
	for reaction in message.reactions:
		await reaction.clear()

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

async def paginate(client, ctx: commands.Context, inp: list, t: str, dsc: bool, sb: str):
	""" Discord Bot list of paginatable objects. Limit 5 objects per page. """
	# RETURNS: int (Specific to Embed context)
	fields = formatEmbedsForPagination(inp=inp, t=t, sb=sb)
	fields = sorted(fields, key = lambda k: k['sort'], reverse=dsc)
	embeds = []
	temp_embed = discord.Embed(title="Results")
	temp_objs = []
	page = 1
	counter = 1
	for obj in fields:
		num_emote = eNumberToEmote(counter)
		temp_embed.add_field(name=num_emote + obj['name'], value=obj['value'], inline=False)
		temp_objs.append(obj['obj'])
		counter += 1
		if counter == 6:
			pagembed = {
				'embed': temp_embed,
				'page': page,
				'items': counter - 1,
				'objs': temp_objs
			}
			embeds.append(pagembed)
			temp_embed = discord.Embed(title="Results")
			temp_objs = []
			counter = 1
			page += 1
	if temp_objs:
		pagembed = {
				'embed': temp_embed,
				'page': page,
				'items': counter - 1,
				'objs': temp_objs
			}
		embeds.append(pagembed)
	for embed in embeds:
		embed['embed'].set_footer(text="Page " + str(embed['page']) + " of " + str(page))
	embeds = sorted(embeds, key = lambda e: e['page'])

	choice = 0
	allowed = [
		CHAR_ONE,
		CHAR_TWO,
		CHAR_THREE,
		CHAR_FOUR,
		CHAR_FIVE,
		CHAR_STOP,
		CHAR_FORWARD,
		CHAR_BACK
	]
	current_page = 0
	def check(reaction, user):
		return user.id == ctx.author.id and str(reaction.emoji) in allowed
	message = await ctx.send(embed=embeds[current_page]['embed'])
	while True:
		for num in range(1, embeds[current_page]['items'] + 1):
			await message.add_reaction(eNumberToEmote(num))
		if current_page > 0:
			await message.add_reaction(CHAR_BACK)
		if current_page < len(embeds) - 1:
			await message.add_reaction(CHAR_FORWARD)
		await message.add_reaction(CHAR_STOP)
		try:
			reaction, user = await client.wait_for('reaction_add', timeout=30.0, check=check)
		except asyncio.TimeoutError:
			await message.clear_reactions()
			break
		else:
			await message.clear_reactions()
			resp = str(reaction.emoji)
			if resp == CHAR_STOP:
				break
			if resp == CHAR_FORWARD or resp == CHAR_BACK:
				if resp == CHAR_FORWARD:
					current_page += 1
				elif resp == CHAR_BACK:
					current_page -= 1
				await message.edit(embed=embeds[current_page]['embed'])
				continue
			if resp in [CHAR_ONE, CHAR_TWO, CHAR_THREE, CHAR_FOUR, CHAR_FIVE]:
				resp_num = eEmoteToNumber(resp)
				if resp_num > embeds[current_page]['items']:
					continue
				choice = embeds[current_page]['objs'][resp_num - 1].id
				break
	return choice


def embedLevel(level) -> discord.Embed:
	""" Converts a MMLevel into a Discord Embed. """
	# RETURNS: discord.Embed
	eRating = "NOT RATED"
	eDifficulty = eGDDifficulty(diff=level.difficulty, dmn=level.demon)
	thumbnail = IMAGE_STATUS_NOT_RATED
	if level.isRated:
		eRating = "RATED"
		thumbnail = IMAGE_STATUS_RATED_NORMAL
		if level.demon != 0:
			eRating = "RATED DEMON"
			thumbnail = IMAGE_STATUS_RATED_DEMON
	embed = discord.Embed(title="ID: " + str(level.id), description="This level is " + eRating, 
		color=eRatingsToColor(eDifficulty))
	embed.set_author(name=level.name + " by " + level.author, icon_url=eRatingsToImage(eDifficulty))
	embed.set_thumbnail(url=thumbnail)
	embed.add_field(name="Length", value=eGDLength(level.length).capitalize(), inline=True)
	embed.add_field(name="Requested Stars", value=str(level.rqs), inline=True)
	return embed

def formatEmbedsForPagination(inp: list, t: str, sb: str) -> list:
	""" Converts a list of objects into a list of embeddable fields. """
	# RETURNS: list<dict>
	func = {
		'level': peLevel
	}
	return [func[t](obj, sb) for obj in inp]

def peLevel(level, sb: str) -> dict:
	""" Converts a MMLevel into a Discord Embed Fields dict used for pagination. """
	# RETURNS: dict (Fields)
	lastRequest = DatetimeToRelative(dt=UNIXToDatetime(level.lastrq))
	timesRequested = str(level.timesrq)
	timesSent = str(level.timessent)
	sort_by = {
		'recent': level.lastrq,
		'times_rq': level.timesrq,
		'times_sent': level.timessent
	}
	diffIcon = eRatingsToEmote(eGDDifficulty(diff=level.difficulty, dmn=level.demon))
	d = {
		'obj': level,
		'sort': sort_by[sb],
		'name': diffIcon + " " + level.name + " by " + level.author,
		'value': 'Last Request: ' + lastRequest + " | Times Requested: " + timesRequested + " | Times Sent: " + timesSent
	}
	return d

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
	return did in DUSERS_DBADMINS

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
