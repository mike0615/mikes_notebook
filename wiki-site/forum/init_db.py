import sqlite3, os
DB = os.path.join(os.path.dirname(__file__), 'forum.db')
conn = sqlite3.connect(DB)
conn.execute('''CREATE TABLE IF NOT EXISTS posts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    author TEXT,
    content TEXT,
    created TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)''')
conn.commit()
conn.close()
print('initialized', DB)
