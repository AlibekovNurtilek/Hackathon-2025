from fastapi import FastAPI
from app.routes import users, items

app = FastAPI(title="Hackathon-2025 API")

# Подключаем маршруты
app.include_router(users.router, prefix="/users", tags=["Users"])

@app.get("/")
def home():
    return {"message": "FastAPI with Conda is running!"}
