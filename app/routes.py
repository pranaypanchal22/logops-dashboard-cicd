import json
from datetime import datetime, timedelta, timezone
from flask import Blueprint, jsonify, request, render_template, current_app
from sqlalchemy import func
from .db import db
from .models import LogEvent

bp = Blueprint("main", __name__)

ALLOWED_LEVELS = {"INFO", "WARN", "ERROR"}

def parse_iso8601(ts: str) -> datetime:
    # Accepts "2026-01-02T12:34:56Z" or "...+00:00"
    ts = ts.replace("Z", "+00:00")
    return datetime.fromisoformat(ts).astimezone(timezone.utc)

@bp.get("/")
def home():
    return jsonify({
        "name": "LogOps Dashboard",
        "version": current_app.config["APP_VERSION"],
        "endpoints": {
            "dashboard": "/dashboard",
            "ingest": "/api/logs",
            "stats": "/api/stats",
            "health": "/health"
        }
    })

@bp.get("/health")
def health():
    # Simple DB connectivity check
    try:
        db.session.execute(db.select(func.count(LogEvent.id)).limit(1))
        return jsonify({"status": "ok"}), 200
    except Exception as e:
        return jsonify({"status": "degraded", "error": str(e)}), 500

@bp.post("/api/logs")
def ingest_log():
    """
    Accept JSON:
    {
      "timestamp": "2026-01-02T12:34:56Z" (optional; defaults now),
      "level": "INFO|WARN|ERROR",
      "service": "auth-api",
      "message": "something happened",
      "metadata": {...} (optional)
    }
    """
    data = request.get_json(silent=True) or {}
    level = (data.get("level") or "").upper().strip()
    service = (data.get("service") or "").strip()
    message = (data.get("message") or "").strip()
    metadata = data.get("metadata")

    if level not in ALLOWED_LEVELS:
        return jsonify({"error": "Invalid level. Use INFO, WARN, or ERROR."}), 400
    if not service:
        return jsonify({"error": "service is required"}), 400
    if not message:
        return jsonify({"error": "message is required"}), 400

    ts = data.get("timestamp")
    if ts:
        try:
            timestamp = parse_iso8601(ts)
        except Exception:
            return jsonify({"error": "Invalid timestamp format. Use ISO8601 e.g. 2026-01-02T12:34:56Z"}), 400
    else:
        timestamp = datetime.now(timezone.utc)

    event = LogEvent(
        timestamp=timestamp,
        level=level,
        service=service,
        message=message,
        metadata_json=json.dumps(metadata) if metadata is not None else None
    )
    db.session.add(event)
    db.session.commit()

    return jsonify({"status": "ingested", "id": event.id}), 201

@bp.get("/api/stats")
def stats():
    minutes = int(request.args.get("minutes", "60"))
    since = datetime.now(timezone.utc) - timedelta(minutes=minutes)

    total = db.session.query(func.count(LogEvent.id)).filter(LogEvent.timestamp >= since).scalar()
    errors = db.session.query(func.count(LogEvent.id)).filter(
        LogEvent.timestamp >= since, LogEvent.level == "ERROR"
    ).scalar()

    top_services = (
        db.session.query(LogEvent.service, func.count(LogEvent.id).label("cnt"))
        .filter(LogEvent.timestamp >= since)
        .group_by(LogEvent.service)
        .order_by(func.count(LogEvent.id).desc())
        .limit(5)
        .all()
    )

    return jsonify({
        "window_minutes": minutes,
        "since_utc": since.isoformat(),
        "total_events": int(total or 0),
        "error_events": int(errors or 0),
        "top_services": [{"service": s, "count": int(c)} for s, c in top_services]
    })

@bp.get("/dashboard")
def dashboard():
    level = (request.args.get("level") or "").upper().strip()
    service = (request.args.get("service") or "").strip()
    q = (request.args.get("q") or "").strip()
    minutes = int(request.args.get("minutes", "60"))

    since = datetime.now(timezone.utc) - timedelta(minutes=minutes)

    base = db.session.query(LogEvent).filter(LogEvent.timestamp >= since)

    if level in ALLOWED_LEVELS:
        base = base.filter(LogEvent.level == level)
    if service:
        base = base.filter(LogEvent.service.ilike(f"%{service}%"))
    if q:
        base = base.filter(LogEvent.message.ilike(f"%{q}%"))

    recent = base.order_by(LogEvent.timestamp.desc()).limit(50).all()

    # Summary counts
    counts = dict(
        db.session.query(LogEvent.level, func.count(LogEvent.id))
        .filter(LogEvent.timestamp >= since)
        .group_by(LogEvent.level)
        .all()
    )

    # Top services by ERROR count
    top_error_services = (
        db.session.query(LogEvent.service, func.count(LogEvent.id).label("cnt"))
        .filter(LogEvent.timestamp >= since, LogEvent.level == "ERROR")
        .group_by(LogEvent.service)
        .order_by(func.count(LogEvent.id).desc())
        .limit(5)
        .all()
    )

    return render_template(
        "dashboard.html",
        version=current_app.config["APP_VERSION"],
        window_minutes=minutes,
        since=since,
        filters={"level": level, "service": service, "q": q},
        counts={
            "INFO": int(counts.get("INFO", 0)),
            "WARN": int(counts.get("WARN", 0)),
            "ERROR": int(counts.get("ERROR", 0)),
        },
        top_error_services=top_error_services,
        recent=recent,
        allowed_levels=sorted(ALLOWED_LEVELS)
    )
