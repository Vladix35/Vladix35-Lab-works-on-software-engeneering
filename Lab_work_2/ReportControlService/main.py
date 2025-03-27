from fastapi import FastAPI, HTTPException
from pydantic import BaseModel


class ConferenceReport(BaseModel):
    report_name: str
    speaker: str


app = FastAPI(title="ReportControlAPP")

reports_db = [
    {
        "id": 0,
        "report_name": "Алгоритм детектирования лица Виолы-Джонса",
        "speaker": "Копелиович Михаил"
    },
    {
        "id": 1,
        "report_name": "Метод отбора смазанных и расфокусированных изображений",
        "speaker": "Раскин Антон"
    }]


@app.get(
        "/conference_reports",
        summary="endpoint для получения всех докладов",
        tags=["Взаимодействие с докладами конференции"])
def get_conference_reports():
    return reports_db


@app.get(
        "/conference_reports/{report_id}",
        summary="endpoint для получения доклада по его id",
        tags=["Взаимодействие с докладами конференции"])
def get_conference_reports(report_id: int):
    for conference_report in reports_db:
        if report_id == conference_report["id"]:
            return conference_report
    raise HTTPException(status_code=404, detail="Report not found")


@app.post(
        "/conference_reports",
        summary="endpoint для создания доклада",
        tags=["Взаимодействие с докладами конференции"])
def create_conference_report(conference_report: ConferenceReport):
    reports_db.append({
        "id": len(reports_db) + 1, 
        "report_name": conference_report.report_name,
        "speaker": conference_report.speaker
    })
    return {"success": True}
