from sqlalchemy import Column, Integer, String, DateTime, Text, Float, ForeignKey
from sqlalchemy.orm import relationship
import datetime
from app.core.database import Base
from app.models.report import Report

class Student(Base):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, index=True)
    student_code = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String, nullable=False)
    department = Column(String, nullable=False, default="Computer Science")
    attendance_pct = Column(Float, default=90.0)
    avg_marks = Column(Float, default=85.0)
    projects_count = Column(Integer, default=3)
    certificates_json = Column(Text, nullable=True)
    performance_history_json = Column(Text, nullable=True)
    face_embedding_json = Column(Text, nullable=True)
    avatar_url = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
