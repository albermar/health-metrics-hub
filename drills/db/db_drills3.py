#Create a DB with id as primary key, name, age
import sqlite3
db_name = 'drills3.db'
conn = sqlite3.connect(db_name)
c = conn.cursor()
c.execute('''
          CREATE TABLE IF NOT EXISTS users(
                id INTEGER PRIMARY KEY, 
                name TEXT, 
                age INTEGER
                );
        ''')
conn.commit()
conn.close()

import os
import random

##while the size is less than 10 MB, keep inserting 100 random records
while os.path.getsize(db_name) < 10 * 1024 * 1024:
    conn = sqlite3.connect(db_name)
    c = conn.cursor()
    for i in range(10000):
        name = f'User{random.randint(100000, 999999)}'
        age = random.randint(18, 80)
        c.execute('INSERT INTO users (name, age) VALUES (?, ?)', (name, age))
    conn.commit()
    conn.close()


#Next drill: check the db health:

conn = sqlite3.connect(db_name)
cur = conn.cursor()

cur.execute('PRAGMA integrity_check;')
result = cur.fetchone()
if result[0] == 'ok':
    print("Database integrity check passed.")
else:
    print("Database integrity check failed:", result[0])
    
cur.execute('SELECT name FROM sqlite_master WHERE type="table";')
tables = cur.fetchall()
print("Tables in the database:")
for table in tables:
    print(table[0])



#count how many rows you have:
cur.execute('SELECT COUNT(*) FROM users;')
row_count = cur.fetchone()[0]
print(f"Total number of rows in users table: {row_count}")


#see a sample of data 10 rows:
cur.execute('SELECT * FROM users LIMIT 10;')
rows = cur.fetchall()
print("Sample data from users table:")
for row in rows:
    print(row)  
    




conn.close()