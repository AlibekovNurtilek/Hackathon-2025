from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import cast, Float, Date
from datetime import date
import re

from app.database.database import get_db
from app.database.models import Program, University, FieldOfStudy, Subject, Requirement

router = APIRouter(prefix="/programs", tags=["Programs"])


class ProgramSearchFilter(BaseModel):
    program_name: Optional[str] = None
    program_location: Optional[str] = None
    university_name: Optional[str] = None
    university_location: Optional[str] = None
    field_of_study: Optional[str] = None
    subjects: Optional[List[str]] = None
    language: Optional[str] = None
    duration: Optional[str] = None
    mode_of_study: Optional[str] = None
    uni_assist: Optional[str] = None
    ects_max: Optional[float] = None  # Допустим, пользователь вводит как float
    budget: Optional[float] = None  # Максимальный бюджет
    gpa: Optional[float] = None
    toefl: Optional[float] = None
    ielts: Optional[float] = None
    gre: Optional[float] = None
    gmat: Optional[float] = None
    english_level: Optional[str] = None
    german_level: Optional[str] = None


# Словарь для порядковых номеров CEFR-уровней
CEFR_ORDER = {"A1": 1, "A2": 2, "B1": 3, "B2": 4, "C1": 5, "C2": 6}


def extract_float_from_string(value: str) -> Optional[float]:
    """
    Пытается найти в строке первое числовое значение и вернуть его в формате float.
    Если не удаётся найти число, возвращает None.
    Пример: '500 EUR per semester' -> 500.0
    """
    if not value:
        return None
    match = re.search(r"(\d+(\.\d+)?)", value)
    if match:
        return float(match.group(1))
    return None


def compare_or_fallback(db_value_str: str, user_value: Optional[float]) -> bool:
    """
    Пытается сравнить user_value с числом, извлечённым из db_value_str.
    Если в базе нет чёткого числа (extract_float_from_string -> None),
    тогда делаем «мягкую» проверку: если user_value тоже None – считаем, что подходит,
    иначе пытаемся сопоставить (пример: user_value=500, в базе 'около 500 евро' ->
    если есть подстрока '500', можно считать подходящим).

    Возвращает True, если условие выполнено (требование удовлетворено), иначе False.
    """
    # Если в базе значение пустое или "none", считаем, что требования нет
    if not db_value_str or db_value_str.lower() in ["none", "null", ""]:
        return True

    db_number = extract_float_from_string(db_value_str)
    if db_number is not None:
        # Если из строки базы извлекли число, сравниваем
        if user_value is None:
            # Пользователь ничего не ввёл, а в базе есть требование -> не подходит
            return False
        return user_value >= db_number
    else:
        # В базе нет явного числа. Попробуем частичный поиск.
        if user_value is None:
            # Если пользователь не задал значение, считаем, что проходит
            return True
        # Если в строке базы есть подстрока, совпадающая с целой частью user_value,
        # считаем, что это условно подходит (упрощённый вариант).
        # Пример: user_value=500.0 -> '500'
        if str(int(user_value)) in db_value_str:
            return True
        return False


def compare_cefr_levels(db_level_str: str, user_level_str: Optional[str]) -> bool:
    """
    Сравнивает уровень языка, заданный в базе (db_level_str), с пользовательским (user_level_str).
    Если db_level_str пуст, считаем, что требования нет. Если есть, то проверяем:
    - Если db_level_str можно интерпретировать как CEFR (B2), сравниваем порядки.
    - Если нет, делаем частичный поиск по подстроке (например, 'CEFR B2' содержит 'B2').
    """
    if not db_level_str or db_level_str.lower() in ["none", "null", ""]:
        return True

    # Приводим к верхнему регистру и убираем пробелы
    db_level = db_level_str.strip().upper()
    if user_level_str is None:
        # Пользователь ничего не ввёл
        # Если в базе указано требование, проверим, не пустое ли оно
        return False

    user_level = user_level_str.strip().upper()

    # Если оба уровня присутствуют в CEFR_ORDER, сравниваем порядки
    if db_level in CEFR_ORDER and user_level in CEFR_ORDER:
        return CEFR_ORDER[user_level] >= CEFR_ORDER[db_level]
    else:
        # Иначе пытаемся частично сравнить строки
        # Например, если в базе 'CEFR B2', а пользователь ввёл 'B2'
        if user_level in db_level or db_level in user_level:
            return True
        return False


@router.post("/search")
def search_programs(filters: ProgramSearchFilter, db: Session = Depends(get_db)):
    """
    Эндпоинт поиска программ с «мягкими» проверками:
    - Фильтрация по полям программы, университета, направлению, предметам, дедлайну
    - Парсинг строковых значений, если в базе нет чёткого формата
    - Частичный поиск по языковым уровням
    """
    query = db.query(Program)

    # 1. Фильтр по дедлайну
    today = date.today()
    query = query.filter(cast(Program.application_deadline, Date) >= today)

    # 2. Фильтрация по строковым полям Program (частичный поиск через ilike)
    if filters.program_name:
        query = query.filter(Program.name.ilike(f"%{filters.program_name}%"))
    if filters.program_location:
        query = query.filter(Program.location.ilike(f"%{filters.program_location}%"))
    if filters.language:
        query = query.filter(Program.language.ilike(f"%{filters.language}%"))
    if filters.duration:
        query = query.filter(Program.duration.ilike(f"%{filters.duration}%"))
    if filters.mode_of_study:
        query = query.filter(Program.mode_of_study.ilike(f"%{filters.mode_of_study}%"))
    if filters.uni_assist:
        query = query.filter(Program.uni_assist.ilike(f"%{filters.uni_assist}%"))

    # Для ects_max и budget пробуем приводить Program.ects_max, Program.tuition_fees к числу,
    # но если там в базе строка "500 euro", используем cast.
    # (Это базовая проверка: если cast() не сможет привести строку к float, будет ошибка,
    # но частичная логика ниже в Python для требований.)
    if filters.ects_max is not None:
        query = query.filter(cast(Program.ects_max, Float) >= filters.ects_max)
    if filters.budget is not None:
        query = query.filter(cast(Program.tuition_fees, Float) <= filters.budget)

    # 3. Фильтр по университету (строковый поиск через ilike)
    if filters.university_name or filters.university_location:
        query = query.join(Program.university)
        if filters.university_name:
            query = query.filter(University.name.ilike(f"%{filters.university_name}%"))
        if filters.university_location:
            query = query.filter(University.location.ilike(f"%{filters.university_location}%"))

    # 4. Фильтр по направлению (FieldOfStudy)
    if filters.field_of_study:
        query = query.join(Program.fields_of_study).filter(FieldOfStudy.name.ilike(f"%{filters.field_of_study}%"))

    # 5. Фильтр по предметам (Subject)
    if filters.subjects:
        query = query.join(Program.subjects).filter(Subject.name.in_(filters.subjects))

    # 6. Выполняем запрос
    programs = query.distinct().all()

    # 7. Дополнительная «мягкая» проверка требований (GPA, TOEFL, IELTS, GRE, GMAT, уровни языка)
    filtered_programs = []
    for program in programs:
        meets_all = True

        # (a) GPA
        if filters.gpa is not None:
            # Ищем requirement типа "GPA"
            if not any(compare_or_fallback(req.detail, filters.gpa)
                       for req in program.requirements if req.type.lower() == "gpa"):
                # Если нет ни одного подходящего требования, программа не подходит
                meets_all = False

        # (b) GRE
        if filters.gre is not None:
            if not any(compare_or_fallback(req.detail, filters.gre)
                       for req in program.requirements if req.type.lower() == "standardized_test_gre"):
                meets_all = False

        # (c) GMAT
        if filters.gmat is not None:
            if not any(compare_or_fallback(req.detail, filters.gmat)
                       for req in program.requirements if req.type.lower() == "standardized_test_gmat"):
                meets_all = False

        # (d) TOEFL / IELTS -> языковое требование для английского
        # У нас может быть отдельное поле "language_requirement_English"
        # или же конкретные требования "standardized_test_toefl"/"standardized_test_ielts".
        # Для упрощения воспользуемся функцией сравнения уровней + числовых значений.
        # Проверим, есть ли среди requirements что-то типа "language_requirement_english".
        # Если такого требования нет или оно пустое, считаем, что подходит.
        # Если есть, пытаемся сравнить уровень + баллы.

        # Уровень английского
        if not any(compare_cefr_levels(req.detail, filters.english_level)
                   for req in program.requirements if req.type.lower() == "language_requirement_english"):
            meets_all = False

        # TOEFL
        if filters.toefl is not None:
            if not any(compare_or_fallback(req.detail, filters.toefl)
                       for req in program.requirements if req.type.lower() == "standardized_test_toefl"):
                # Если в базе нет такого требования или оно пустое – считаем, что ок.
                # Но если оно есть и не проходит сравнение – не подходит.
                # Для простоты считаем: если requirement.type == "standardized_test_toefl", то проверяем compare_or_fallback
                meets_all = False

        # IELTS
        if filters.ielts is not None:
            if not any(compare_or_fallback(req.detail, filters.ielts)
                       for req in program.requirements if req.type.lower() == "standardized_test_ielts"):
                meets_all = False

        # (e) Немецкий язык
        if not any(compare_cefr_levels(req.detail, filters.german_level)
                   for req in program.requirements if req.type.lower() == "language_requirement_german"):
            meets_all = False

        if meets_all:
            filtered_programs.append(program)

    # 8. Формируем ответ
    result = []
    for program in filtered_programs:
        result.append({
            "id": program.id,
            "name": program.name,
            "program_location": program.location,
            "duration": program.duration,
            "tuition_fees": program.tuition_fees,
            "language": program.language,
            "mode_of_study": program.mode_of_study,
            "uni_assist": program.uni_assist,
            "ects_max": program.ects_max,
            "application_deadline": program.application_deadline.isoformat() if program.application_deadline else None,
            "link": program.link,
            "university": {
                "name": program.university.name if program.university else None,
                "location": program.university.location if program.university else None
            }
        })

    return result
