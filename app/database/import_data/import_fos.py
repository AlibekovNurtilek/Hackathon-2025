import json
from sqlalchemy.orm import Session
from app.database.models import FieldOfStudy, Subject, fields_subjects
from app.database.database import SessionLocal

def import_fos():
    """Импортирует данные в БД, если таблицы пустые."""
    db = SessionLocal()
    
    # Проверяем, есть ли уже данные
    if db.query(FieldOfStudy).first() is None:
        print("⏳ Импортируем данные в базу...")

        with open("app/database/static_files/fields_of_study.json", "r", encoding="utf-8") as f:
            data = json.load(f)

        subjects_cache = {}

        try:
            for fos in data["fields_of_study"]:
                # Добавляем FieldOfStudy
                field = FieldOfStudy(name=fos["name"])
                db.add(field)
                db.commit()
                db.refresh(field)

                # Добавляем Subject и связи fields_subjects
                for subject in fos["subjects"]:
                    subject_id = subject["id"]
                    subject_name = subject["name"]

                    if subject_id not in subjects_cache:
                        new_subject = Subject(id=subject_id, name=subject_name)
                        db.add(new_subject)
                        db.commit()
                        db.refresh(new_subject)
                        subjects_cache[subject_id] = new_subject
                    else:
                        new_subject = subjects_cache[subject_id]

                    # Заполняем связь fields_subjects
                    db.execute(fields_subjects.insert().values(field_id=field.id, subject_id=new_subject.id))
                    db.commit()

            print("✅ Данные успешно импортированы!")

        except Exception as e:
            db.rollback()
            print(f"❌ Ошибка при импорте: {e}")

        finally:
            db.close()
    else:
        print("✅ База уже содержит данные, импорт не требуется.")

