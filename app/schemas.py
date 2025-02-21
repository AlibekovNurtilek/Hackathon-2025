from pydantic import BaseModel

# Схема для регистрации пользователя
from pydantic import BaseModel, Field

class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, strip_whitespace=True)
    password: str = Field(..., min_length=6, max_length=100)


# Схема для ответа после логина (JWT-токен)
class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str

# Схема для передачи данных о пользователе
class UserResponse(BaseModel):
    id: int
    username: str

    class Config:
        from_attributes = True  # Для работы с SQLAlchemy
