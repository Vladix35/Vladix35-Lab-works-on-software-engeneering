from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy import create_engine, Column, Integer, String, Index, exc
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import IntegrityError
from pydantic import BaseModel
from passlib.hash import bcrypt
import os
import time
import redis
import json


DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@db/postgres")
engine = create_engine(DATABASE_URL)

REDIS_URL = os.getenv("REDIS_URL", "redis://cache:6379/0")
redis_client = redis.from_url(REDIS_URL, decode_responses=True)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class ConferenceUser(Base):
    __tablename__ = "conference_users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)

    __table_args__ = (
        Index("conference_username", "username"),
    )

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

create_tables_with_retry()

class UserCreate(BaseModel):
    username: str
    password: str

class UserResponse(BaseModel):
    id: int
    username: str

    class Config:
        from_attributes = True

app = FastAPI()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def hash_password(password: str) -> str:
    return bcrypt.hash(password)

@app.post("/conference_users/", response_model=UserResponse, tags=["Контроль пользователей"])
def create_user(conference_user: UserCreate, db: Session = Depends(get_db)):
    hashed_password = hash_password(conference_user.password)
    db_user = ConferenceUser(username=conference_user.username, hashed_password=hashed_password)
    
    try:
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        # redis_client.delete("all_users")
        return db_user
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Username already exists")

@app.get("/conference_users/{user_id}", response_model=UserResponse, tags=["Контроль пользователей"])
def get_user(user_id: int, db: Session = Depends(get_db)):
    # cache_key = f"conference_user:{user_id}"
    # cached = redis_client.get(cache_key)
    # if cached:
    #     return json.loads(cached)
    
    user = db.query(ConferenceUser).filter(ConferenceUser.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="ConferenceUser not found")
    
    # user_data = UserResponse.from_orm(user).dict()
    # redis_client.setex(cache_key, 180, json.dumps(user_data))
    return user

@app.get("/conference_users/", response_model=list[UserResponse], tags=["Контроль пользователей"])
def get_all_conference_users(db: Session = Depends(get_db)):
    # cached = redis_client.get("all_users")
    # if cached:
    #     return json.loads(cached)
    
    users = db.query(ConferenceUser).all()
    # users_data = [UserResponse.from_orm(u).dict() for u in users]
    # redis_client.setex("all_users", 180, json.dumps(users_data))
    return users

@app.on_event("shutdown")
def shutdown_event():
    engine.dispose()
    print("Database connections closed")

def init_db():
    test_users = [
        {"username": "Pantelemon", "password": "password123"},
        {"username": "Homelande", "password": "password257"},
    ]

    with SessionLocal() as session:
        for user in test_users:
            try:
                exists = session.query(ConferenceUser.id).filter_by(username=user["username"]).first()
                if not exists:
                    hashed_password = hash_password(user["password"])
                    db_user = ConferenceUser(
                        username=user["username"], 
                        hashed_password=hashed_password
                    )
                    session.add(db_user)
                    session.commit()
            except IntegrityError:
                session.rollback()
                print(f"User {user['username']} already exists, skipping...")

init_db()