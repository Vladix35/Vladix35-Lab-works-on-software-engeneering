from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from kafka import KafkaProducer
import json
import os

app = FastAPI()

# Конфиг KafkaProducer
bootstrap = os.getenv("KAFKA_BOOTSTRAP", "kafka:9092").split(",")
producer = KafkaProducer(
    bootstrap_servers=bootstrap,
    value_serializer=lambda v: json.dumps(v).encode("utf-8")
)
TOPIC = os.getenv("KAFKA_TOPIC", "conference_users")

class UserCreate(BaseModel):
    username: str
    password: str

@app.post("/conference_users/", response_model=dict)
def create_user(user: UserCreate):
    payload = user.dict()
    try:
        producer.send(TOPIC, payload)
        producer.flush()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return {"status": "queued", "user": payload}
