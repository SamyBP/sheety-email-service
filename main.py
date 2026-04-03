from datetime import datetime
from typing import Any, Optional
import uuid
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import gspread
from google.oauth2.service_account import Credentials


class EmailRequest(BaseModel):
    to: str
    subject: str
    body: str


class EmailResponse(EmailRequest):
    id: uuid.UUID
    queued_at: datetime
    processed_at: Optional[datetime]
    status: str

    @staticmethod
    def of(data: Any) -> "EmailResponse":
        if isinstance(data, EmailRequest):
            return EmailResponse(
                id=uuid.uuid4(),
                to=data.to,
                subject=data.subject,
                body=data.body,
                status="PENDING",
                queued_at=datetime.now(),
                processed_at=None,
            )
        if isinstance(data, list):
            has_processed_at = len(data) == 7

            if len(data) < 6:
                raise ValueError(
                    "Improper spreadheet format. Expecting rows of at least 6 columns and optionaly a 7th"
                    "Expected row format: id | to | subject | body | status | queued_at | processed_at"
                )

            return EmailResponse(
                id=uuid.UUID(data[0]),
                to=data[1],
                subject=data[2],
                body=data[3],
                status=data[4],
                queued_at=data[5],
                processed_at=None if not has_processed_at else data[6],
            )

        raise ValueError(
            f"Improper usage of factory method. Excepted types ('EmailRequest', 'list[str]'). Actual: {type(data)}"
        )

    def as_row(self) -> list:
        return [
            str(self.id),
            self.to,
            self.subject,
            self.body,
            self.status,
            str(self.queued_at) if self.queued_at else "",
            str(self.processed_at) if self.processed_at else "",
        ]


class GSpreadConf(BaseModel):
    spreadheet_name: str
    worksheet_name: str
    credentials_file: str
    google_auth_scopes: list[str] = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]

    @property
    def creds(self):
        return Credentials.from_service_account_file(
            self.credentials_file, scopes=self.google_auth_scopes
        )


class EmailService:

    def __init__(self, config: GSpreadConf) -> None:
        self.sheet_client = gspread.authorize(config.creds)
        self.sheet = self.sheet_client.open(config.spreadheet_name).worksheet(
            config.worksheet_name
        )

    def send(self, payload: EmailRequest) -> EmailResponse:
        _mail = EmailResponse.of(payload)
        row = _mail.as_row()
        self.sheet.append_row(row)
        return _mail

    def get_email_by_id(self, id: uuid.UUID) -> EmailResponse:
        cell = self.sheet.find(str(id))

        if not cell:
            raise HTTPException(
                status_code=404, detail=f"No email with id: {str(id)} was sent"
            )

        row_values = self.sheet.row_values(cell.row)
        return EmailResponse.of(row_values)


app = FastAPI()

config = GSpreadConf(
    spreadheet_name="SheetyEmailService",
    worksheet_name="DISI_2026",
    credentials_file="credentials.json",
)

email_service = EmailService(config)


@app.post("/api/emails", response_model=EmailResponse)
def send_mail(payload: EmailRequest):
    return email_service.send(payload)


@app.get("/api/emails/{id}", response_model=EmailResponse)
def trace_email(id: uuid.UUID):
    return email_service.get_email_by_id(id)
