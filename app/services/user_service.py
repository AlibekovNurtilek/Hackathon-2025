from sqlalchemy.orm import Session
from app.database.models import User
from app.schemas import UserCreate
from app.utils import hash_password, verify_password, create_access_token, create_refresh_token
from datetime import timedelta
from app.config import ACCESS_TOKEN_EXPIRE_MINUTES, REFRESH_TOKEN_EXPIRE_DAYS
from fastapi import HTTPException


# Функция для регистрации пользователя
def create_user(db: Session, user_data: UserCreate):
    # Проверяем, существует ли уже пользователь с таким именем
    existing_user = db.query(User).filter(User.username == user_data.username).first()
    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="User with this username already exists"
        )
    
    hashed_password = hash_password(user_data.password)
    db_user = User(username=user_data.username, hashed_password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    return db_user

# Функция для аутентификации пользователя (логин)
def authenticate_user(db: Session, username: str, password: str):
    user = db.query(User).filter(User.username == username).first()
    if not user or not verify_password(password, user.hashed_password):
        return None
    return user

# Функция для выдачи JWT-токена при успешном входе
def generate_tokens(user: User, db: Session):
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    refresh_token_expires = timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)

    access_token = create_access_token(
        data={"sub": user.username, "user_id": user.id}, expires_delta=access_token_expires
    )
    refresh_token = create_refresh_token(
        data={"sub": user.username, "user_id": user.id}, expires_delta=refresh_token_expires
    )

    # Сохраняем Refresh Token в базе
    user.refresh_token = refresh_token
    db.commit()

    return access_token, refresh_token
