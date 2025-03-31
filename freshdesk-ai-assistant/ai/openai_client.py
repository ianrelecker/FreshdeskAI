import os
import json
import logging
import requests
from typing import Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def generate_response(prompt: str) -> str:
    """Generate a response using the OpenAI API directly with requests.
    
    Args:
        prompt: The prompt to send to the API
        
    Returns:
        The generated response text
    """
    try:
        # Get API key from config
        config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config.json')
        with open(config_path, 'r') as f:
            config = json.load(f)
        api_key = config['openai']['api_key']
        
        # API endpoint
        url = "https://api.openai.com/v1/chat/completions"
        
        # Request headers
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        
        # Get model from config or use default
        model = config.get('openai', {}).get('model', "gpt-4o-mini")
        
        # Request payload with improved system message
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": "You are an experienced IT support specialist with excellent communication skills. You excel at explaining technical concepts in simple terms and providing empathetic, human-like responses that make customers feel valued and understood. IMPORTANT: Format your responses as plain text only, not markdown."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.7,  # Slightly higher temperature for more human-like responses
            "max_tokens": 1000   # Allow for longer, more detailed responses
        }
        
        # Make the API request
        response = requests.post(url, headers=headers, json=payload)
        
        # Check for successful response
        if response.status_code == 200:
            response_data = response.json()
            return response_data['choices'][0]['message']['content']
        else:
            logger.error(f"OpenAI API error: {response.status_code} - {response.text}")
            return "I apologize, but I'm currently unable to generate a response for your ticket. A support representative will review your ticket manually as soon as possible."
            
    except Exception as e:
        logger.error(f"Error calling OpenAI API: {str(e)}")
        return "I apologize, but I'm currently unable to generate a response for your ticket. A support representative will review your ticket manually as soon as possible."
