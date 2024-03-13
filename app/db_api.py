import threading, sqlite3, random, time, os

def DB_DictFactory(cursor, row):
	_ = {}
	for i, column in enumerate(cursor.description):
		_[column[0]] = row[i]
	return _

def os_delete(*paths):
	for path in paths:
		for x in range(50):
			try: os.remove(path)
			except: time.sleep(.8)

class database_driver:
	def __init__(self):
		self.con = sqlite3.connect('db.db')
		self.con.row_factory = DB_DictFactory
		self.cur = self.con.cursor()

	def _get_connection(self):
		return self.con, self.cur
	
	def change_list(self, *query):
		for q in query:
			self.cur.execute(q)
		self.con.commit()

	def close(self):
		self.cur.close()
		self.con.close()

	def create_tables(self):
		table_queries = {
			'users': '''
				CREATE TABLE IF NOT EXISTS users(
					uid INTEGER PRIMARY KEY AUTOINCREMENT,
					username TEXT,
					hashed_password TEXT,
					access_level INTEGER DEFAULT (0)
				)
			''',
			'records': '''
				CREATE TABLE IF NOT EXISTS records(
					id INTEGER PRIMARY KEY AUTOINCREMENT,
					uid INTEGER,
					field1 TEXT,
					field2 TEXT,
					field3 TEXT,
					field4 TEXT,
					field5 TEXT,
					field6 TEXT,
					field7 TEXT,
					field8 TEXT,
					file_url TEXT,
					create_date INTEGER
				)
			''',
		}

		for table_name, q in table_queries.items():
			self.cur.execute(q)

		self.con.commit()

	async def get_records(self, fields: list = {}, full_comparasion: bool = True, all_records: bool = False):
		if all_records:
			return self.cur.execute(f'SELECT id, field1, field2, field3, field4, field5, field6, field7, field8, file_url FROM records ORDER BY create_date DESC').fetchall()
		
		default_fields = ['field1', 'field2', 'field3', 'field4', 'field5', 'field6', 'field7', 'field8']
		if full_comparasion:
			search_fields = {default_fields[i]: x[1] for i, x in enumerate(fields.items()) if x[1].strip() != ''}
			if len(search_fields) == 0: return []

			sql_islt = [f'{x}' for x in search_fields]
			self.cur.execute(f'SELECT id, field1, field2, field3, field4, field5, field6, field7, field8, file_url FROM records WHERE ({", ".join(sql_islt)}) = ({", ".join(["?" for x in sql_islt])}) ORDER BY create_date DESC', [*search_fields.values()])
		else:
			search_fields = {default_fields[i]: f'%{x[1]}%' for i, x in enumerate(fields.items()) if x[1].strip() != ''}
			if len(search_fields) == 0: return []

			sql_islt = [f'{x} LIKE ?' for x in search_fields]
			self.cur.execute(f'SELECT id, field1, field2, field3, field4, field5, field6, field7, field8, file_url FROM records WHERE {" AND ".join(sql_islt)} ORDER BY create_date DESC', [*search_fields.values()])

		return self.cur.fetchall()

	async def add_record(self, uid = 1, fields = {}, file = None):
		default_fields = ['field1', 'field2', 'field3', 'field4', 'field5', 'field6', 'field7', 'field8']
		search_fields = {default_fields[i]: x[1] for i, x in enumerate(fields.items()) if x[1].strip() != ''}
		if len(search_fields) == 0: return {}
		sql_islt = [*search_fields.keys()]
		sql_islt_AS = [f'{default_fields[i]} AS "{x}"' for i, x in enumerate(fields.keys())]
		ts = int(time.time())

		file_url = f'files/{ts}{random.randint(111,999)}_{file.filename}'
		open(file_url, "wb").write(file.file.read())

		self.cur.execute(f'INSERT INTO records (uid, file_url, create_date{", " if len(sql_islt) > 0 else ""}{", ".join(sql_islt)}) VALUES (?, ?, ?{", " if len(sql_islt) > 0 else ""}{", ".join(["?" for x in sql_islt])})', [uid, file_url, ts, *search_fields.values()])
		self.con.commit()

		return self.cur.execute('SELECT * FROM records WHERE (uid, file_url, create_date) = (?, ?, ?)', [uid, file_url, ts]).fetchone()

	async def delete_record(self, record_id):
		threading.Thread(target=os_delete, args=[self.cur.execute('SELECT file_url FROM records WHERE id = ?', [record_id]).fetchone()['file_url']]).start()
		self.cur.execute('DELETE FROM records WHERE id = ?', [record_id])
		self.con.commit()

		return self.cur.execute('SELECT * FROM records WHERE (id) = (?)', [record_id]).fetchone()

	async def update_record(self, record_id, record_data):
		#print(record_data.values(), [x if x not in ('', ' ') else None for x in record_data.values()])
		record_data = [x if x not in ('', ' ') else None for x in record_data.values()]
		self.cur.execute('UPDATE records SET (field1, field2, field3, field4, field5, field6, field7, field8) = (?, ?, ?, ?, ?, ?, ?, ?) WHERE id = ?', [*record_data, record_id])
		self.con.commit()

		return self.cur.execute('SELECT * FROM records WHERE (id) = (?)', [record_id]).fetchone()

	async def get_user(self, user):
		user = self.cur.execute('SELECT * FROM users WHERE (username) = (?)', [user.username]).fetchone()
		return user

	async def create_user(self, user):
		if not await self.get_user(user):
			self.cur.execute('INSERT INTO users (username, hashed_password, access_level) VALUES (?, ?, ?)', [user.username, user.password, user.access_level])
			self.con.commit()
		
		user = self.cur.execute('SELECT * FROM users WHERE (username) = (?)', [user.username]).fetchone()
		return user

	def __enter__(self):
		return self

	def __exit__(self, exc_type, exc_value, traceback):
		self.close()

	def __del__(self):
		self.close()

#_db = database_driver().create_tables()
_db = database_driver()
con, cur = _db._get_connection()
cur.execute('UPDATE users SET username = ?', [None])
con.commit()