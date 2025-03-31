import os
import json
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app

from database.db_operations import (
    get_session,
    get_all_tickets,
    get_ticket_by_freshdesk_id,
    get_responses_for_ticket,
    get_conversations_for_ticket,
    update_response,
    update_response_full,
    mark_response_sent,
    create_response,
    mark_ticket_processed
)
from database.models import Ticket
from freshdesk.api_client import create_client_from_config

# Create blueprint
bp = Blueprint('main', __name__)

# Set up logging
logger = logging.getLogger(__name__)

@bp.route('/')
def index():
    """Render the dashboard page."""
    # Get all tickets from the database
    session = get_session()
    tickets = get_all_tickets(session)
    
    # Prepare data for the template
    ticket_data = []
    for ticket in tickets:
        # Get the latest response for this ticket
        responses = get_responses_for_ticket(session, ticket.id)
        latest_response = responses[0] if responses else None
        
        ticket_data.append({
            'id': ticket.id,
            'freshdesk_id': ticket.freshdesk_id,
            'subject': ticket.subject,
            'status': ticket.status,
            'requester_name': ticket.requester_name,
            'created_at': ticket.created_at,
            'updated_at': ticket.updated_at,
            'has_response': latest_response is not None,
            'response_sent': latest_response.is_sent if latest_response else False
        })
    
    session.close()
    
    return render_template('dashboard.html', tickets=ticket_data)

@bp.route('/ticket/<int:freshdesk_id>')
def ticket_detail(freshdesk_id):
    """Render the ticket detail page."""
    # Get the ticket from the database
    session = get_session()
    ticket = get_ticket_by_freshdesk_id(session, freshdesk_id)
    
    if not ticket:
        session.close()
        flash(f"Ticket {freshdesk_id} not found", "error")
        return redirect(url_for('main.index'))
    
    # Get conversations for this ticket
    conversations = get_conversations_for_ticket(session, ticket.id)
    
    # Get responses for this ticket
    responses = get_responses_for_ticket(session, ticket.id)
    latest_response = responses[0] if responses else None
    
    session.close()
    
    return render_template(
        'ticket_detail.html',
        ticket=ticket,
        conversations=conversations,
        response=latest_response
    )

@bp.route('/api/response/<int:response_id>', methods=['PUT'])
def update_response_api(response_id):
    """API endpoint to update a response."""
    data = request.json
    if not data or 'content' not in data:
        return jsonify({'error': 'Missing content field'}), 400
    
    session = get_session()
    response = update_response(session, response_id, data['content'])
    session.close()
    
    if not response:
        return jsonify({'error': 'Response not found'}), 404
    
    return jsonify({'success': True, 'response': {
        'id': response.id,
        'content': response.final_content,
        'updated_at': response.updated_at.isoformat()
    }})

@bp.route('/api/response/<int:response_id>/send', methods=['POST'])
def send_response_api(response_id):
    """API endpoint to send a response to Freshdesk."""
    session = get_session()
    response = update_response(session, response_id, request.json.get('content', ''))
    
    if not response:
        session.close()
        return jsonify({'error': 'Response not found'}), 404
    
    # Get the ticket for this response
    ticket = response.ticket
    
    # Create Freshdesk client
    freshdesk_client = create_client_from_config()
    
    # Send the response to Freshdesk
    result = freshdesk_client.reply_to_ticket(
        ticket.freshdesk_id,
        response.final_content
    )
    
    if result:
        # Mark the response as sent
        mark_response_sent(session, response_id)
        session.close()
        return jsonify({'success': True})
    else:
        session.close()
        return jsonify({'error': 'Failed to send response to Freshdesk'}), 500

@bp.route('/api/tickets/refresh', methods=['POST'])
def refresh_tickets_api():
    """API endpoint to manually trigger ticket refresh."""
    from freshdesk.ticket_importer import run_importer
    
    try:
        # Run the importer only
        imported = run_importer()
        
        # Note: Response generation is now manual only, triggered by user action
        
        return jsonify({
            'success': True,
            'imported': imported,
            'processed': 0  # Always 0 since we don't auto-generate responses
        })
    except Exception as e:
        logger.error(f"Error refreshing tickets: {str(e)}")
        return jsonify({
            'success': False,
            'error': f"Error refreshing tickets: {str(e)}"
        }), 500

@bp.route('/api/tickets/<int:ticket_id>/generate_response', methods=['POST'])
def generate_response_api(ticket_id):
    """API endpoint to generate an AI response for a specific ticket."""
    from ai.response_generator import generate_ticket_response, generate_follow_up_questions
    
    # Get a database session
    session = get_session()
    
    try:
        # Get the ticket
        ticket = session.query(Ticket).filter(Ticket.id == ticket_id).first()
        
        if not ticket:
            return jsonify({
                'success': False,
                'error': f"Ticket {ticket_id} not found"
            }), 404
        
        # Get conversations for this ticket
        conversations = get_conversations_for_ticket(session, ticket.id)
        
        # Generate response directly - now returns a simple string
        response_text = generate_ticket_response(ticket, conversations)
        
        # Generate follow-up questions if the ticket lacks clarity
        follow_up_questions = generate_follow_up_questions(ticket, conversations)
        
        # Check if there's an existing response that's not sent
        existing_responses = get_responses_for_ticket(session, ticket.id)
        if existing_responses and not existing_responses[0].is_sent:
            # Update the existing response
            response = update_response_full(
                session, 
                existing_responses[0].id, 
                final_content=response_text,
                tech_instructions="", # No tech instructions
                follow_up_questions=follow_up_questions,
                is_final_solution=False # Default to false
            )
        else:
            # Store the response as a new one
            response = create_response(
                session, 
                ticket.id, 
                response_text,
                tech_instructions="", # No tech instructions
                follow_up_questions=follow_up_questions,
                is_final_solution=False # Default to false
            )
        
        # Mark the ticket as processed
        mark_ticket_processed(session, ticket.id)
        
        return jsonify({
            'success': True,
            'response': {
                'id': response.id,
                'content': response.final_content,
                'follow_up_questions': follow_up_questions
            }
        })
    except Exception as e:
        logger.error(f"Error generating response: {str(e)}")
        return jsonify({
            'success': False,
            'error': f"Error generating response: {str(e)}"
        }), 500
    finally:
        # Always close the session
        session.close()

@bp.route('/api/tickets/<int:ticket_id>/generate_tech_instructions', methods=['POST'])
def generate_tech_instructions_api(ticket_id):
    """API endpoint to generate technical instructions for a specific ticket."""
    from ai.response_generator import generate_tech_instructions, generate_follow_up_questions
    
    # Get a database session
    session = get_session()
    
    try:
        # Get the ticket
        ticket = session.query(Ticket).filter(Ticket.id == ticket_id).first()
        
        if not ticket:
            return jsonify({
                'success': False,
                'error': f"Ticket {ticket_id} not found"
            }), 404
        
        # Get conversations for this ticket
        conversations = get_conversations_for_ticket(session, ticket.id)
        
        # Generate tech instructions
        tech_instructions = generate_tech_instructions(ticket, conversations)
        
        # Generate follow-up questions if the ticket lacks clarity
        follow_up_questions = generate_follow_up_questions(ticket, conversations)
        
        # Generate a placeholder response for the customer
        placeholder_response = "This is a placeholder response. Please edit before sending to the customer."
        
        # Check if there's an existing response that's not sent
        existing_responses = get_responses_for_ticket(session, ticket.id)
        if existing_responses and not existing_responses[0].is_sent:
            # Update the existing response
            response = update_response_full(
                session, 
                existing_responses[0].id, 
                final_content=placeholder_response,
                tech_instructions=tech_instructions,
                follow_up_questions=follow_up_questions,
                is_final_solution=False
            )
        else:
            # Store the response as a new one
            response = create_response(
                session, 
                ticket.id, 
                placeholder_response,
                tech_instructions=tech_instructions,
                follow_up_questions=follow_up_questions,
                is_final_solution=False
            )
        
        # Mark the ticket as processed
        mark_ticket_processed(session, ticket.id)
        
        return jsonify({
            'success': True,
            'response': {
                'id': response.id,
                'content': placeholder_response,
                'tech_instructions': tech_instructions,
                'follow_up_questions': follow_up_questions
            }
        })
    except Exception as e:
        logger.error(f"Error generating tech instructions: {str(e)}")
        return jsonify({
            'success': False,
            'error': f"Error generating tech instructions: {str(e)}"
        }), 500
    finally:
        # Always close the session
        session.close()
