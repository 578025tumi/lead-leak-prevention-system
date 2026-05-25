from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from src.core.database import get_db
from src.models.orm_models import Client

router = APIRouter(prefix="/clients", tags=["Clients"])

@router.post("/")
def create_client(company_name: str, contact_name: str, contact_email: str, contact_phone: str | None = None, db: Session = Depends(get_db)):
    client = Client(company_name=company_name, contact_name=contact_name, contact_email=contact_email, contact_phone=contact_phone)
    db.add(client)
    db.commit()
    db.refresh(client)
    return client

@router.get("/{client_id}")
def read_client(client_id: int, db: Session = Depends(get_db)):
    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    return client

@router.put("/{client_id}")
def update_client(client_id: int, company_name: str, contact_name: str, contact_email: str, contact_phone: str | None = None, db: Session = Depends(get_db)):
    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    client.company_name = company_name
    client.contact_name = contact_name
    client.contact_email = contact_email
    client.contact_phone = contact_phone
    db.commit()
    db.refresh(client)
    return client

@router.delete("/{client_id}")
def delete_client(client_id: int, db: Session = Depends(get_db)):
    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    db.delete(client)
    db.commit()
    return {"detail": "Client deleted"}
