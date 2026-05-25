from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from src.core.database import Base

class Lead(Base):
    __tablename__ = "leads"

    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    phone_number = Column(String, nullable=False)
    source = Column(String, nullable=False)
    campaign = Column(String, nullable=True)
    ad_group = Column(String, nullable=True)
    landing_page_url = Column(String, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    notes = Column(Text, nullable=True)
    tags = Column(JSON, nullable=True)          # store list of tags
    custom_fields = Column(JSON, nullable=True) # flexible dictionary

    # Relationships
    events = relationship("Event", back_populates="lead")


class Client(Base):
    __tablename__ = "clients"

    id = Column(Integer, primary_key=True, index=True)
    company_name = Column(String, nullable=False)
    contact_name = Column(String, nullable=False)
    contact_email = Column(String, unique=True, index=True, nullable=False)
    contact_phone = Column(String, nullable=True)

    # Relationships
    events = relationship("Event", back_populates="client")


class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    date = Column(DateTime, default=datetime.utcnow)

    # Foreign keys
    lead_id = Column(Integer, ForeignKey("leads.id"), nullable=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=True)

    # Relationships
    lead = relationship("Lead", back_populates="events")
    client = relationship("Client", back_populates="events")
