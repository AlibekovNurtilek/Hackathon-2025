import json
from app.database.database import SessionLocal
from app.database.models import Program

def get_unique_values():
    db = SessionLocal()
    try:
        # Извлекаем уникальные значения (результат — список кортежей)
        locations = db.query(Program.location).distinct().all()
        languages = db.query(Program.language).distinct().all()
        modes = db.query(Program.mode_of_study).distinct().all()

        # Преобразуем списки кортежей в множества строк, исключая пустые значения
        unique_locations = sorted({loc[0] for loc in locations if loc[0]})
        unique_languages = sorted({lang[0] for lang in languages if lang[0]})
        unique_modes = sorted({mode[0] for mode in modes if mode[0]})

        # Собираем итоговый словарь
        unique_data = {
            "location": unique_locations,
            "language": unique_languages,
            "mode_of_study": unique_modes
        }
        return unique_data
    finally:
        db.close()

def save_unique_values_to_json(filepath="unique_fields.json"):
    unique_data = get_unique_values()
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(unique_data, f, ensure_ascii=False, indent=4)
    print(f"Уникальные значения сохранены в {filepath}")

if __name__ == "__main__":
    save_unique_values_to_json()
