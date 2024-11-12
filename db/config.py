import sqlite3


con = sqlite3.connect("db/db.sqlite")
con.row_factory = sqlite3.Row
cur = con.cursor()

cur.execute(
    """
    CREATE TABLE IF NOT EXISTS users(
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

cur.execute(
    """
    CREATE TABLE IF NOT EXISTS sent_ads(
        id INTEGER PRIMARY KEY NOT NULL,
        user_id INTEGER NOT NULL,
        olx_link STRING NOT NULL
    )
    """
)

con.commit()
