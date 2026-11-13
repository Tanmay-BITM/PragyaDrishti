from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Float
from sqlalchemy.orm import relationship
import datetime
from app.core.database import Base

class MLModel(Base):
    __tablename__ = "ml_models"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    task_type = Column(String, nullable=False)
    target_column = Column(String, nullable=True)
    best_algorithm = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    metrics_json = Column(Text, nullable=True)
    feature_importance_json = Column(Text, nullable=True)
    leaderboard_json = Column(Text, nullable=True)
    explanation_text = Column(Text, nullable=True)
    endpoint_url = Column(String, nullable=True)
    status = Column(String, default="ACTIVE")
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    dataset_id = Column(Integer, ForeignKey("datasets.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    owner = relationship("User", back_populates="models")
    dataset = relationship("Dataset", back_populates="ml_models")
