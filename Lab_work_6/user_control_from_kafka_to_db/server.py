import os, json
from kafka import KafkaConsumer
from sqlalchemy import create_engine, Column, Integer, String, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from passlib.hash import bcrypt

# Настройка DB
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@db:5432/postgres")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

class ConferenceUser(Base):
    __tablename__ = "conference_users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)
    __table_args__ = (Index("conference_users_username", "username"),)

Base.metadata.create_all(bind=engine)

# Конфиг KafkaConsumer
bootstrap = os.getenv("KAFKA_BOOTSTRAP", "kafka:9092").split(",")
consumer = KafkaConsumer(
    os.getenv("KAFKA_TOPIC", "conference_users"),
    bootstrap_servers=bootstrap,
    auto_offset_reset="earliest",
    group_id="conference_users_group",
    value_deserializer=lambda v: json.loads(v.decode("utf-8"))
)

def consume_loop():
    for record in consumer:
        data = record.value
        session = SessionLocal()
        try:
            hashed = bcrypt.hash(data["password"])
            user = ConferenceUser(username=data["username"], hashed_password=hashed)
            session.add(user)
            session.commit()
            print("Inserted user:", data["username"])
        except Exception as e:
            session.rollback()
            print("Insert error:", e)
        finally:
            session.close()

if __name__ == "__main__":
    consume_loop()
