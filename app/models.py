from datetime import datetime, timezone
from .db import db

class LogEvent(db.Model):
    __tablename__ = "log_events"

    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, nullable=False, index=True)
    level = db.Column(db.String(10), nullable=False, index=True)      # INFO/WARN/ERROR
    service = db.Column(db.String(64), nullable=False, index=True)    # e.g., auth-api
    message = db.Column(db.Text, nullable=False)
    metadata_json = db.Column(db.Text, nullable=True)

    created_at = db.Column(
        db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc)
    )
