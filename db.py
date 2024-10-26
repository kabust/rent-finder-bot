import sqlite3


con = sqlite3.connect("db.sqlite")
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


def get_user(user_id: int):
    user = cur.execute("SELECT * FROM users WHERE user_id = (?)", [user_id])
    return user.fetchone()


def get_user_by_chat_id(chat_id: int):
    user = cur.execute("SELECT * FROM users WHERE chat_id = (?)", [chat_id])
    return user.fetchone()


def get_all_users():
    users = cur.execute("SELECT * FROM users")
    return users.fetchall()


def get_all_users_with_city():
    users = cur.execute(
        "SELECT user_id, chat_id, city FROM users WHERE city IS NOT NULL"
    )
    return users.fetchall()


def write_user(
    user_id: int,
    chat_id: int,
    full_name: str,
    username: str,
    is_bot: bool,
    city: str | None = None,
):
    cur.execute(
        "INSERT INTO users VALUES (?, ?, ?, ?, ?, ?)",
        [user_id, chat_id, full_name, username, is_bot, city],
    )
    con.commit()


def delete_user(user_id: int):
    cur.execute("DELETE FROM users WHERE id = (?)", [user_id])
    con.commit()


def update_user_city(user_id: int, new_city: str):
    cur.execute("UPDATE users SET city = (?) WHERE user_id = (?)", [new_city, user_id])
    con.commit()
