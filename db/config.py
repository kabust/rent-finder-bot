import sqlite3


con = sqlite3.connect("db.sqlite")
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
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        user_id INTEGER NOT NULL,
        olx_link STRING NOT NULL
    )
    """
)

con.commit()


if __name__ == "__main__":
    cur.execute("DROP TABLE users_new")
    cur.execute(
        """
        CREATE TABLE users_new(
            user_id INTEGER NOT NULL,
            chat_id INTEGER NOT NULL,
            full_name VARCHAR(50), 
            username VARCHAR(50), 
            is_active BOOLEAN NOT NULL DEFAULT 1,
            is_bot BOOLEAN, 
            city VARCHAR(50), 
            PRIMARY KEY(user_id)
        )
        """
    )
    cur.execute(
        """
        INSERT INTO users_new (user_id, chat_id, full_name, username, is_active, is_bot, city)
        SELECT user_id, chat_id, full_name, username, 1, is_bot, city
        FROM users
        """
    )
    cur.execute("DROP TABLE users")
    cur.execute("ALTER TABLE users_new RENAME TO users")

    con.commit()
