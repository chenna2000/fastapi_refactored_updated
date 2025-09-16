from sqlalchemy import create_engine # type: ignore
from sqlalchemy.ext.declarative import declarative_base # pyright: ignore[reportMissingImports]
from sqlalchemy.orm import sessionmaker # type: ignore
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL is None:
    raise ValueError("DATABASE_URL environment variable is not set.")

engine = create_engine("mysql+mysqlconnector://root:root@localhost:3306/test_chat")
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()