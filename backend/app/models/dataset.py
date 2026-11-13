from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Float
from sqlalchemy.orm import relationship
import datetime
from app.core.database import Base

class Dataset(Base):
    __tablename__ = "datasets"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    filename = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    row_count = Column(Integer, default=0)
    col_count = Column(Integer, default=0)
    file_size_bytes = Column(Integer, default=0)
    quality_score = Column(Float, default=100.0)
    summary_json = Column(Text, nullable=True)
    columns_json = Column(Text, nullable=True)
    cleaned_file_path = Column(String, nullable=True)
    version = Column(Integer, default=1)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    owner = relationship("User", back_populates="datasets")
    ml_models = relationship("MLModel", back_populates="dataset")
