from db.config import SessionLocal, User


def get_user(user_id: int):
    session = SessionLocal()
    user = session.query(User).filter(User.user_id == user_id).first()
    session.close()
    return user


def get_user_by_chat_id(chat_id: int):
    session = SessionLocal()
    user = session.query(User).filter(User.chat_id == chat_id).first()
    session.close()
    return user


def get_all_users():
    session = SessionLocal()
    users = session.query(User).all()
    session.close()
    return users


def get_all_active_users_with_city():
    session = SessionLocal()
    users = session.query(User).filter(
        User.city.isnot(None),
        User.is_active == True,
        User.is_bot == False
    ).with_entities(User.user_id, User.chat_id, User.city).all()
    session.close()
    return users


def write_user(
    user_id: int,
    chat_id: int,
    full_name: str,
    username: str,
    is_bot: bool,
    city: str | None = None,
):
    session = SessionLocal()
    user = User(
        user_id=user_id,
        chat_id=chat_id,
        full_name=full_name,
        username=username,
        is_bot=is_bot,
        city=city,
        is_active=True
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    session.close()
    return user


def delete_user(user_id: int):
    session = SessionLocal()
    session.query(User).filter(User.user_id == user_id).delete()
    session.commit()
    session.close()


def activate_user(user_id: int):
    session = SessionLocal()
    session.query(User).filter(User.user_id == user_id).update({"is_active": True})
    session.commit()
    session.close()


def deactivate_user(user_id: int):
    session = SessionLocal()
    session.query(User).filter(User.user_id == user_id).update({"is_active": False})
    session.commit()
    session.close()


def update_user_city(user_id: int, new_city: str):
    session = SessionLocal()
    session.query(User).filter(User.user_id == user_id).update({"city": new_city})
    session.commit()
    session.close()


def get_unique_cities():
    session = SessionLocal()
    cities = session.query(User.city).filter(
        User.city.isnot(None),
        User.is_active == True
    ).distinct().all()
    session.close()
    return set(city for (city,) in cities if city)
