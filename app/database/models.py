from sqlalchemy import Column, Integer, String
from app.database.database import Base
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Float, Table, Date
from sqlalchemy.orm import relationship


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    refresh_token = Column(String, nullable=True)  # Добавляем поле


from sqlalchemy import Column, Integer, String, ForeignKey, Table
from sqlalchemy.orm import relationship
from app.database.database import Base

# Ассоциационные таблицы (Many-to-Many)
program_requirements = Table(
    "program_requirements", Base.metadata,
    Column("program_id", Integer, ForeignKey("programs.id"), primary_key=True),
    Column("requirement_id", Integer, ForeignKey("requirements.id"), primary_key=True),
    Column("min_score", String, nullable=True),  # Из Float в String
    Column("is_mandatory", String, nullable=True)  # Из Boolean в String
)

program_fields = Table(
    "program_fields", Base.metadata,
    Column("program_id", Integer, ForeignKey("programs.id"), primary_key=True),
    Column("field_id", Integer, ForeignKey("fields_of_study.id"), primary_key=True)
)

program_subjects = Table(
    "program_subjects", Base.metadata,
    Column("program_id", Integer, ForeignKey("programs.id"), primary_key=True),
    Column("subject_id", Integer, ForeignKey("subjects.id"), primary_key=True)
)

fields_subjects = Table(
    "fields_subjects", Base.metadata,
    Column("field_id", Integer, ForeignKey("fields_of_study.id"), primary_key=True),
    Column("subject_id", Integer, ForeignKey("subjects.id"), primary_key=True)
)

# Таблицы
class University(Base):
    __tablename__ = "universities"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=True)
    location = Column(String, nullable=True)
    
    programs = relationship("Program", back_populates="university")

class Program(Base):
    __tablename__ = "programs"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=True)
    university_id = Column(Integer, ForeignKey("universities.id"), nullable=True)
    location = Column(String, nullable=True)
    duration = Column(String, nullable=True)
    tuition_fees = Column(String, nullable=True)
    language = Column(String, nullable=True)
    mode_of_study = Column(String, nullable=True)
    uni_assist = Column(String, nullable=True)  # Из Boolean в String
    ects_max = Column(String, nullable=True)  # Из Integer в String
    application_deadline = Column(String, nullable=True)  # Из Date в String
    link = Column(String, nullable=True)  # ✅ Добавлено поле link


    university = relationship("University", back_populates="programs")
    requirements = relationship("Requirement", secondary=program_requirements, back_populates="programs")
    fields_of_study = relationship("FieldOfStudy", secondary=program_fields, back_populates="programs")
    subjects = relationship("Subject", secondary=program_subjects, back_populates="programs")

class Requirement(Base):
    __tablename__ = "requirements"
    id = Column(Integer, primary_key=True, index=True)
    type = Column(String, nullable=True)
    detail = Column(String, nullable=True)
    
    programs = relationship("Program", secondary=program_requirements, back_populates="requirements")

class FieldOfStudy(Base):
    __tablename__ = "fields_of_study"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=True)
    
    programs = relationship("Program", secondary=program_fields, back_populates="fields_of_study")
    subjects = relationship("Subject", secondary=fields_subjects, back_populates="fields_of_study")

class Subject(Base):
    __tablename__ = "subjects"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=True)
    
    programs = relationship("Program", secondary=program_subjects, back_populates="subjects")
    fields_of_study = relationship("FieldOfStudy", secondary=fields_subjects, back_populates="subjects")

