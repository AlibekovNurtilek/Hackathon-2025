from fastapi import FastAPI
from app.routes import users, items
from app.database.database import engine, Base
import app.database.models  # Импортируем, чтобы SQLAlchemy знал о таблицах

app = FastAPI(title="Hackathon-2025 API")

# Создаём таблицы, если их нет
Base.metadata.create_all(bind=engine)

# Подключаем маршруты
app.include_router(users.router)

@app.get("/")
def home():
    return {"message": "FastAPI with Conda is running!"}
