import os
import json
from sqlalchemy.orm import Session
from app.database.database import SessionLocal
from app.database.models import University, Program, Requirement, FieldOfStudy, Subject, program_requirements, program_fields, program_subjects

# Директория с JSON-файлами
DATA_DIR = "app/database/static_files/json_data"

def process_json_file(filepath, db):
    """ Обрабатывает один JSON-файл и загружает его в базу """
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Извлекаем данные из JSON
    course_details = data.get("course_details", {})
    requirements_data = data.get("requirements", {})
    fields_of_study_data = data.get("field_of_study", [])
    subjects_data = data.get("subject", [])
    application_link = data.get("application_link", None)

    # 1. Проверяем, что course_title не None
    course_title = course_details.get("course_title") or "Unknown Program"

    # 2. Добавляем университет (если не существует)
    university_name = course_details.get("university") or "Unknown University"
    university_location = course_details.get("location") or "Unknown Location"

    university = db.query(University).filter_by(name=university_name).first()
    if not university:
        university = University(name=university_name, location=university_location)
        db.add(university)
        db.flush()  # Сохраняем в памяти, но не коммитим сразу

    # 3. Добавляем программу
    program = Program(
        name=course_title,
        university_id=university.id,
        location=university_location,
        duration=course_details.get("duration"),
        tuition_fees=course_details.get("tuition_fees"),
        language=course_details.get("language_of_instruction"),
        mode_of_study=course_details.get("mode_of_study"),
        application_deadline=(requirements_data.get("application_deadline") or [None])[0],
        link=application_link  # Добавляем ссылку
    )
    db.add(program)
    db.flush()

    # 4. Добавляем fields_of_study и связываем с программой
    for field_name in fields_of_study_data:
        field = db.query(FieldOfStudy).filter_by(name=field_name).first()
        if not field:
            field = FieldOfStudy(name=field_name)
            db.add(field)
            db.flush()
        
        # Добавляем связь
        db.execute(program_fields.insert().values(program_id=program.id, field_id=field.id))

    # 5. Добавляем subjects и связываем с программой
    for subject_name in subjects_data:
        subject = db.query(Subject).filter_by(name=subject_name).first()
        if not subject:
            subject = Subject(name=subject_name)
            db.add(subject)
            db.flush()
        
        # Добавляем связь
        db.execute(program_subjects.insert().values(program_id=program.id, subject_id=subject.id))

    # 6. Добавляем требования и связываем с программой
    all_requirements = []

    # Обрабатываем языковые требования
    for req_type, req_detail in requirements_data.get("language_requirements", {}).items():
        if isinstance(req_detail, dict):
            for key, value in req_detail.items():
                if value:
                    all_requirements.append(f"{req_type} - {key}: {value}")
        elif req_detail:  # Если просто строка, а не вложенный объект
            all_requirements.append(f"{req_type}: {req_detail}")

    # Обрабатываем стандартные тесты
    for test_name, test_value in requirements_data.get("standardized_tests", {}).items():
        if test_value:
            all_requirements.append(f"{test_name}: {test_value}")

    # Обрабатываем другие требования (например, GPA)
    if requirements_data.get("GPA"):
        all_requirements.append(f"GPA: {requirements_data.get('GPA')}")

    # Добавляем все найденные требования в БД и связываем с программой
    for requirement_text in all_requirements:
        requirement = db.query(Requirement).filter_by(type="General", detail=requirement_text).first()
        if not requirement:
            requirement = Requirement(type="General", detail=requirement_text)
            db.add(requirement)
            db.flush()

        # Связываем requirement с program
        db.execute(program_requirements.insert().values(program_id=program.id, requirement_id=requirement.id))

    db.commit()  # Один коммит в конце для повышения производительности

    print(f"✅ Импортирована программа: {course_title} (с {len(all_requirements)} требованиями)")

def import_all_programs():
    """ Обрабатывает все JSON-файлы в папке DATA_DIR """
    db = SessionLocal()

    try:
        files_processed = 0
        for filename in os.listdir(DATA_DIR):
            if filename.endswith(".json"):
                filepath = os.path.join(DATA_DIR, filename)
                process_json_file(filepath, db)
                files_processed += 1

        if files_processed == 0:
            print("⚠️ В папке нет JSON-файлов для обработки.")

    except Exception as e:
        db.rollback()
        print(f"❌ Ошибка при импорте программ: {e}")
    finally:
        db.close()