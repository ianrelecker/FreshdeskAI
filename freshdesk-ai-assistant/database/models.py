from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
import datetime
import os
import json

# Load configuration
with open(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config.json'), 'r') as f:
    config = json.load(f)

# Create SQLite database engine
db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'tickets.db')
engine = create_engine(f'sqlite:///{db_path}')
Session = sessionmaker(bind=engine)

Base = declarative_base()

class Ticket(Base):
    """Model representing a Freshdesk ticket."""
    __tablename__ = 'tickets'

    id = Column(Integer, primary_key=True)
    freshdesk_id = Column(Integer, unique=True, nullable=False)
    subject = Column(String(255), nullable=False)
    description = Column(Text)
    status = Column(String(50))
    priority = Column(Integer)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    requester_name = Column(String(100))
    requester_email = Column(String(100))
    needs_processing = Column(Boolean, default=True)
    
    # Relationship with responses
    responses = relationship("Response", back_populates="ticket", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Ticket(id={self.freshdesk_id}, subject='{self.subject}')>"


class Response(Base):
    """Model representing an AI-generated response to a ticket."""
    __tablename__ = 'responses'

    id = Column(Integer, primary_key=True)
    ticket_id = Column(Integer, ForeignKey('tickets.id'), nullable=False)
    draft_content = Column(Text)
    final_content = Column(Text)
    tech_instructions = Column(Text)  # Instructions for tech support, not sent to customer
    follow_up_questions = Column(Text)  # JSON array of follow-up questions when ticket lacks clarity
    is_final_solution = Column(Boolean, default=False)  # Whether this is a final solution or needs further investigation
    is_sent = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    sent_at = Column(DateTime)
    
    # Relationship with ticket
    ticket = relationship("Ticket", back_populates="responses")
    
    def __repr__(self):
        return f"<Response(id={self.id}, ticket_id={self.ticket_id}, is_sent={self.is_sent})>"


class Conversation(Base):
    """Model representing conversation history for a ticket."""
    __tablename__ = 'conversations'

    id = Column(Integer, primary_key=True)
    ticket_id = Column(Integer, ForeignKey('tickets.id'), nullable=False)
    freshdesk_id = Column(Integer)
    body = Column(Text)
    from_email = Column(String(100))
    user_id = Column(Integer)
    created_at = Column(DateTime)
    
    # Relationship with ticket
    ticket = relationship("Ticket")
    
    def __repr__(self):
        return f"<Conversation(id={self.id}, ticket_id={self.ticket_id})>"


def init_db():
    """Initialize the database by creating all tables."""
    Base.metadata.create_all(engine)


if __name__ == "__main__":
    init_db()
    print("Database initialized successfully.")
