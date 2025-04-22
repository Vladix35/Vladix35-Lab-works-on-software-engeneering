from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel
from pymongo import MongoClient, errors
import json
import os
import time
from typing import List


MONGO_URI = "mongodb://mongodb:27020/?serverSelectionTimeoutMS=5000&socketTimeoutMS=30000"
MAX_RETRIES = 5
RETRY_DELAY = 3


app = FastAPI(
    title="ReportControlService",
    description="API для управления докладами конференции"
)


class ConferenceReport(BaseModel):
    id: int
    report_name: str
    speaker: str


def get_db_connection():
    for attempt in range(MAX_RETRIES):
        try:
            client = MongoClient(MONGO_URI)
            client.admin.command('ping')
            return client['conference_db']
        except errors.ConnectionFailure:
            time.sleep(RETRY_DELAY)
    raise RuntimeError("Ошибка подключения к базе данных")


def get_next_sequence(db, name):
    counter = db.counters.find_one_and_update(
        {'_id': name},
        {'$inc': {'seq': 1}},
        upsert=True,
        return_document=True
    )
    return counter['seq']


def seed_data_from_json(db):
    try:
        if db.reports.count_documents({}) == 0:
            if not os.path.exists("reports.json"):
                raise FileNotFoundError("Файл reports.json не найден")
            
            with open("reports.json", "r", encoding="utf-8") as f:
                data = json.load(f)
                for idx, item in enumerate(data, start=1):
                    item['id'] = idx
                    db.reports.insert_one(item)
                
                db.counters.update_one(
                    {'_id': 'report_id'},
                    {'$set': {'seq': len(data)}},
                    upsert=True
                )
                print("Данные успешно загружены")
    except Exception as e:
        print(f"Ошибка инициализации данных: {str(e)}")
        raise


@app.on_event("startup")
def initialize_database():
    db = get_db_connection()
    seed_data_from_json(db)
    app.state.db = db


@app.get("/conference_reports", response_model=List[ConferenceReport], tags=["Доклады"])
def get_all_reports():
    return list(app.state.db.reports.find({}, {'_id': 0}).sort('id', 1))


@app.get("/conference_reports/{report_id}", response_model=ConferenceReport, tags=["Доклады"])
def get_single_report(report_id: int):
    report = app.state.db.reports.find_one({'id': report_id}, {'_id': 0})
    if not report:
        raise HTTPException(status_code=404, detail="Доклад не найден")
    return report


@app.post("/conference_reports", response_model=ConferenceReport, status_code=201, tags=["Доклады"])
def create_new_report(report: ConferenceReport):
    try:
        report.id = get_next_sequence(app.state.db, 'report_id')
        app.state.db.reports.insert_one(report.dict())
        return app.state.db.reports.find_one({'id': report.id}, {'_id': 0})
    except errors.DuplicateKeyError:
        raise HTTPException(status_code=409, detail="Доклад уже существует")