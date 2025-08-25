from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional, List
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from datetime import datetime
import os

DATABASE_URL_ENV = "DATABASE_URL"

engine = None
SessionLocal = None
current_db_url = None
Base = declarative_base()


class ActivityORM(Base):
    __tablename__ = "activities"
    id = Column(Integer, primary_key=True, index=True)
    actor = Column(String(120), index=True, nullable=False)
    verb = Column(String(60), index=True, nullable=False)
    object = Column(Text, nullable=False)
    target = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)


def _ensure_engine_and_session():
    global engine, SessionLocal, current_db_url
    database_url = os.getenv(DATABASE_URL_ENV, "sqlite:///./activities.db")
    # Reinitialize if first time or env var changed (useful for tests)
    if engine is None or SessionLocal is None or current_db_url != database_url:
        engine = create_engine(
            database_url,
            connect_args={"check_same_thread": False} if database_url.startswith("sqlite") else {},
        )
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        Base.metadata.create_all(bind=engine)
        current_db_url = database_url


def get_db():
    _ensure_engine_and_session()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class ActivityIn(BaseModel):
    actor: str = Field(..., min_length=1, max_length=120)
    verb: str = Field(..., min_length=1, max_length=60)
    object: str = Field(..., min_length=1)
    target: Optional[str] = None


class ActivityOut(ActivityIn):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


app = FastAPI(title="Activities Service")


@app.on_event("startup")
def on_startup():
    _ensure_engine_and_session()


@app.post("/activities", response_model=ActivityOut, status_code=201)
def post_activity(payload: ActivityIn, db: Session = Depends(get_db)):
    record = ActivityORM(
        actor=payload.actor.strip(),
        verb=payload.verb.strip(),
        object=payload.object.strip(),
        target=(payload.target.strip() if payload.target else None),
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


@app.get("/activities", response_model=List[ActivityOut])
def list_activities(
    limit: int = 20,
    actor: Optional[str] = None,
    verb: Optional[str] = None,
    db: Session = Depends(get_db),
):
    limit = max(1, min(limit, 100))
    q = db.query(ActivityORM).order_by(ActivityORM.created_at.desc())
    if actor:
        q = q.filter(ActivityORM.actor == actor)
    if verb:
        q = q.filter(ActivityORM.verb == verb)
    return q.limit(limit).all()

