import sqlite3
import time
from json_abs import *
from cep import *
import gd

client = gd.Client()

class MMLevel:

	def __init__(self, lID: int, lName="", lAuthor="", lDifficulty=0, lLength=-2, lRqS=-1, lIsRated=False):
		""" Object for Levels in-game."""
		self.id = lID
		self.name = lName
		self.author = lAuthor
		self.difficulty = lDifficulty
		self.length = lLength
		self.rqs = lRqS
		self.isRated = lIsRated

	async def generate(self):
		""" Fill all empty 'l' attributes from ID. """
		level = await client.get_level(self.id)
		self.name = level.name
		self.author = level.creator.name
		self.difficulty = level.difficulty.value
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

		self.db.execute("CREATE TABLE Levels("
			# Levels requested.
			# -lID INTEGER: In-game Level ID.
			# -lName TEXT, -lAuthor TEXT, -lDifficulty INTEGER, -lLength INTEGER,
			# -lRqS INTEGER (Requested Stars), and -lIsRated INTEGER (BOOL) are
			# in-game level attributes.
			# -isSent INTEGER: Number of times sent.
			"lID INTEGER PRIMARY KEY, "
			"lName TEXT, "
			"lAuthor TEXT, "
			"lDifficulty INTEGER, "
			"lLength INTEGER, "
			"lRqS INTEGER, "
			"lIsRated INTEGER, "
			"isSent INTEGER "
			")")
		self.db.execute("CREATE TABLE Users("
			# Users with linked Discord and in-game accounts.
			# -uID INTEGER: User's in-game account ID.
			# -dID INTEGER: User's Discord ID.
			# -uName TEXT and -uIsMod INTEGER are in-game user attributes.
			"uID INTEGER PRIMARY KEY, "
			"dID INTEGER, "
			"uName TEXT, "
			"uIsMod INTEGER, "
			"UNIQUE(uName) "
			")")
		self.db.execute("CREATE TABLE SendHistory("
			# -sID INTEGER: Record ID for sent level.
			# -flID INTEGER and -fuID INTEGER are references.
			# -sTime INTEGER (UNIX timestamp): Record creation time.
			"sID INTEGER PRIMARY KEY AUTOINCREMENT, "
			"flID INTEGER, "
			"fuID INTEGER, "
			"sTime INTEGER, "
			"FOREIGN KEY(flID) REFERENCES Levels(lID), "
			"FOREIGN KEY(fuID) REFERENCES Users(uID) "
			")")
		self.db.execute("CREATE TABLE RequestUsers("
			# -rdID INTEGER: User's Discord ID.
			# -rName TEXT: User's Discord Name.
			# -banned INTEGER (bool): If the user is banned from requesting.
			# -requestLast INTEGER (UNIX timestamp): Most recent time user requested.
			# -requestToday INTEGER: Count times user requested today.
			"rdID INTEGER PRIMARY KEY, "
			"rName TEXT, "
			"banned INTEGER, "
			"requestLast INTEGER, "
			"requestToday INTEGER "
			"UNIQUE(rdID) "
			")")
		self.db.execute("CREATE TABLE ServerSettings("
			# -stID INTEGER: Server's Discord ID.
			# -stName TEXT: Server's Discord Name.
			# -requests INTEGER (bool): If level requests are on for this server.
			# -allowedChannels TEXT (list<int>): List of Discord Channels allowed 
			# to request in. If empty, any Discord Channel is allowed.
			# -allowedRoles TEXT (list<int>): List of Discord Roles a user needs
			# one of to request. If empty, no Discord Roles required to request.
			# -requestCooldown INTEGER (Minutes): Cooldown between requests.
			# If 0, no cooldown.
			# -requestLimit INTEGER: Number of requests allowed in server per day.
			# If 0, no limit.
			"stID INTEGER PRIMARY KEY, "
			"stName TEXT, "
			"requests INTEGER, "
			"allowedChannels TEXT, "
			"allowedRoles TEXT, "
			"requestCooldown INTEGER, "
			"requestLimit INTEGER, "
			"UNIQUE(stID) "
			")")
		self.db.commit()

		for user in DBPRELOAD_Users:
			mmu = MMUser(uID=user['uID'], dID=user['dID'], uName=user['uName'], uIsMod=user['uIsMod'])
			self.add_user(mmu)
		print('[db] cep.py: PRELOADED Users')

	# LEVELS
	def add_level(self, mml: MMLevel) -> bool:
		""" Adds MMLevel object to Levels table. """
		# RETURNS: bool (Level added successfully)
		if not self.get_level(mml.id):
			try:
				self.db.execute("INSERT INTO Levels(lID, lName, lAuthor, lDifficulty, lLength, lRqS, lIsRated, isSent)"
					"VALUES(?, ?, ?, ?, ?, ?, ?, ?)", 
					(mml.id, mml.name, mml.author, mml.difficulty, mml.length, mml.rqs, int(mml.isRated), 0,))
				return True
			except sqlite3.IntegrityError:
				return False
		return False

	def remove_level(self, lid: int):
		""" Removes MMLevel object from Levels table. """
		self.db.execute("DELETE FROM Levels "
			"WHERE lID=?",
			(lid,))

	def get_level(self, lid: int) -> MMLevel:
		""" Returns MMLevel object from Levels table. """
		# RETURNS: MMLevel
		t = self.query_single_result("SELECT * FROM Levels WHERE lID = ?", (lid,)) 
		if not t:
			return None
		return MMLevel(lID=t[0], lName=t[1], lAuthor=t[2], lDifficulty=t[3], 
			lLength=t[4], lRqS=t[5], lIsRated=bool(t[6]))

	async def new_level(self, lid: int) -> bool:
		""" Searches for level in-game with given ID and adds to Levels table. """
		# RETURNS: bool (Level added successfully)
		mml = MMLevel(lID=lid)
		await mml.generate()
		return self.add_level(mml)

	# USERS
	def add_user(self, mmu: MMUser) -> bool:
		""" Adds MMUser object to Users table. """
		# RETURNS: bool (User added successfully)
		if not self.get_user(mmu.uid):
			try:
				self.db.execute("INSERT INTO Users(uID, dID, uName, uIsMod)"
					"VALUES(?, ?, ?, ?)",
					(mmu.uid, mmu.did, mmu.name, mmu.isMod,))
			except sqlite3.IntegrityError:
				return False
			return True
		return False

	def remove_user(self, uid: int):
		""" Removes MMUser object from Users table. """
		self.db.execute("DELETE FROM Users "
			"WHERE uID=?",
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

	#SEND HISTORY
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
		self.db.execute("INSERT INTO SendHistory(flID, fuID, sTime)"
			"VALUES(?, ?, ?)",
			(flid, fuid, int(time.time()),))
		self.db.execute("UPDATE Levels "
			"SET isSent = isSent + 1"
			"WHERE flID = ? ",
			(flid,))
		return 0

	def get_sends_user(self, *args, **kwds) -> list:
		""" Finds levels a user has sent. """
		# Allowed ARGS: uID (int), dID (int)
		# RETURNS: list<MMLevel>
		if 'uID' not in args and 'dID' not in args:
			return None
		kID = kwds[args[0]]
		if args[0] == 'dID':
			kID = get_user_uid(kID)

		leveldata = list(self.query_multiple_results(
			"""
			SELECT Levels.lID, Levels.lName, Levels.lAuthor, Levels.lDifficulty, Levels.lLength,
			Levels.lRqS, Levels.lIsRated
			FROM SendHistory
			INNER JOIN Levels ON Levels.lID = SendHistory.flID
			WHERE SendHistory.fuID = ?
			"""
			), (kID))
		return [MMLevel(lID=r[0], lName=r[1], lAuthor=r[2], lDifficulty=r[3], 
			lLength=r[4], lRqS=r[5], lIsRated=r[6]) for r in leveldata]

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