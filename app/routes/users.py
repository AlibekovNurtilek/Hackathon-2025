from fastapi import Request

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm
from app.database.database import get_db
from app.services.user_service import create_user, authenticate_user, generate_tokens
from app.schemas import UserCreate, Token
import jwt
from app.database.models import User
from app.config import SECRET_KEY, ALGORITHM

router = APIRouter(prefix="/users", tags=["Users"])


# Эндпоинт для регистрации пользователя
@router.post("/register")
def register(user_data: UserCreate, db: Session = Depends(get_db)):
    db_user = create_user(db, user_data)
    return {"message": "User registered successfully", "username": db_user.username}


# # Эндпоинт для логина и получения JWT
# @router.post("/token", response_model=Token)
# def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
#     user = authenticate_user(db, form_data.username, form_data.password)
#     if not user:
#         raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
#
#     access_token, refresh_token = generate_tokens(user, db)
#
#     return {
#         "access_token": access_token,
#         "refresh_token": refresh_token,
#         "token_type": "bearer"
#     }

@router.post("/token", response_model=Token)
async def login(request: Request, db: Session = Depends(get_db)):
    content_type = request.headers.get("content-type", "")

    if "application/json" in content_type.lower():
        # Читаем JSON
        data = await request.json()
        username = data.get("username")
        password = data.get("password")
    else:
        # Иначе используем OAuth2PasswordRequestForm (x-www-form-urlencoded)
        form = await request.form()
        username = form.get("username")
        password = form.get("password")

    user = authenticate_user(db, username, password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    access_token, refresh_token = generate_tokens(user, db)
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }


@router.post("/refresh")
def refresh_token(refresh_token: str, db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("user_id")

        user = db.query(User).filter(User.id == user_id, User.refresh_token == refresh_token).first()
        if not user:
            raise HTTPException(status_code=401, detail="Invalid refresh token")

        access_token, new_refresh_token = generate_tokens(user, db)

        return {
            "access_token": access_token,
            "refresh_token": new_refresh_token,
            "token_type": "bearer"
        }
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Refresh token expired")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
