from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
import os

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    # Store in ./data/ so a Railway Volume mounted at /app/data survives deploys.
    # Falls back to the local ./data/ dir for development.
    db_dir = os.getenv("DB_DIR", "./data")
    os.makedirs(db_dir, exist_ok=True)
    DATABASE_URL = f"sqlite:///{db_dir}/inventory.db"

if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

connect_args = {"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
