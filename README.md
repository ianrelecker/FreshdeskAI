# AI-Powered Freshdesk Ticket Assistant

An open-source tool that integrates with Freshdesk to generate intelligent AI responses for support tickets, with specialized tech instructions for support agents.

![Freshdesk AI Assistant](https://github.com/yourusername/freshdesk-ai-assistant/raw/main/screenshots/dashboard.png)

## Features

- **Freshdesk Integration**: Automatically polls for new support tickets with robust rate limiting
- **Dual-Purpose AI Responses**: 
  - Customer-friendly responses for ticket replies
  - Technical instructions for support agents
- **Email-Like Interface**: Conversations displayed in an intuitive email thread format
- **One-Click Generation**: Generate responses or tech instructions with a single click
- **Follow-up Questions**: Automatically generates relevant questions when ticket information is unclear
- **Local Deployment**: Runs on your local machine with minimal setup

## Requirements

- Python 3.9 to 3.12 (Python 3.13 is not supported)
- Freshdesk account with API access
- OpenAI API key

> **Important**: Python 3.13 is not currently supported due to compatibility issues with SQLAlchemy. The application will not run on Python 3.13. Please use Python 3.9 to 3.12.

## Installation

### Quick Setup (Recommended)

1. Clone this repository:
   ```
   git clone https://github.com/yourusername/freshdesk-ai-assistant.git
   cd freshdesk-ai-assistant
   ```

2. Run the quick setup script:
   ```
   ./quick_setup.sh
   ```
   
   This script will:
   - Create a virtual environment
   - Install all dependencies
   - Initialize the database
   
3. Configure your API keys:
   - cp config_example.json config.json
   - Open `config.json`
   - Replace placeholder values with your actual Freshdesk domain, API key, and OpenAI API key

### Manual Setup

If you prefer to set up manually:

1. Clone this repository:
   ```
   git clone https://github.com/yourusername/freshdesk-ai-assistant.git
   cd freshdesk-ai-assistant
   ```

2. Create and activate a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Initialize the database:
   ```
   python -c "from database.models import init_db; init_db()"
   ```

5. Configure your API keys:
   - Open `config.json`
   - Replace placeholder values with your actual Freshdesk domain, API key, and OpenAI API key

## Usage

1. Start the application:
   ```
   python app.py
   ```

2. Open your web browser and navigate to:
   ```
   http://localhost:8001
   ```

3. The dashboard will display your tickets with AI-generated draft responses
4. Review and edit responses as needed
5. Click "Send Response" to post the approved response back to Freshdesk

## How It Works

1. The application polls Freshdesk at regular intervals for new or updated tickets
2. When a new ticket is found, it extracts the relevant information and stores it in the local database
3. You can view the ticket details and click "Generate AI Response" to create a draft response
4. The system analyzes the ticket content and generates a solution-oriented response
5. For common IT issues (password reset, login problems, VPN access, printer issues, etc.), the system provides specific troubleshooting steps
6. You can review, edit, and approve the response through the web interface
7. Once approved, the response is posted back to Freshdesk

> **Note**: Responses are only generated when you explicitly request them by clicking the "Generate AI Response" button on the ticket detail page. This gives you full control over which tickets get AI-generated responses.

## Smart Response Generation

The system uses OpenAI's advanced language models to generate intelligent responses:

- Analyzes ticket subject and description to understand the specific issue
- Generates personalized, context-aware responses addressing the customer by name
- Provides clear, step-by-step troubleshooting instructions tailored to the specific problem
- Creates professional responses with a friendly, helpful tone
- Includes tech instructions for support staff that don't get sent to the customer
- Identifies whether a response is a final solution or needs follow-up
- Generates follow-up questions when ticket information is incomplete or unclear

### Response Refinement

The system now supports response refinement:

- Generate multiple AI responses until you get one that meets your needs
- Provide specific refinement instructions to guide the AI
  - "Make it more concise"
  - "Add more details about VPN setup"
  - "Use a more formal tone"
  - "Include troubleshooting steps for network connectivity"
- Each new response overwrites the previous one in the editor
- No page reloads required when generating new responses

### Tech Instructions

The system now offers two generation options:

1. **Generate Customer Response**: Creates a customer-friendly response that can be sent to the ticket requester
2. **Generate Tech Instructions**: Creates detailed technical instructions specifically for support staff

For tech instructions, the system provides:
   - Detailed technical analysis of the root cause
   - Specific diagnostic steps to confirm the issue
   - Step-by-step technical resolution instructions with commands or settings
   - System requirements, dependencies, and compatibility information
   - Potential complications or edge cases to watch out for
   - Follow-up actions to prevent similar issues
   - Relevant documentation links or knowledge base references

Tech instructions are displayed by default and can be toggled on/off with a button. They are stored separately from the customer response and are never sent to the customer.

### Solution Status

Responses are now classified as:

- **Final Solution**: The AI believes this response fully addresses the customer's issue
- **Needs Follow-up**: The AI has identified that this issue likely requires additional information or steps

## Project Structure

```
freshdesk-ai-assistant/
├── app.py                  # Main application entry point
├── config.json             # Configuration file
├── requirements.txt        # Python dependencies
├── database/               # Database models and operations
├── freshdesk/              # Freshdesk API integration
├── ai/                     # OpenAI integration
├── web/                    # Flask web application
├── static/                 # Static assets (CSS, JS)
└── utils/                  # Utility functions
```

## Customization

- Adjust polling frequency in `config.json`
- Configure ticket processing:
  - Set `freshdesk.ticket_limit` in `config.json` to limit the number of tickets processed (default: 25)
  - Adjust `freshdesk.rate_limit_delay` in `config.json` to control the delay between API requests
- Modify AI prompt templates in `ai/response_generator.py`
- Customize the web interface in the `web/templates` directory

## Troubleshooting

- Check the application logs for error messages
- Ensure your API keys are correctly configured
- Verify your Freshdesk domain is correctly formatted

### Common Issues

#### Freshdesk API Rate Limiting

The application now includes robust rate limiting with exponential backoff and automatic retries. If you still encounter "Too Many Requests" errors from the Freshdesk API, you can adjust these settings in `config.json`:

- `freshdesk.rate_limit_delay` (default: 3.0 seconds): Base delay between API requests
- `freshdesk.retry_delay` (default: 5.0 seconds): Initial delay before retrying after a rate limit error
- `freshdesk.max_retries` (default: 5): Maximum number of retry attempts for rate-limited requests
- `freshdesk.ticket_limit` (default: 10): Maximum number of tickets to process in each polling cycle

The system will automatically use exponential backoff when rate limited, doubling the retry delay after each failed attempt up to a maximum of 60 seconds.

#### OpenAI Integration

The application uses the OpenAI API to generate intelligent, context-aware responses. The system:

- Uses GPT-4o-mini by default for high-quality, nuanced responses
- Generates both customer-facing responses and detailed tech instructions
- Creates human-like, empathetic responses that address customers by name
- Ensures all responses are in plain text format (not markdown)
- Provides graceful error handling if the API is temporarily unavailable

The OpenAI integration has been completely rewritten to:
- Use direct HTTP requests instead of the OpenAI SDK for better reliability
- Send carefully crafted prompts with detailed context about the ticket
- Include specific instructions for generating human-like, helpful responses
- Automatically strip any markdown formatting that might be present
- Handle API errors gracefully with informative error messages

To configure the OpenAI integration:
1. Get an API key from [OpenAI](https://platform.openai.com/)
2. Add your API key to the `config.json` file
3. Optionally change the model in `config.json` (default is "gpt-4o-mini")

## License

This project is open source and available under the MIT License.
