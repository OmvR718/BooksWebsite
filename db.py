from sqlalchemy import URL , create_engine
from sqlalchemy.orm import sessionmaker
from models import Base

url_object = URL.create(
    "postgresql+pg8000",
    username="postgres",
    password="omarkassem",  
    host="localhost",
    database="test_db",
)

engine = create_engine(url_object)

SessionLocal=sessionmaker(autocommit=False,autoflush=False,bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

