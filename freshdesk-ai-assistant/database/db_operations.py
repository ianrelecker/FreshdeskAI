from sqlalchemy.orm import Session
from datetime import datetime
from typing import List, Optional, Dict, Any

from .models import Ticket, Response, Conversation, Session as DBSession

def get_session() -> Session:
    """Get a new database session."""
    return DBSession()

# Ticket operations
def create_ticket(session: Session, ticket_data: Dict[str, Any]) -> Ticket:
    """Create a new ticket in the database."""
    ticket = Ticket(
        freshdesk_id=ticket_data['id'],
        subject=ticket_data['subject'],
        description=ticket_data.get('description', ''),
        status=ticket_data.get('status', ''),
        priority=ticket_data.get('priority', 1),
        requester_name=ticket_data.get('requester_name', ''),
        requester_email=ticket_data.get('requester_email', ''),
        created_at=datetime.fromisoformat(ticket_data['created_at'].replace('Z', '+00:00')) if 'created_at' in ticket_data else datetime.utcnow(),
        updated_at=datetime.fromisoformat(ticket_data['updated_at'].replace('Z', '+00:00')) if 'updated_at' in ticket_data else datetime.utcnow(),
        needs_processing=True
    )
    session.add(ticket)
    session.commit()
    session.refresh(ticket)
    return ticket

def get_ticket_by_freshdesk_id(session: Session, freshdesk_id: int) -> Optional[Ticket]:
    """Get a ticket by its Freshdesk ID."""
    return session.query(Ticket).filter(Ticket.freshdesk_id == freshdesk_id).first()

def get_all_tickets(session: Session) -> List[Ticket]:
    """Get all tickets from the database."""
    return session.query(Ticket).order_by(Ticket.freshdesk_id.desc()).all()

def get_tickets_needing_processing(session: Session) -> List[Ticket]:
    """Get all tickets that need AI processing."""
    return session.query(Ticket).filter(Ticket.needs_processing == True).all()

def update_ticket(session: Session, ticket: Ticket, ticket_data: Dict[str, Any]) -> Ticket:
    """Update an existing ticket with new data."""
    for key, value in ticket_data.items():
        if key == 'created_at' or key == 'updated_at':
            value = datetime.fromisoformat(value.replace('Z', '+00:00')) if value else datetime.utcnow()
        if hasattr(ticket, key):
            setattr(ticket, key, value)
    
    session.commit()
    session.refresh(ticket)
    return ticket

def mark_ticket_processed(session: Session, ticket_id: int) -> None:
    """Mark a ticket as processed by the AI."""
    ticket = session.query(Ticket).filter(Ticket.id == ticket_id).first()
    if ticket:
        ticket.needs_processing = False
        session.commit()

# Response operations
def create_response(session: Session, ticket_id: int, draft_content: str, tech_instructions: str = None, 
                   follow_up_questions: str = None, is_final_solution: bool = False) -> Response:
    """Create a new AI-generated response for a ticket."""
    response = Response(
        ticket_id=ticket_id,
        draft_content=draft_content,
        final_content=draft_content,  # Initially the same as draft
        tech_instructions=tech_instructions,
        follow_up_questions=follow_up_questions,
        is_final_solution=is_final_solution,
        is_sent=False,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    session.add(response)
    session.commit()
    session.refresh(response)
    return response

def get_response(session: Session, response_id: int) -> Optional[Response]:
    """Get a response by its ID."""
    return session.query(Response).filter(Response.id == response_id).first()

def get_responses_for_ticket(session: Session, ticket_id: int) -> List[Response]:
    """Get all responses for a specific ticket."""
    return session.query(Response).filter(Response.ticket_id == ticket_id).order_by(Response.created_at.desc()).all()

def update_response(session: Session, response_id: int, final_content: str) -> Optional[Response]:
    """Update the final content of a response."""
    response = session.query(Response).filter(Response.id == response_id).first()
    if response:
        response.final_content = final_content
        response.updated_at = datetime.utcnow()
        session.commit()
        session.refresh(response)
    return response

def update_response_full(session: Session, response_id: int, final_content: str = None, 
                         tech_instructions: str = None, follow_up_questions: str = None,
                         is_final_solution: bool = None) -> Optional[Response]:
    """Update multiple fields of a response."""
    response = session.query(Response).filter(Response.id == response_id).first()
    if response:
        if final_content is not None:
            response.final_content = final_content
        if tech_instructions is not None:
            response.tech_instructions = tech_instructions
        if follow_up_questions is not None:
            response.follow_up_questions = follow_up_questions
        if is_final_solution is not None:
            response.is_final_solution = is_final_solution
        
        response.updated_at = datetime.utcnow()
        session.commit()
        session.refresh(response)
    return response

def mark_response_sent(session: Session, response_id: int) -> Optional[Response]:
    """Mark a response as sent to Freshdesk."""
    response = session.query(Response).filter(Response.id == response_id).first()
    if response:
        response.is_sent = True
        response.sent_at = datetime.utcnow()
        session.commit()
        session.refresh(response)
    return response

# Conversation operations
def add_conversation(session: Session, ticket_id: int, conversation_data: Dict[str, Any]) -> Conversation:
    """Add a conversation entry for a ticket."""
    conversation = Conversation(
        ticket_id=ticket_id,
        freshdesk_id=conversation_data.get('id'),
        body=conversation_data.get('body', ''),
        from_email=conversation_data.get('from_email', ''),
        user_id=conversation_data.get('user_id'),
        created_at=datetime.fromisoformat(conversation_data['created_at'].replace('Z', '+00:00')) if 'created_at' in conversation_data else datetime.utcnow()
    )
    session.add(conversation)
    session.commit()
    session.refresh(conversation)
    return conversation

def get_conversations_for_ticket(session: Session, ticket_id: int) -> List[Conversation]:
    """Get all conversation entries for a specific ticket."""
    return session.query(Conversation).filter(Conversation.ticket_id == ticket_id).order_by(Conversation.created_at).all()

def get_conversation_by_freshdesk_id(session: Session, ticket_id: int, freshdesk_id: int) -> Optional[Conversation]:
    """Get a conversation by its Freshdesk ID and ticket ID."""
    return session.query(Conversation).filter(
        Conversation.ticket_id == ticket_id,
        Conversation.freshdesk_id == freshdesk_id
    ).first()
