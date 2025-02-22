from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database.database import get_db
from app.database.models import Program, FieldOfStudy, Subject, Requirement
from typing import List, Dict
from sqlalchemy.sql import or_

router = APIRouter()

@router.post("/programs/filter", summary="Фильтрация программ по JSON-фильтру")
def filter_programs(filters: Dict, db: Session = Depends(get_db)):
    # 1️⃣ Начинаем с фильтрации по `field_of_study` и `subject`, если они указаны
    query = db.query(Program)

    if filters.get("field_of_study"):
        query = query.join(Program.fields_of_study).filter(FieldOfStudy.name.ilike(f"%{filters['field_of_study']}%"))

    if filters.get("subject"):
        query = query.join(Program.subjects).filter(Subject.name.in_(filters["subject"]))

    # Получаем предварительный список программ после первого фильтра
    programs = query.all()

    # 2️⃣ Теперь проверяем `requirements` программ на соответствие `requirements` пользователя
    filtered_programs = []

    for program in programs:
        program_requirements = {req.type: req.detail for req in program.requirements}

        # ✅ Если у программы нет требований (NULL), то она всегда подходит
        if not program_requirements:
            filtered_programs.append(program)
            continue

        user_requirements = filters.get("requirements", {}).get("language_requirements", {})

        is_valid = True  # Считаем, что программа подходит, пока не найдём несоответствие

        for lang, user_level in user_requirements.items():
            if user_level:  # Если пользователь указал уровень языка
                program_level = program_requirements.get(lang)

                if program_level and user_level not in program_level:
                    is_valid = False
                    break  # Как только найдём несоответствие, выходим

        if is_valid:
            filtered_programs.append(program)

    # 3️⃣ Возвращаем отфильтрованные программы
    return [
        {
            "id": program.id,
            "name": program.name,
            "university": program.university.name if program.university else None,
            "location": program.location,
            "duration": program.duration,
            "tuition_fees": program.tuition_fees,
            "language": program.language,
            "mode_of_study": program.mode_of_study,
            "uni_assist": program.uni_assist,
            "application_deadline": program.application_deadline,
            "link": program.link
        }
        for program in filtered_programs
    ]
