import sqlite3
import time
from json_abs import *
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

	def __init__(self, uID: int, dID: int, uName="", uIsMod=False):
		""" Object for Users in Discord and in-game. """
		self.uid = uID
		self.did = dID
		self.name = uName
		self.isMod = uIsMod

	async def generate(self):
		""" Fill all empty 'u' attributes from ID. """
		user = await client.get_user(self.uid)
		self.name = user.name
		self.isMod = user.to_user().is_mod()


class LevelDatabase:
	
	def __init__(self, dbPath):
		""" Class for executing sqlite3 commands. """
		self.db = sqlite3.connect(dbPath)
		self.db.execute("PRAGMA foreign_keys = 1")

	def query_single_result(self, query, parameters):
        """ Execute a query for a single result. """
        # Author: MultipleMonomials

        cursor = self.database.execute(query, parameters)
        row = cursor.fetchone()

        if row is None or len(row) < 1:
            return None

        result = row[0]
        cursor.close()
        return result

    def query_multiple_results(self, query, parameters) -> tuple:
    	""" Execute a query for multiple results. """
    	cursor = self.database.execute(query, parameters)
        result = cursor.fetchall()
        if row is None or len(row) < 1:
            return None
        cursor.close()
        return result

	def create_tables(self):
		""" Loads tables from instructions. """
		self.db.execute("BEGIN")

		self.db.execute("CREATE TABLE Levels("
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
			# -uID INTEGER: User's in-game account ID.
			# -dID INTEGER: User's Discord ID.
			# -uName TEXT and -uIsMod INTEGER (BOOL) are in-game user attributes.
			"uID INTEGER PRIMARY KEY, "
			"dID INTEGER, "
			"uName TEXT, "
			"uIsMod INTEGER, "
			"UNIQUE(uName) "
			")")
		self.db.execute("CREATE TABLE SendHistory("
			# -sID INTEGER: Record ID for sent level.
			# -lID INTEGER and -uID INTEGER are references.
			# -sTime INTEGER: UNIX timestamp of record creation.
			"sID INTEGER PRIMARY KEY AUTOINCREMENT, "
			"FOREIGN KEY(lID) REFERENCES Levels(lID), "
			"FOREIGN KEY(uID) REFERENCES Users(uID), "
			"sTime INTEGER, "
			"UNIQUE(lID, uID)"
			")")

	# LEVELS
	def add_level(self, mml: MMLevel):
		""" Adds MMLevel object to Levels table. """
		self.db.execute("INSERT INTO Levels(lID, lName, lAuthor, lDifficulty, lLength, lRqS, lIsRated, isSent)"
			"VALUES(?, ?, ?, ?, ?, ?, ?, ?)", 
			(mml.id, mml.name, mml.author, mml.difficulty, mml.length, mml.rqs, int(mml.isRated), 0,))

	def remove_level(self, lid: int):
		""" Removes MMLevel object from Levels table. """
		self.db.execute("DELETE FROM Levels "
			"WHERE lID=?",
			(lid,))

	def get_level(self, lid: int) -> MMLevel:
		""" Returns MMLevel object from Levels table. """
		# RETURNS: MMLevel
		t = self.query_single_result("SELECT * FROM Levels WHERE lID = ?", (lid,)) 
		return MMLevel(lID=t[0], lName=t[1], lAuthor=t[2], lDifficulty=t[3], 
			lLength=t[4], lRqS=t[5], lIsRated=bool(t[6]))

	async def new_level(self, lid: int):
		""" Searches for level in-game with given ID and adds to Levels table. """
		mml = MMLevel(lID=lid)
		await mml.generate()
		self.add_level(mml)

	# USERS
	def add_user(self, mmu: MMUser):
		""" Adds MMUser object to Users table. """
		self.db.execute("INSERT INTO Users(uID, dID, uName, uIsMod)"
			"VALUES(?, ?, ?, ?)"
			(mmu.uid, mmu.did, mmu.name, int(mmu.isMod),))

	def remove_user(self, uid: int):
		""" Removes MMUser object from Users table. """
		self.db.execute("DELETE FROM Users "
			"WHERE uID=?",
			(uid,))

	def get_user(self, *args, **kwds) -> MMUser:
		""" Returns MMUser object from Users table. """
		# Allowed ARGS: uID (int), dID (int)
		# RETURNS: MMUser
		if 'uID' in not args and 'dID' not in args:
			return None
		t = self.query_single_result("SELECT * FROM Users WHERE " + args[0] + " = ?", (kwds[args[0]],)) 
		return MMUser(uID=t[0], dID=t[1], uName=t[2], uIsMod=bool(t[3]))

	def get_user_uid(self, did: int) -> int:
		""" Returns user's in-game ID from Discord ID. """
		# RETURNS: int
		return self.query_single_result("SELECT uID from Users WHERE dID = ?", (did,))

	async def new_user(self, uid: int, did: int):
		""" Searches for user in-game with given user ID and adds to Users table. """
		mmu = MMUser(uID=uid, dID=did)
		await mmu.generate()
		self.add_user(mmu)

	#SEND HISTORY
	def send(self, lid: int, uid: int) -> int:
		""" Creates new SendHistory record from a level being sent. """
		# RETURNS: 0=Success, 1=lid not found in Levels, 2=uid not found in Users, 3=User is not mod
		level = self.get_level(lid)
		if not level:
			return 1
		user = self.get_user(uid)
		if not user:
			return 2
		if not user.isMod:
			return 3
		self.db.execute("INSERT INTO SendHistory(lID, uID, sTime)"
			"VALUES(?, ?, ?)",
			(lid, uid, int(time.time()),))
		self.db.execute("UPDATE Levels "
			"SET isSent = isSent + 1"
			"WHERE lID = ? ",
			(lid,))
		return 0

	def get_sends_user(self, *args, **kwds) -> list:
		""" Finds levels a user has sent. """
		# Allowed ARGS: uID (int), dID (int)
		# RETURNS: list<MMLevel>
		if 'uID' in not args and 'dID' not in args:
			return None
		kID = kwds[args[0]]
		if args[0] == 'dID':
			kID = get_user_uid(kID)
		t = list(self.query_multiple_results("SELECT lID FROM SendHistory WHERE uID = ?", (kID,)))
		return [self.get_level(level) for level in t]

	def get_sends_level(self, lid: int):
		""" Finds users who've sent this level. """
		# RETURNS: list<MMUser>
		t = list(self.query_multiple_results("SELECT uID FROM SendHistory WHERE lID = ?", (lid,)))
		return [self.get_user(user) for user in t]