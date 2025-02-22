import re
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends
from sqlalchemy import or_
from app.database.database import get_db
from app.database.models import Program, FieldOfStudy, Subject, Requirement, program_requirements  # ✅ Импортируем program_requirements

router = APIRouter()


def extract_number_from_string(text):
    """Извлекает числовое значение (GPA, GRE, IELTS и т. д.) из строки."""
    if not text:
        return None
    numbers = re.findall(r"\d+\.?\d*", text)  # Ищем числа (с точкой или без)
    return float(numbers[0]) if numbers else None  # Берём первое найденное число


@router.post("/programs/filter", summary="Фильтрация программ по JSON-фильтру")
def filter_programs(filters: dict, db: Session = Depends(get_db)):
    query = db.query(Program)

    # 1️⃣ Фильтр по `location` (учитывает массив значений)
    user_locations = filters.get("course_details", {}).get("location", [])
    if user_locations:
        query = query.filter(
            or_(*[Program.location.ilike(f"%{loc}%") for loc in user_locations])
        )

    # 2️⃣ Фильтр по `field_of_study` и `subject`
    if filters.get("field_of_study"):
        query = query.join(Program.fields_of_study).filter(FieldOfStudy.name.ilike(f"%{filters['field_of_study']}%"))

    if filters.get("subject"):
        query = query.join(Program.subjects).filter(Subject.name.in_(filters["subject"]))

    # Получаем предварительный список программ
    programs = query.all()

    # 3️⃣ Фильтруем по `requirements`
    filtered_programs = []
    user_gpa = filters["requirements"].get("GPA")  # GPA пользователя (может быть None)
    user_gre = filters["requirements"].get("GRE")  # GRE пользователя (может быть None)
    user_language_requirements = filters["requirements"].get("language_requirements", {})

    for program in programs:
        # 4️⃣ Получаем `requirements` этой программы через `program_requirements`
        program_requirements_list = (
            db.query(Requirement)
            .join(program_requirements, program_requirements.c.requirement_id == Requirement.id)  # ✅ Явно указываем связь
            .filter(program_requirements.c.program_id == program.id)
            .all()
        )

        # ✅ Если у программы нет требований → она всегда подходит
        if not program_requirements_list:
            filtered_programs.append(program)
            continue

        is_valid = True  # Флаг соответствия

        # 🔥 5️⃣ Фильтр по `GPA`
        program_gpa = None
        for req in program_requirements_list:
            if "GPA" in req.detail:
                extracted_gpa = extract_number_from_string(req.detail)
                if extracted_gpa:
                    program_gpa = extracted_gpa

        if program_gpa is not None and user_gpa is not None:
            if user_gpa < program_gpa:
                is_valid = False  # ❌ GPA пользователя ниже порога

        # 🔥 6️⃣ Фильтр по `GRE`
        program_gre = None
        gre_required = False  # Флаг, указывающий, нужен ли GRE

        for req in program_requirements_list:
            if "GRE" in req.detail:
                if "recommended" in req.detail.lower():  # GRE: Recommended
                    gre_required = False
                else:
                    extracted_gre = extract_number_from_string(req.detail)
                    if extracted_gre:
                        program_gre = extracted_gre
                        gre_required = True

        if program_gre is not None:
            if user_gre is None or user_gre < program_gre:
                is_valid = False  # ❌ Если GRE обязательный и пользователь не соответствует

        if gre_required and user_gre is None:
            is_valid = False  # ❌ Если GRE обязательный, а пользователь не указал его

        # 🔥 7️⃣ Фильтр по IELTS, TOEFL и другим тестам
        for lang, user_tests in user_language_requirements.items():
            if not isinstance(user_tests, dict):  # Проверяем, что это словарь
                continue
            for test_name, user_score in user_tests.items():
                if user_score:  # Если пользователь указал значение теста
                    for req in program_requirements_list:
                        if test_name in req.detail:
                            extracted_score = extract_number_from_string(req.detail)
                            if extracted_score is not None:
                                if float(user_score) < extracted_score:
                                    is_valid = False  # ❌ Пользователь не проходит по баллам
                                    break

        if is_valid:
            filtered_programs.append(program)

    # 8️⃣ Возвращаем отфильтрованные программы
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
