from db.config import con, cur


def get_user(user_id: int):
    user = cur.execute("SELECT * FROM users WHERE user_id = (?)", [user_id])
    return user.fetchone()


def get_user_by_chat_id(chat_id: int):
    user = cur.execute("SELECT * FROM users WHERE chat_id = (?)", [chat_id])
    return user.fetchone()


def get_all_users():
    users = cur.execute("SELECT * FROM users")
    return users.fetchall()


def get_all_active_users_with_city():
    users = cur.execute(
        """
        SELECT user_id, chat_id, city 
        FROM users 
        WHERE city IS NOT NULL AND is_active = 1
        """
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
    user = cur.execute(
        "INSERT INTO users VALUES (?, ?, ?, ?, ?, ?, ?)",
        [user_id, chat_id, full_name, username, 1, is_bot, city],
    )

    con.commit()
    return user.fetchone()


def delete_user(user_id: int):
    cur.execute("DELETE FROM users WHERE id = (?)", [user_id])
    con.commit()


def activate_user(user_id: int):
    cur.execute("UPDATE users SET is_active = 1 WHERE user_id = (?)", [user_id])
    con.commit()


def deactivate_user(user_id: int):
    cur.execute("UPDATE users SET is_active = 0 WHERE user_id = (?)", [user_id])
    con.commit()


def update_user_city(user_id: int, new_city: str):
    cur.execute("UPDATE users SET city = (?) WHERE user_id = (?)", [new_city, user_id])
    con.commit()


def get_unique_cities():
    query = cur.execute("SELECT DISTINCT city FROM users WHERE city IS NOT NULL")
    cities = set(raw["city"] for raw in query.fetchall())
    return cities
