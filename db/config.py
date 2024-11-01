import sqlite3


con = sqlite3.connect("db.sqlite")
con.row_factory = sqlite3.Row
cur = con.cursor()

try:
    cur.execute("SELECT * FROM users")
except Exception as e:
    print(e)
    cur.execute(
        """
        CREATE TABLE users(
            user_id INTEGER NOT NULL,
            chat_id INTEGER NOT NULL,
            full_name VARCHAR(50), 
            username VARCHAR(50), 
            is_bot BOOLEAN, 
            city VARCHAR(50), 
            PRIMARY KEY(user_id)
        )
        """
    )

try:
    cur.execute("SELECT * FROM sent_ads")
except Exception as e:
    print(e)
    cur.execute(
        """
        CREATE TABLE sent_ads(
            user_id INTEGER NOT NULL,
            olx_link STRING NOT NULL,
            PRIMARY KEY(user_id)
        )
        """
    )
