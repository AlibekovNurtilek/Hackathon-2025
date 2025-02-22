from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware  # Импортируем CORS Middleware
from app.routes import users, items
from app.database.database import engine, Base
import app.database.models  # Импортируем, чтобы SQLAlchemy знал о таблицах
from app.database.import_data.start_import import start_import
app = FastAPI(title="Hackathon-2025 API")

# Разрешаем CORS для всех источников (*), методов и заголовков
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Разрешаем все источники
    allow_credentials=True,
    allow_methods=["*"],  # Разрешаем все методы (GET, POST, PUT, DELETE и т. д.)
    allow_headers=["*"],  # Разрешаем все заголовки
)
print(f"📌 Используемая БД: {engine.url}")

Base.metadata.create_all(bind=engine)

#start_import()

# Подключаем маршруты
app.include_router(users.router)
app.include_router(items.router)

@app.get("/")
def home():
    return {"message": "FastAPI with Conda is running!"}
