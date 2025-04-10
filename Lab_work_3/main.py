from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy import create_engine, Column, Integer, String, Index, exc
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import IntegrityError
from pydantic import BaseModel
from passlib.hash import bcrypt
import os
import time

# Настройка SQLAlchemy
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@db/postgres")
engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Модель SQLAlchemy
class ConferenceUser(Base):
    __tablename__ = "conference_users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)

    __table_args__ = (
        Index("conference_users_username", "username"),
    )

# Функция для создания таблиц с повторными попытками
def create_tables_with_retry():
    max_retries = 5
    retry_delay = 2
    
    for attempt in range(max_retries):
        try:
            Base.metadata.create_all(bind=engine)
            print("Database tables created successfully")
            return
        except exc.OperationalError as e:
            if attempt == max_retries - 1:
                raise
            print(f"Connection failed (attempt {attempt + 1}/{max_retries}), retrying in {retry_delay}s...")
            time.sleep(retry_delay)

# Создание таблиц
create_tables_with_retry()

# Модель Pydantic для валидации данных
class UserCreate(BaseModel):
    username: str
    password: str

class UserResponse(BaseModel):
    id: int
    username: str

    class Config:
        from_attributes = True

app = FastAPI()

# Зависимости для получения сессии базы данных
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Утилита для хэширования пароля
def hash_password(password: str) -> str:
    return bcrypt.hash(password)

# CRUD маршруты
@app.post("/conference_users/", response_model=UserResponse, tags=["Контроль пользователей"])
def create_user(conference_user: UserCreate, db: Session = Depends(get_db)):
    hashed_password = hash_password(conference_user.password)
    db_user = ConferenceUser(username=conference_user.username, hashed_password=hashed_password)
    
    try:
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Username already exists")

@app.get("/conference_users/{user_id}", response_model=UserResponse, tags=["Контроль пользователей"])
def get_user(user_id: int, db: Session = Depends(get_db)):
    conference_user = db.query(ConferenceUser).filter(ConferenceUser.id == user_id).first()
    if conference_user is None:
        raise HTTPException(status_code=404, detail="ConferenceUser not found")
    return conference_user

@app.get("/conference_users/", response_model=list[UserResponse], tags=["Контроль пользователей"])
def get_all_conference_users(db: Session = Depends(get_db)):
    conference_users = db.query(ConferenceUser).all()
    return conference_users

# Обработчик для закрытия соединений при завершении
@app.on_event("shutdown")
def shutdown_event():
    engine.dispose()
    print("Database connections closed")

# Инициализация базы данных с тестовыми данными
def init_db():
    test_users = [
        {"username": "Pantelemon", "password": "password123"},
        {"username": "Homelande", "password": "password257"},
    ]

    with SessionLocal() as session:
        for user in test_users:
            try:
                hashed_password = hash_password(user["password"])
                db_user = ConferenceUser(username=user["username"], hashed_password=hashed_password)
                session.add(db_user)
            except IntegrityError:
                session.rollback()
        session.commit()

# Вызов инициализации при старте
init_db()