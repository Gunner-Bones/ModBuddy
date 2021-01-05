import sqlite3
import time
from json_abs import *
from cep import *
import gd
import discord
from discord.ext import commands

client = gd.Client()

class MMLevel:

	def __init__(self, lID: int, lName="", lAuthor="", lDifficulty=0, lDemon=0, lLength=-2, lRqS=-1, lIsRated=False):
		""" Object for Levels in-game."""
		self.id = lID
		self.name = lName
		self.author = lAuthor
		self.difficulty = lDifficulty
		self.demon = lDemon
		self.length = lLength
		self.rqs = lRqS
		self.isRated = lIsRated

	async def generate(self):
		""" Fill all empty 'l' attributes from ID. """
		level = await client.get_level(self.id)
		self.name = level.name
		self.author = level.creator.name
		if level.is_demon():
			self.difficulty = -2
			self.demon = level.difficulty.value
		else:
			self.difficulty = level.difficulty.value
			self.demon = 0
		self.length = level.length.value
		self.rqs = level.requested_stars
		self.isRated = level.is_rated()


class MMUser:

	def __init__(self, uID: int, dID: int, uName="", uIsMod=0):
		""" Object for Users in Discord and in-game. """
		self.uid = uID
		self.did = dID
		self.name = uName
		self.isMod = uIsMod

	async def generate(self):
		""" Fill all empty 'u' attributes from ID. """
		user = await client.get_user(self.uid)
		self.name = user.name
		self.isMod = 0
		nuser = await user.to_user()
		if nuser.is_mod():
			self.isMod = 1
			if nuser.is_mod('elder'):
				self.isMod = 2


class MMRequestUser:

	def __init__(self, rdID: int, rName: str, banned: bool, requestLast: int):
		""" Object for Requesting Users in Discord. """
		self.id = rdID
		self.name = rName
		self.banned = banned
		self.rqLast = requestLast


class MMServerSettings:

	def __init__(self, stID: int, stName: str, requests: bool, 
		allowedChannels: list, allowedRoles: list, requestCooldown: int):
		""" Object for Server Settings in Discord. """
		self.id = stID
		self.name = stName
		self.requests = requests
		self.allowedChannels = allowedChannels
		self.allowedRoles = allowedRoles
		self.requestCooldown = requestCooldown

	def canRequest(self, ctx: commands.Context, rq: MMRequestUser):
		""" Checks if the Requesting User can request a new level in this Server. """
		# RETURNS: int (0=User can request, 1=User is banned, 2=Requests are not turned on,
		# 3=User is not in an allowed Channel, 4=User does not have an allowed Role,
		# 5=User is on request Cooldown
		if rq.banned:
			return 1
		if not self.requests:
			return 2
		if self.allowedChannels:
			if not any(allowed == ctx.channel.id for allowed in self.allowedChannels):
				return 3
		if self.allowedRoles:
			if not any(allowed in [role.id for role in ctx.author.roles] for allowed in self.allowedRoles):
				return 4
		if int(time.time()) < rq.rqLast + self.requestCooldown:
			return 5
		return 0

class LevelDatabase:
	
	def __init__(self, dbPath):
		""" Class for executing sqlite3 commands. """
		self.db = sqlite3.connect(dbPath, isolation_level=None)
		self.db.execute("PRAGMA foreign_keys = 1")

	def query_single_result(self, query, parameters):
		""" Execute a query for a single result. """
		# Author: MultipleMonomials

		cursor = self.db.execute(query, parameters)
		row = cursor.fetchone()

		if row is None or len(row) < 1:
			return None

		result = row[0]
		cursor.close()
		return result

	def query_multiple_results(self, query, parameters) -> tuple:
		""" Execute a query for multiple results. """
		cursor = self.db.execute(query, parameters)
		result = cursor.fetchall()
		if row is None or len(row) < 1:
			return None
		cursor.close()
		return result

	def create_tables(self):
		""" Loads tables from instructions. """
		self.db.execute("BEGIN")

		self.db.execute(
			"""
			CREATE TABLE Levels(
			/*
			Levels requested.
			-lID INTEGER: In-game Level ID.
			-lName TEXT, -lAuthor TEXT, -lDifficulty INTEGER, -lLength INTEGER,
			-lRqS INTEGER (Requested Stars), -lDemon INTEGER, and -lIsRated INTEGER (BOOL) are
			in-game level attributes.
			-isSent INTEGER: Number of times sent.
			-timesRequested INTEGER: Number of times requested.
			*/
			lID INTEGER PRIMARY KEY, 
			lName TEXT, 
			lAuthor TEXT, 
			lDifficulty INTEGER, 
			lDemon INTEGER,
			lLength INTEGER, 
			lRqS INTEGER, 
			lIsRated INTEGER, 
			isSent INTEGER ,
			timesRequested INTEGER
			)
			""")
		self.db.execute(
			"""
			CREATE TABLE Users(
			/*
			Users with linked Discord and in-game accounts.
			-uID INTEGER: User's in-game account ID.
			-dID INTEGER: User's Discord ID.
			-uName TEXT and -uIsMod INTEGER are in-game user attributes.
			*/
			uID INTEGER PRIMARY KEY, 
			dID INTEGER, 
			uName TEXT, 
			uIsMod INTEGER, 
			UNIQUE(uName) 
			)
			""")
		self.db.execute(
			"""
			CREATE TABLE SendHistory(
			/*
			Records of when a Moderator has sent a Level.
			-sID INTEGER: Record ID for sent level.
			-flID INTEGER and -fuID INTEGER are references.
			-sTime INTEGER (UNIX timestamp): Record creation time.
			*/
			sID INTEGER PRIMARY KEY AUTOINCREMENT, 
			flID INTEGER, 
			fuID INTEGER, 
			sTime INTEGER, 
			FOREIGN KEY(flID) REFERENCES Levels(lID), 
			FOREIGN KEY(fuID) REFERENCES Users(uID) 
			)
			""")
		self.db.execute(
			"""
			CREATE TABLE RequestUsers(
			/*
			Users who request Levels.
			-rdID INTEGER: User's Discord ID.
			-rName TEXT: User's Discord Name.
			-banned INTEGER (bool): If the user is banned from requesting.
			-requestLast INTEGER (UNIX timestamp): Most recent time user requested.
			*/
			rdID INTEGER PRIMARY KEY, 
			rName TEXT, 
			banned INTEGER, 
			requestLast INTEGER, 
			UNIQUE(rdID) 
			)
			""")
		self.db.execute(
			"""
			CREATE TABLE ServerSettings(
			/*
			Settings by Server pertaining requests.
			-stID INTEGER: Server's Discord ID.
			-stName TEXT: Server's Discord Name.
			-requests INTEGER (bool): If level requests are on for this server.
			-allowedChannels TEXT (list<int>): List of Discord Channels allowed 
			to request in. If empty, any Discord Channel is allowed.
			-allowedRoles TEXT (list<int>): List of Discord Roles a user needs
			one of to request. If empty, no Discord Roles required to request.
			-requestCooldown INTEGER (Minutes): Cooldown between requests.
			If 0, no cooldown.
			*/
			stID INTEGER PRIMARY KEY, 
			stName TEXT, 
			requests INTEGER, 
			allowedChannels TEXT, 
			allowedRoles TEXT, 
			requestCooldown INTEGER, 
			UNIQUE(stID)
			)
			""")
		self.db.commit()

		for user in DBPRELOAD_Users:
			mmu = MMUser(uID=user['uID'], dID=user['dID'], uName=user['uName'], uIsMod=user['uIsMod'])
			self.add_user(mmu)
		print('[db] cep.py: PRELOADED Users')

	# LEVELS
	def add_level(self, mml: MMLevel) -> bool:
		""" Adds MMLevel object to Levels table. """
		# RETURNS: bool (True if newly added, False if requested again)
		try:
			self.db.execute(
				"""
				INSERT INTO Levels(lID, lName, lAuthor, lDifficulty, lDemon, lLength, lRqS, lIsRated, isSent, timesRequested)
				VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
				""", 
				(mml.id, mml.name, mml.author, mml.difficulty, mml.demon, mml.length, mml.rqs, int(mml.isRated), 0, 1))
			return True
		except sqlite3.IntegrityError:
			self.db.execute(
				"""
				UPDATE Levels 
				SET timesRequested = timesRequested + 1
				WHERE lID = ? 
				""",
				(mml.lID,))
			return False

	def remove_level(self, lid: int):
		""" Removes MMLevel object from Levels table. """
		self.db.execute(
			"""
			DELETE FROM Levels 
			WHERE lID=?
			""",
			(lid,))

	def get_level(self, lid: int) -> MMLevel:
		""" Returns MMLevel object from Levels table. """
		# RETURNS: MMLevel
		t = self.query_single_result("SELECT * FROM Levels WHERE lID = ?", (lid,)) 
		if not t:
			return None
		return MMLevel(lID=t[0], lName=t[1], lAuthor=t[2], lDifficulty=t[3], 
			lDemon=t[4], lLength=t[5], lRqS=t[6], lIsRated=bool(t[7]))

	async def new_level(self, lid: int) -> MMLevel:
		""" Searches for level in-game with given ID and adds to Levels table. """
		# RETURNS: MMLevel
		mml = MMLevel(lID=lid)
		await mml.generate()
		if self.add_level(mml):
			return mml
		return None

	# USERS
	def add_user(self, mmu: MMUser) -> bool:
		""" Adds MMUser object to Users table. """
		# RETURNS: bool (User added successfully)
		try:
			self.db.execute(
				"""
				INSERT INTO Users(uID, dID, uName, uIsMod)
				VALUES(?, ?, ?, ?)
				""",
				(mmu.uid, mmu.did, mmu.name, mmu.isMod,))
			return True
		except sqlite3.IntegrityError:
			return False

	def remove_user(self, uid: int):
		""" Removes MMUser object from Users table. """
		self.db.execute(
			"""
			DELETE FROM Users
			WHERE uID=?
			""",
			(uid,))

	def get_user(self, *args, **kwds) -> MMUser:
		""" Returns MMUser object from Users table. """
		# Allowed ARGS: uID (int), dID (int)
		# RETURNS: MMUser
		if 'uID' not in args and 'dID' not in args:
			return None
		t = self.query_single_result("SELECT * FROM Users WHERE " + args[0] + " = ?", (kwds[args[0]],)) 
		return MMUser(uID=t[0], dID=t[1], uName=t[2], uIsMod=t[3])

	def get_user_uid(self, did: int) -> int:
		""" Returns user's in-game ID from Discord ID. """
		# RETURNS: int
		return self.query_single_result("SELECT uID from Users WHERE dID = ?", (did,))

	async def new_user(self, uid: int, did: int) -> bool:
		""" Searches for user in-game with given user ID and adds to Users table. """
		# RETURNS: bool (Level added successfully)
		mmu = MMUser(uID=uid, dID=did)
		await mmu.generate()
		return self.add_user(mmu)

	# SEND HISTORY
	def send(self, flid: int, fuid: int) -> int:
		""" Creates new SendHistory record from a level being sent. """
		# RETURNS: 0=Success, 1=flid not found in Levels, 2=fuid not found in Users, 3=User is not mod
		level = self.get_level(flid)
		if not level:
			return 1
		user = self.get_user(fuid)
		if not user:
			return 2
		if not user.isMod:
			return 3
		self.db.execute(
			"""
			INSERT INTO SendHistory(flID, fuID, sTime)
			VALUES(?, ?, ?)
			""",
			(flid, fuid, int(time.time()),))
		self.db.execute(
			"""
			UPDATE Levels 
			SET isSent = isSent + 1
			WHERE flID = ? 
			""",
			(flid,))
		return 0

	def get_sends_user(self, *args, **kwds) -> list:
		""" Finds levels a user has sent. """
		# Allowed ARGS: uID (int), dID (int)
		# RETURNS: list<MMLevel>
		allowed = ['uID', 'dID']
		if not any(a in args for a in allowed):
			return None
		kID = kwds[args[0]]
		if args[0] == 'dID':
			kID = get_user_uid(kID)

		leveldata = list(self.query_multiple_results(
			"""
			SELECT Levels.lID, Levels.lName, Levels.lAuthor, Levels.lDifficulty, Levels.lDemon, 
			Levels.lLength, Levels.lRqS, Levels.lIsRated
			FROM SendHistory
			INNER JOIN Levels ON Levels.lID = SendHistory.flID
			WHERE SendHistory.fuID = ?
			"""
			), (kID))
		return [MMLevel(lID=r[0], lName=r[1], lAuthor=r[2], lDifficulty=r[3], 
			lDemon=t[4], lLength=r[5], lRqS=r[6], lIsRated=r[7]) for r in leveldata]

	def get_sends_level(self, flid: int):
		""" Finds users who've sent this level. """
		# RETURNS: list<MMUser>
		userdata = list(self.query_multiple_results(
			"""
			SELECT Users.uID, Users.dID, Users.uName, Users.uIsMod
			FROM SendHistory
			INNER JOIN Users ON Users.uID = SendHistory.fuID
			WHERE SendHistory.flID = ?
			"""), (flid,))
		return [MMUser(uID=r[0], dID=r[1], uName=r[2], uIsMod=r[3]) for r in userdata]

	def get_sends_level_count(self, flid: int) -> int:
		""" Returns number of times a level was sent. """
		# RETURNS: int
		return self.query_single_result("SELECT isSent FROM Levels WHERE flID = ?", (flid,))

	# REQUEST USERS
	def add_requester(self, mmru: MMRequestUser) -> bool:
		""" Adds MMRequestUser object to RequestUsers table. """
		# RETURNS: bool (Request User added successfully)
		try:
			self.db.execute(
				"""
				INSERT INTO RequestUsers(rdID, rName, banned, requestLast)
				VALUES(?, ?, ?, ?)
				""",
				(mmru.id, mmru.name, mmru.banned, mmru.rqLast,))
			return True
		except sqlite3.IntegrityError:
			return False

	def remove_requester(self, rdid: int):
		""" Removes MMRequestUser object from RequestUsers table. """
		self.db.execute(
			"""
			DELETE FROM RequestUsers
			WHERE rdID=?
			""",
			(rdid,))

	def new_requester(self, rdid: int, rname: str) -> MMRequestUser:
		""" Generates new requester and adds to RequestUsers table. """
		# RETURNS: MMRequestUser
		mmru = MMRequestUser(rdID=rdid, rName=rname, banned=False, requestLast=0)
		if self.add_requester(mmru):
			return mmru
		return None

	def get_requester(self, rdid: int, rname="") -> MMRequestUser:
		""" Returns MMRequestUser object from RequestUsers table, generates if doesn't exist. """
		# RETURNS: MMRequestUser
		t = self.query_single_result("SELECT * FROM RequestUsers WHERE rdID = ?", (rdid,))
		if not t:
			return new_requester(rdid=rdid, rname=rname)
		return MMRequestUser(rdID=t[0], rName=r[1], banned=bool(r[2]), requestLast=r[3])

	def update_requester(self, rdid: int, *args, **kwds) -> bool:
		""" Updates attributes of a Request User. """
		# Allowed ARGS: banned (int), requestLast (int)
		# RETURNS: bool (User updated successfully)
		allowed = ['banned', 'requestLast']
		if not any(a in args for a in allowed):
			return False
		self.db.execute("UPDATE RequestUsers SET " + args[0] + " = " + kwds[args[0]] + " WHERE rdID = ?",
			(rdid,))
		return True

	def ban_requester(self, rdid: int) -> bool:
		""" Bans a Request User. """
		# RETURNS: bool (User updated successfully)
		return self.update_requester(rdid=rdid, banned=1)

	def unban_requester(self, rdid: int) -> bool:
		""" Unbans a Request User. """
		# RETURNS: bool (User updated successfully)
		return self.update_requester(rdid=rdid, banned=0)

	def requester_rq(self, rdid: int) -> bool:
		""" Updates a Request User's last time they requested to now. """
		# RETURNS: bool (User updated successfully)
		return self.update_requester(rdid=rdid, requestLast=int(time.time()))

	# SERVER SETTINGS
	def add_server(self, mmss: MMServerSettings) -> bool:
		""" Adds MMServerSettings object to the ServerSettings table. """
		# RETURNS: bool (Server Settings added successfully)
		try:
			self.db.execute(
				"""
				INSERT INTO ServerSettings(stID, stName, requests, allowedChannels, allowedRoles, requestCooldown)
				VALUES(?, ?, ?, ?, ?, ?)
				""",
				(mmss.id, mmss.name, int(mmss.requests), str(mmss.allowedChannels), 
					str(mmss.allowedRoles), mmss.requestCooldown,))
			return True
		except sqlite3.IntegrityError:
			return False

	def remove_server(self, stid: int):
		""" Removes MMServerSettings object from the ServerSettings table. """
		self.db.execute(
			"""
			DELETE FROM ServerSettings
			WHERE stID=?
			""",
			(stid,))

	def new_server(self, stid: int, stname: str, 
		requests: bool, allowedChannels: list, allowedRoles: list, requestCooldown: int) -> bool:
		""" Generates new MMServerSettings object and adds it to ServerSettings table. """
		# RETURNS: bool (Server Settings added successfully)
		mmss = MMServerSettings(stID=stid, stName=stname, requests=requests, 
			allowedChannels=allowedChannels, allowedRoles=allowedRoles, requestCooldown=requestCooldown)
		return self.add_server(mmss)

	def get_server(self, stid: int) -> MMServerSettings:
		""" Returns the Server Settings from a given Discord Server ID. """
		# RETURNS: MMServerSettings
		t = self.query_single_result("SELECT * FROM ServerSettings WHERE stID = ?", (stid,))
		if not t:
			return None
		return MMServerSettings(stID=t[0], stName=t[1], requests=bool(t[2]), 
			allowedChannels=StrToListInts(t[3]), allowedRoles=StrToListInts(t[4]), requestCooldown=t[5])

	def update_server(self, stid: int, *args, **kwds) -> bool:
		""" Updates MMServerSettings object in the ServerSettings table. """
		# Allowed ARGS: requests (int), allowedChannels (str), allowedRoles (str), requestCooldown (int)
		# RETURNS: bool (Server Settings updated successfully)
		allowed = ['requests', 'allowedChannels', 'allowedRoles', 'requestCooldown']
		if not any(a in args for a in allowed):
			return False
		upd = kwds[args[0]]
		if args[0] == 'requests':
			upd = int(upd)
		elif args[0] in ['allowedChannels', 'allowedRoles']:
			upd = str(upd)
		self.db.execute("UPDATE ServerSettings SET " + args[0] + " = " + upd + " WHERE stID = ?",
			(rdid,))
		return True
