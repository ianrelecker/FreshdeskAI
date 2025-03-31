import logging
import re
import json
from ai.openai_client import generate_response

# Configure logging
logger = logging.getLogger(__name__)

def remove_markdown(text):
    """Remove markdown formatting from text.
    
    Args:
        text: Text that might contain markdown
        
    Returns:
        Plain text with markdown formatting removed
    """
    if not text:
        return text
        
    # Remove heading markers
    text = re.sub(r'^#+\s+', '', text, flags=re.MULTILINE)
    
    # Remove bold/italic markers
    text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
    text = re.sub(r'\*(.+?)\*', r'\1', text)
    text = re.sub(r'__(.+?)__', r'\1', text)
    text = re.sub(r'_(.+?)_', r'\1', text)
    
    # Remove bullet points and replace with standard format
    text = re.sub(r'^\s*[-*+]\s+', '• ', text, flags=re.MULTILINE)
    
    # Remove code blocks and inline code
    text = re.sub(r'```.*?\n(.*?)```', r'\1', text, flags=re.DOTALL)
    text = re.sub(r'`([^`]+)`', r'\1', text)
    
    # Remove blockquotes
    text = re.sub(r'^>\s+', '', text, flags=re.MULTILINE)
    
    # Remove horizontal rules
    text = re.sub(r'^\s*[-*=_]{3,}\s*$', '', text, flags=re.MULTILINE)
    
    # Remove link formatting but keep the text
    text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)
    
    return text

def create_prompt(ticket, conversations):
    """Create a prompt for OpenAI based on ticket details and conversation history.
    
    Args:
        ticket: The ticket to create a prompt for
        conversations: List of conversations for the ticket
        
    Returns:
        Prompt string for OpenAI
    """
    # Get first name for more personalized response
    first_name = ticket.requester_name.split()[0] if ticket.requester_name else "there"
    
    # Basic ticket information with context
    prompt = f"""You are an experienced, empathetic IT support specialist responding to a customer support ticket. Your goal is to provide a helpful, friendly, and professional response that resolves the customer's issue while making them feel valued and understood.

TICKET DETAILS:
Subject: {ticket.subject}
Description: {ticket.description or 'No description provided'}
Customer: {ticket.requester_name} ({ticket.requester_email})

"""
    
    # Add conversation history if available with better formatting
    if conversations:
        prompt += "CONVERSATION HISTORY (most recent last):\n"
        for i, conv in enumerate(conversations):
            sender = conv.from_email or 'Unknown'
            is_customer = sender.lower() == ticket.requester_email.lower() if ticket.requester_email else False
            role = "Customer" if is_customer else "Support Agent"
            prompt += f"--- {role} ({sender}) ---\n{conv.body or 'No content'}\n\n"
    
    # Add detailed instructions for a more human-like response
    prompt += f"""
RESPONSE GUIDELINES:
1. Start with a warm, personalized greeting using the customer's first name ({first_name})
2. Show genuine empathy by acknowledging their specific issue and any frustration they might be experiencing
3. If this is a follow-up conversation, reference previous interactions to show continuity
4. Provide a clear, concise explanation of the issue in non-technical language when possible
5. Offer a comprehensive solution with step-by-step instructions that are easy to follow
6. If multiple solutions are possible, present options and explain the pros/cons of each
7. Anticipate follow-up questions and address them proactively
8. End with a friendly closing that invites further questions if needed
9. Use a conversational, natural tone throughout - write as a helpful human would, not as a formal or robotic response

IMPORTANT FORMATTING INSTRUCTIONS:
- DO NOT use markdown formatting (no *, #, -, >, etc.)
- Use plain text only with standard punctuation
- For lists, use simple numbers or letters followed by a period or parenthesis
- For emphasis, use capitalization or quotation marks instead of bold or italic formatting
- Separate paragraphs with blank lines
- For step-by-step instructions, use simple numbered lists (1., 2., 3., etc.)

Write a response that sounds like it comes from a real person who cares about solving the customer's problem. Be friendly but professional, and focus on being genuinely helpful.
"""
    
    return prompt

def create_tech_instructions_prompt(ticket, conversations):
    """Create a prompt for generating technical instructions for support agents.
    
    Args:
        ticket: The ticket to create a prompt for
        conversations: List of conversations for the ticket
        
    Returns:
        Prompt string for OpenAI
    """
    # Basic ticket information with context
    prompt = f"""You are an experienced IT support specialist creating internal technical instructions for another support agent who needs to solve this customer issue. Provide detailed technical steps and explanations that would help a fellow IT professional resolve this ticket efficiently.

TICKET DETAILS:
Subject: {ticket.subject}
Description: {ticket.description or 'No description provided'}
Customer: {ticket.requester_name} ({ticket.requester_email})

"""
    
    # Add conversation history if available with better formatting
    if conversations:
        prompt += "CONVERSATION HISTORY (most recent last):\n"
        for i, conv in enumerate(conversations):
            sender = conv.from_email or 'Unknown'
            is_customer = sender.lower() == ticket.requester_email.lower() if ticket.requester_email else False
            role = "Customer" if is_customer else "Support Agent"
            prompt += f"--- {role} ({sender}) ---\n{conv.body or 'No content'}\n\n"
    
    # Add detailed instructions for technical guidance
    prompt += """
TECHNICAL INSTRUCTIONS GUIDELINES:
1. Start with a brief summary of the issue from a technical perspective
2. Provide a detailed technical analysis of the likely root cause(s)
3. List specific diagnostic steps the agent should take to confirm the issue
4. Provide step-by-step technical resolution instructions with commands or settings where applicable
5. Include any relevant system requirements, dependencies, or compatibility issues
6. Mention potential complications or edge cases to watch out for
7. Suggest follow-up actions to prevent similar issues in the future
8. Include any relevant documentation links or internal knowledge base references that would be helpful

IMPORTANT FORMATTING INSTRUCTIONS:
- DO NOT use markdown formatting (no *, #, -, >, etc.)
- Use plain text only with standard punctuation
- For lists, use simple numbers or letters followed by a period or parenthesis
- For emphasis, use capitalization or quotation marks instead of bold or italic formatting
- Separate paragraphs with blank lines
- For step-by-step instructions, use simple numbered lists (1., 2., 3., etc.)

Write detailed technical instructions that would be helpful for another IT professional. Focus on technical accuracy and thoroughness rather than customer-friendly language.
"""
    
    return prompt

def generate_tech_instructions(ticket, conversations):
    """Generate technical instructions for a ticket.
    
    Args:
        ticket: The ticket to generate instructions for
        conversations: List of conversations for the ticket
        
    Returns:
        The generated technical instructions text
    """
    try:
        # Create prompt
        prompt = create_tech_instructions_prompt(ticket, conversations)
        
        # Generate response
        response_text = generate_response(prompt)
        
        # Remove any markdown formatting that might still be present
        clean_response = remove_markdown(response_text)
        
        return clean_response
    except Exception as e:
        logger.error(f"Error generating tech instructions: {str(e)}")
        return "Unable to generate technical instructions at this time. Please analyze the ticket manually."

def create_follow_up_questions_prompt(ticket, conversations):
    """Create a prompt for generating follow-up questions when ticket lacks clarity.
    
    Args:
        ticket: The ticket to create a prompt for
        conversations: List of conversations for the ticket
        
    Returns:
        Prompt string for OpenAI
    """
    # Basic ticket information with context
    prompt = f"""You are an experienced IT support specialist analyzing a customer support ticket. Your task is to identify what information is missing to properly resolve this issue, and generate specific follow-up questions to ask the customer.

TICKET DETAILS:
Subject: {ticket.subject}
Description: {ticket.description or 'No description provided'}
Customer: {ticket.requester_name} ({ticket.requester_email})

"""
    
    # Add conversation history if available with better formatting
    if conversations:
        prompt += "CONVERSATION HISTORY (most recent last):\n"
        for i, conv in enumerate(conversations):
            sender = conv.from_email or 'Unknown'
            is_customer = sender.lower() == ticket.requester_email.lower() if ticket.requester_email else False
            role = "Customer" if is_customer else "Support Agent"
            prompt += f"--- {role} ({sender}) ---\n{conv.body or 'No content'}\n\n"
    
    # Add detailed instructions for generating follow-up questions
    prompt += """
FOLLOW-UP QUESTIONS GUIDELINES:
1. Analyze the ticket to identify what critical information is missing to properly diagnose and resolve the issue
2. Focus on technical details, environment information, or steps to reproduce that would help resolve the issue
3. Generate 3-5 specific, clear follow-up questions that would help gather the missing information
4. Questions should be direct, concise, and focused on one piece of information each
5. Avoid yes/no questions - ask open-ended questions that elicit detailed responses
6. Prioritize questions based on their importance for resolving the issue
7. Format your response as a JSON array of strings, with each string being a follow-up question

EXAMPLE RESPONSE FORMAT:
[
  "What version of the operating system are you currently using?",
  "When did you first notice this issue occurring?",
  "Have you made any recent changes to your system before the problem started?",
  "Can you describe the exact error message you're receiving?",
  "Have you already attempted any troubleshooting steps? If so, what were they?"
]

Generate only the JSON array of follow-up questions, nothing else.
"""
    
    return prompt

def extract_follow_up_questions(response_text):
    """Extract follow-up questions from the AI response.
    
    Args:
        response_text: The raw response from the AI
        
    Returns:
        A JSON string containing an array of follow-up questions, or None if parsing fails
    """
    try:
        # Clean up the response text to ensure it's valid JSON
        # Remove any text before the first [ and after the last ]
        json_text = re.search(r'\[(.*)\]', response_text, re.DOTALL)
        if json_text:
            json_array = "[" + json_text.group(1) + "]"
            # Parse the JSON to validate it
            questions = json.loads(json_array)
            # Return the validated JSON as a string
            return json.dumps(questions)
        else:
            # If no JSON array is found, try to extract questions directly
            questions = []
            # Look for numbered questions (1. Question text)
            numbered_questions = re.findall(r'^\d+\.\s+(.+?)$', response_text, re.MULTILINE)
            if numbered_questions:
                questions.extend(numbered_questions)
            
            # If we found questions, return them as JSON
            if questions:
                return json.dumps(questions)
            
            logger.warning("Could not extract follow-up questions from response")
            return None
    except Exception as e:
        logger.error(f"Error extracting follow-up questions: {str(e)}")
        return None

def generate_follow_up_questions(ticket, conversations):
    """Generate follow-up questions for a ticket that lacks clarity.
    
    Args:
        ticket: The ticket to generate questions for
        conversations: List of conversations for the ticket
        
    Returns:
        A JSON string containing an array of follow-up questions, or None if generation fails
    """
    try:
        # Create prompt
        prompt = create_follow_up_questions_prompt(ticket, conversations)
        
        # Generate response
        response_text = generate_response(prompt)
        
        # Extract follow-up questions
        follow_up_questions = extract_follow_up_questions(response_text)
        
        return follow_up_questions
    except Exception as e:
        logger.error(f"Error generating follow-up questions: {str(e)}")
        return None

def generate_ticket_response(ticket, conversations):
    """Generate a response for a ticket.
    
    Args:
        ticket: The ticket to generate a response for
        conversations: List of conversations for the ticket
        
    Returns:
        The generated response text
    """
    try:
        # Create prompt
        prompt = create_prompt(ticket, conversations)
        
        # Generate response
        response_text = generate_response(prompt)
        
        # Remove any markdown formatting that might still be present
        clean_response = remove_markdown(response_text)
        
        return clean_response
    except Exception as e:
        logger.error(f"Error generating response: {str(e)}")
        return "I apologize, but I'm currently unable to generate a response for your ticket. A support representative will review your ticket manually as soon as possible."
