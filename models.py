from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    components = relationship("Component", back_populates="owner", cascade="all, delete-orphan")


class Component(Base):
    __tablename__ = "components"

    id = Column(Integer, primary_key=True, index=True)
    digikey_pn = Column(String, index=True, nullable=True)
    manufacturer_pn = Column(String, index=True, nullable=True)
    manufacturer = Column(String, nullable=True)
    description = Column(String, nullable=True)
    quantity = Column(Integer, default=0)
    location = Column(String, nullable=True)
    notes = Column(String, nullable=True)
    raw_barcode = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    owner = relationship("User", back_populates="components")
