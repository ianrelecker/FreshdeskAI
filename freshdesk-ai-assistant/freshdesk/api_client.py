import os
import json
import logging
import time
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import requests
from requests.auth import HTTPBasicAuth

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class FreshdeskClient:
    """Client for interacting with the Freshdesk API."""
    
    def __init__(self, domain: str, api_key: str):
        """Initialize the Freshdesk API client.
        
        Args:
            domain: Freshdesk domain (e.g., 'yourcompany.freshdesk.com')
            api_key: Freshdesk API key
        """
        self.domain = domain
        self.api_key = api_key
        self.base_url = f"https://{domain}/api/v2"
        self.auth = HTTPBasicAuth(api_key, 'X')
        self.headers = {
            'Content-Type': 'application/json',
        }
        self.last_request_time = 0
        self.rate_limit_delay = 1.0  # Default delay between API requests in seconds
        self.max_retries = 5  # Maximum number of retries for rate-limited requests
        self.retry_delay = 2.0  # Initial retry delay in seconds
        
        # Test the connection
        try:
            self.test_connection()
            logger.info("Successfully connected to Freshdesk API")
        except Exception as e:
            logger.error(f"Failed to connect to Freshdesk API: {str(e)}")
            raise
    
    def _rate_limit(self):
        """Apply rate limiting to API requests."""
        current_time = time.time()
        elapsed = current_time - self.last_request_time
        
        if elapsed < self.rate_limit_delay:
            # Sleep to respect rate limit
            sleep_time = self.rate_limit_delay - elapsed
            logger.debug(f"Rate limiting: sleeping for {sleep_time:.2f} seconds")
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    def _make_request(self, method, url, **kwargs):
        """Make a request to the Freshdesk API with retry logic for rate limiting.
        
        Args:
            method: HTTP method (get, post, put, delete)
            url: Full URL to request
            **kwargs: Additional arguments to pass to requests
            
        Returns:
            Response object
        
        Raises:
            requests.exceptions.RequestException: If the request fails after all retries
        """
        retries = 0
        delay = self.retry_delay
        
        while True:
            # Apply rate limiting
            self._rate_limit()
            
            try:
                # Make the request
                response = getattr(requests, method)(url, **kwargs)
                
                # If successful or not a rate limit error, return the response
                if response.status_code != 429:
                    return response
                
                # If we've reached the maximum number of retries, raise the exception
                if retries >= self.max_retries:
                    response.raise_for_status()
                
                # Get retry-after header if available
                retry_after = response.headers.get('Retry-After')
                if retry_after:
                    try:
                        delay = float(retry_after)
                    except (ValueError, TypeError):
                        # If retry-after is not a valid number, use exponential backoff
                        delay = min(delay * 2, 60)  # Cap at 60 seconds
                else:
                    # Use exponential backoff
                    delay = min(delay * 2, 60)  # Cap at 60 seconds
                
                logger.warning(f"Rate limited by Freshdesk API. Retrying in {delay:.2f} seconds (retry {retries+1}/{self.max_retries})")
                time.sleep(delay)
                retries += 1
                
            except requests.exceptions.RequestException as e:
                # If it's not a rate limit error or we've reached the maximum number of retries, raise the exception
                if not hasattr(e, 'response') or e.response is None or e.response.status_code != 429 or retries >= self.max_retries:
                    raise
                
                # Use exponential backoff
                delay = min(delay * 2, 60)  # Cap at 60 seconds
                logger.warning(f"Rate limited by Freshdesk API. Retrying in {delay:.2f} seconds (retry {retries+1}/{self.max_retries})")
                time.sleep(delay)
                retries += 1
    
    def test_connection(self) -> bool:
        """Test the connection to the Freshdesk API."""
        # Check if domain is still the default value
        if self.domain == "yourcompany.freshdesk.com":
            raise ValueError("Please configure your Freshdesk domain in config.json")
        
        # Check if API key is still the default value
        if self.api_key == "YOUR_FRESHDESK_API_KEY":
            raise ValueError("Please configure your Freshdesk API key in config.json")
        
        try:
            response = self._make_request(
                'get',
                f"{self.base_url}/tickets?per_page=1",
                auth=self.auth,
                headers=self.headers
            )
            response.raise_for_status()
            return True
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 401:
                raise ValueError("Invalid Freshdesk API credentials. Please check your API key in config.json")
            raise
    
    def get_tickets(self, updated_since: Optional[datetime] = None, page: int = 1, per_page: int = 100) -> List[Dict[str, Any]]:
        """Get tickets from Freshdesk, optionally filtered by update time.
        
        Args:
            updated_since: Only return tickets updated since this time
            page: Page number for pagination
            per_page: Number of tickets per page
            
        Returns:
            List of ticket dictionaries
        """
        params = {
            'page': page,
            'per_page': per_page,
            'include': 'requester'
        }
        
        if updated_since:
            # Format datetime to ISO 8601 format
            params['updated_since'] = updated_since.isoformat()
        
        try:
            response = self._make_request(
                'get',
                f"{self.base_url}/tickets",
                auth=self.auth,
                headers=self.headers,
                params=params
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching tickets: {str(e)}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response content: {e.response.content}")
            return []
    
    def get_all_tickets(self, updated_since: Optional[datetime] = None, limit: int = None) -> List[Dict[str, Any]]:
        """Get all tickets, handling pagination automatically.
        
        Args:
            updated_since: Only return tickets updated since this time
            limit: Maximum number of tickets to return (default: None, returns all tickets)
            
        Returns:
            List of all ticket dictionaries
        """
        all_tickets = []
        page = 1
        per_page = 100
        
        while True:
            tickets = self.get_tickets(updated_since, page, per_page)
            if not tickets:
                break
                
            all_tickets.extend(tickets)
            
            # If we have enough tickets or there are no more pages, break
            if limit and len(all_tickets) >= limit:
                # Trim to the exact limit
                all_tickets = all_tickets[:limit]
                break
                
            if len(tickets) < per_page:
                break
                
            page += 1
        
        return all_tickets
    
    def get_ticket(self, ticket_id: int) -> Optional[Dict[str, Any]]:
        """Get a specific ticket by ID.
        
        Args:
            ticket_id: The Freshdesk ticket ID
            
        Returns:
            Ticket dictionary or None if not found
        """
        try:
            response = self._make_request(
                'get',
                f"{self.base_url}/tickets/{ticket_id}",
                auth=self.auth,
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching ticket {ticket_id}: {str(e)}")
            return None
    
    def get_ticket_conversations(self, ticket_id: int) -> List[Dict[str, Any]]:
        """Get conversation history for a ticket.
        
        Args:
            ticket_id: The Freshdesk ticket ID
            
        Returns:
            List of conversation dictionaries
        """
        try:
            response = self._make_request(
                'get',
                f"{self.base_url}/tickets/{ticket_id}/conversations",
                auth=self.auth,
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching conversations for ticket {ticket_id}: {str(e)}")
            return []
    
    def add_note_to_ticket(self, ticket_id: int, body: str, private: bool = False) -> Optional[Dict[str, Any]]:
        """Add a note to a ticket.
        
        Args:
            ticket_id: The Freshdesk ticket ID
            body: The note content
            private: Whether the note is private (not visible to requester)
            
        Returns:
            The created note or None if failed
        """
        data = {
            'body': body,
            'private': private
        }
        
        try:
            response = self._make_request(
                'post',
                f"{self.base_url}/tickets/{ticket_id}/notes",
                auth=self.auth,
                headers=self.headers,
                json=data
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error adding note to ticket {ticket_id}: {str(e)}")
            return None
    
    def reply_to_ticket(self, ticket_id: int, body: str, user_id: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """Reply to a ticket.
        
        Args:
            ticket_id: The Freshdesk ticket ID
            body: The reply content
            user_id: The user ID to use for the reply (optional)
            
        Returns:
            The created reply or None if failed
        """
        data = {
            'body': body,
            'from_email': None  # Use the authenticated API user's email
        }
        
        if user_id:
            data['user_id'] = user_id
        
        try:
            response = self._make_request(
                'post',
                f"{self.base_url}/tickets/{ticket_id}/reply",
                auth=self.auth,
                headers=self.headers,
                json=data
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error replying to ticket {ticket_id}: {str(e)}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response content: {e.response.content}")
            return None
    
    def update_ticket(self, ticket_id: int, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update a ticket.
        
        Args:
            ticket_id: The Freshdesk ticket ID
            data: Dictionary of fields to update
            
        Returns:
            The updated ticket or None if failed
        """
        try:
            response = self._make_request(
                'put',
                f"{self.base_url}/tickets/{ticket_id}",
                auth=self.auth,
                headers=self.headers,
                json=data
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error updating ticket {ticket_id}: {str(e)}")
            return None


def create_client_from_config() -> FreshdeskClient:
    """Create a Freshdesk client using the configuration file."""
    config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config.json')
    
    with open(config_path, 'r') as f:
        config = json.load(f)
    
    domain = config['freshdesk']['domain']
    api_key = config['freshdesk']['api_key']
    
    client = FreshdeskClient(domain, api_key)
    
    # Set rate limit delay from config if available
    if 'rate_limit_delay' in config['freshdesk']:
        client.rate_limit_delay = float(config['freshdesk']['rate_limit_delay'])
        logger.info(f"Setting API rate limit delay to {client.rate_limit_delay} seconds")
    
    # Set retry delay from config if available
    if 'retry_delay' in config['freshdesk']:
        client.retry_delay = float(config['freshdesk']['retry_delay'])
        logger.info(f"Setting API retry delay to {client.retry_delay} seconds")
    
    # Set max retries from config if available
    if 'max_retries' in config['freshdesk']:
        client.max_retries = int(config['freshdesk']['max_retries'])
        logger.info(f"Setting API max retries to {client.max_retries}")
    
    return client
