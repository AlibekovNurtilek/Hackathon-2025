from fastapi import APIRouter

router = APIRouter()

@router.get("/")
def get_users():
    return {"users": ["Tyny", "Erji", "Tanos"]}
    