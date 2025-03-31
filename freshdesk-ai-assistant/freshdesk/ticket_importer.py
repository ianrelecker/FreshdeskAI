import os
import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

from freshdesk.api_client import FreshdeskClient, create_client_from_config
from database.db_operations import (
    get_session, 
    create_ticket, 
    get_ticket_by_freshdesk_id, 
    update_ticket,
    add_conversation,
    get_conversation_by_freshdesk_id
)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TicketImporter:
    """Class for importing tickets from Freshdesk into the local database."""
    
    def __init__(self, freshdesk_client: Optional[FreshdeskClient] = None):
        """Initialize the ticket importer.
        
        Args:
            freshdesk_client: Optional FreshdeskClient instance. If not provided, one will be created.
        """
        self.freshdesk_client = freshdesk_client or create_client_from_config()
        self.last_poll_time = None
        
        # Load configuration
        config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config.json')
        with open(config_path, 'r') as f:
            self.config = json.load(f)
        
        # Get ticket limit from config (default to 25)
        self.ticket_limit = self.config.get('freshdesk', {}).get('ticket_limit', 25)
    
    def poll_for_tickets(self) -> int:
        """Poll Freshdesk for new or updated tickets.
        
        Returns:
            Number of tickets imported or updated
        """
        logger.info("Polling for new or updated tickets...")
        
        # Determine the time range to poll for
        if self.last_poll_time is None:
            # First poll, get tickets from the last 24 hours
            updated_since = datetime.utcnow() - timedelta(hours=24)
        else:
            # Subsequent polls, get tickets since last poll
            updated_since = self.last_poll_time
        
        # Get tickets from Freshdesk, limited to the most recent ones
        tickets = self.freshdesk_client.get_all_tickets(updated_since, limit=self.ticket_limit)
        logger.info(f"Found {len(tickets)} new or updated tickets (limited to {self.ticket_limit})")
        
        # Process each ticket
        processed_count = 0
        for ticket_data in tickets:
            if self._process_ticket(ticket_data):
                processed_count += 1
        
        # Update last poll time
        self.last_poll_time = datetime.utcnow()
        
        logger.info(f"Processed {processed_count} tickets")
        return processed_count
    
    def _process_ticket(self, ticket_data: Dict[str, Any]) -> bool:
        """Process a single ticket.
        
        Args:
            ticket_data: Ticket data from Freshdesk API
            
        Returns:
            True if the ticket was successfully processed, False otherwise
        """
        try:
            # Get a database session
            session = get_session()
            
            # Check if the ticket already exists in our database
            existing_ticket = get_ticket_by_freshdesk_id(session, ticket_data['id'])
            
            # Get the full ticket details to ensure we have the description
            full_ticket = self.freshdesk_client.get_ticket(ticket_data['id'])
            if full_ticket:
                # Update ticket_data with the full ticket details
                ticket_data.update(full_ticket)
            
            # Map numeric status to string status
            status_map = {
                2: 'open',
                3: 'pending',
                4: 'resolved',
                5: 'closed'
            }
            
            # Convert status to string if it's a number
            if 'status' in ticket_data and isinstance(ticket_data['status'], int):
                ticket_data['status'] = status_map.get(ticket_data['status'], 'open')
            
            # Extract requester information
            if 'requester' in ticket_data:
                requester = ticket_data['requester']
                ticket_data['requester_name'] = requester.get('name', '')
                ticket_data['requester_email'] = requester.get('email', '')
            
            if existing_ticket:
                # Update existing ticket
                logger.info(f"Updating existing ticket: {ticket_data['id']}")
                update_ticket(session, existing_ticket, ticket_data)
                ticket_id = existing_ticket.id
            else:
                # Create new ticket
                logger.info(f"Creating new ticket: {ticket_data['id']}")
                new_ticket = create_ticket(session, ticket_data)
                ticket_id = new_ticket.id
            
            # Get and store conversation history
            self._process_conversations(ticket_id, ticket_data['id'])
            
            session.close()
            return True
        except Exception as e:
            logger.error(f"Error processing ticket {ticket_data.get('id', 'unknown')}: {str(e)}")
            return False
    
    def _process_conversations(self, ticket_id: int, freshdesk_id: int) -> None:
        """Process and store conversation history for a ticket.
        
        Args:
            ticket_id: Local database ticket ID
            freshdesk_id: Freshdesk ticket ID
        """
        try:
            # Get conversations from Freshdesk
            conversations = self.freshdesk_client.get_ticket_conversations(freshdesk_id)
            
            if not conversations:
                logger.info(f"No conversations found for ticket {freshdesk_id}")
                return
            
            logger.info(f"Found {len(conversations)} conversations for ticket {freshdesk_id}")
            
            # Get a database session
            session = get_session()
            
            # Store each conversation, but only if it doesn't already exist
            for conversation_data in conversations:
                # Check if this conversation already exists
                if 'id' in conversation_data and conversation_data['id']:
                    existing_conversation = get_conversation_by_freshdesk_id(session, ticket_id, conversation_data['id'])
                    if existing_conversation:
                        logger.debug(f"Conversation {conversation_data['id']} already exists, skipping")
                        continue
                
                # Add the new conversation
                add_conversation(session, ticket_id, conversation_data)
            
            session.close()
        except Exception as e:
            logger.error(f"Error processing conversations for ticket {freshdesk_id}: {str(e)}")


def run_importer() -> int:
    """Run the ticket importer once.
    
    Returns:
        Number of tickets imported or updated
    """
    importer = TicketImporter()
    return importer.poll_for_tickets()


if __name__ == "__main__":
    run_importer()
