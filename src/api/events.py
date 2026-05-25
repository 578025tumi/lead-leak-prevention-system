from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from src.core.database import get_db
from src.models.orm_models import Event

router = APIRouter(prefix="/events", tags=["Events"])

@router.post("/")
def create_event(title: str, description: str | None = None, lead_id: int | None = None, client_id: int | None = None, db: Session = Depends(get_db)):
    event = Event(title=title, description=description, lead_id=lead_id, client_id=client_id)
    db.add(event)
    db.commit()
    db.refresh(event)
    return event

@router.get("/{event_id}")
def read_event(event_id: int, db: Session = Depends(get_db)):
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return event

@router.put("/{event_id}")
def update_event(event_id: int, title: str, description: str | None = None, lead_id: int | None = None, client_id: int | None = None, db: Session = Depends(get_db)):
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    event.title = title
    event.description = description
    event.lead_id = lead_id
    event.client_id = client_id
    db.commit()
    db.refresh(event)
    return event

@router.delete("/{event_id}")
def delete_event(event_id: int, db: Session = Depends(get_db)):
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    db.delete(event)
    db.commit()
    return {"detail": "Event deleted"}
