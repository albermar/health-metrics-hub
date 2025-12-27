#Ok, now we're creating a new databse:
import sqlite3
db_name = 'drills2.db'


#delete the databse file if it exists
import os
    

#create the databse file and define columns: id, name, age if the DB doesn't exist:

if not os.path.exists(db_name):
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()

    cursor.execute('''
               CREATE TABLE users(
                   id INTEGER PRIMARY KEY, 
                   name TEXT, 
                   age INTEGER
                   );
               ''')
    conn.commit()
    conn.close()

#insert random users:
N = 3000000

import random

'''
conn = sqlite3.connect(db_name)
cursor = conn.cursor()
for i in range(N):
    age = random.randint(18, 120)
    #the name must be a string computed from the number, with chars, for example converting the i to dictionary base 26 with letters a-z
    name = ''
    n = i
    while n > 0:
        n, r = divmod(n-1, 26)
        name = chr(97 + r) + name
        
    cursor.execute("INSERT INTO users(name, age) VALUES(?, ?);", (name, age))
conn.commit()
conn.close()
'''
'''
#print all users
conn = sqlite3.connect(db_name)
cursor = conn.cursor()
cursor.execute("SELECT * FROM users;")
all_users = cursor.fetchall()
print("All users:")
for user in all_users:
    #print(user) 
    pass
conn.close()
'''


#count users older than 29 
conn = sqlite3.connect(db_name)
cursor = conn.cursor()
cursor.execute("SELECT * FROM users WHERE age > ?;", (29,))
older_users = cursor.fetchall()
print(f"Users older than 29 ({len(older_users)} found):")

conn.close()


#why (29,) instead of (29)?
#Because (29,) is a tuple with one element, while (29) is just an integer enclosed in parentheses.

#update users' names whose names contains hiii to "Johnny"
conn = sqlite3.connect(db_name)
cursor = conn.cursor()
cursor.execute("UPDATE users SET name = ? WHERE name LIKE ?;", ("Johnny", "%hiii%"))
conn.commit()
conn.close()


#print last 10 users
conn = sqlite3.connect(db_name)
cursor = conn.cursor()
cursor.execute("SELECT * FROM users ORDER BY id DESC LIMIT 10;")
last_10_users = cursor.fetchall()
print("Last 10 users:")
for user in last_10_users:
    print(user)
conn.close()


#print users that have a z in their name
conn = sqlite3.connect(db_name)
cursor = conn.cursor()
cursor.execute("SELECT * FROM users WHERE name LIKE ?;", ('%Johnny%',))
users_with_z = cursor.fetchall()
print("Users with 'Johnny' in their name:")
for user in users_with_z:
    print(user)
conn.close()

