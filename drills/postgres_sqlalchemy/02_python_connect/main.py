'''
Opens a connection to Postgres
Creates a table (if it doesn’t exist)
Inserts one row
Reads it back
Prints the result
'''

import  

DB_URL = "postgresql://alberto:supersecret@localhost:5432/health_drill"

def main() -> None:
    #1. connect to the postgresql server
    with psycopg.connect(DB_URL) as conn:
        #2. create a cursor
        with conn.cursor() as cur:
            #3. Create a table (safe to run multiple times)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS notes (
                    id SERIAL PRIMARY KEY,
                    text TEXT NOT NULL
                )
            """)
            # 4. Insert one row
            cur.execute("INSERT INTO notes (text) VALUES (%s) RETURNING id;", ("hello from python",))
            new_id = cur.fetchone()[0]
            
            # 5. Read it back
            cur.execute("SELECT id, text FROM notes WHERE id = %s;",(new_id,))
            row = cur.fetchone()

            print("Inserted and fetched:", row)


if __name__ == "__main__":
    main()
            