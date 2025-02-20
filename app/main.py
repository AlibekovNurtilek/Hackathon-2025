from fastapi import FastAPI
from app.routes import users, items

app = FastAPI(title="FastAPI + Conda Project")

# Подключаем маршруты
app.include_router(users.router, prefix="/users", tags=["Users"])

@app.get("/")
def home():
    return {"message": "FastAPI with Conda is running!"}
