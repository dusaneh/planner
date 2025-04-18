# New Orch Demo

A sophisticated AI-powered chatbot application for support that analyzes user queries, routes them to appropriate knowledge tools, and delivers high-quality answers with proper citations and source attribution.

## Overview

This application demonstrates an enterprise-grade AI assistant specifically designed for QuickBooks support. It employs a multi-stage processing pipeline where:

1. User queries are analyzed using Google's Gemini LLM to understand intent and context
2. The system determines which specialized knowledge tool should handle the query
3. Simulated knowledge retrieval fetches relevant information chunks
4. A final response is generated, integrating retrieved information with proper citations
5. The entire process is visualized in real-time through an interactive UI with thought process visibility

The system implements business rules for handling sensitive topics (e.g., legal compliance, payroll contributions) and maintains contextual awareness between conversation turns.

## File Structure

```
/
├── main.py                  # FastAPI server, WebSocket handling, and control flow
├── helper2.py               # Core LLM interaction, function simulation, response generation
├── static/                  # Frontend assets
│   ├── script.js            # WebSocket client, UI updates, animations
│   └── style.css            # UI styling and layout
├── templates/               # HTML templates
│   └── index.html           # Main chat interface template with admin panel
├── keys.py                  # (Not included) Google API key configuration
└── README.md                # This documentation file
```

## Technical Architecture

### Backend Components

#### `main.py`
- **FastAPI Application**: Sets up the web server and WebSocket endpoints
- **Conversation State Management**: Maintains chat history and context between turns
- **Processing Pipeline Orchestration**: Coordinates the three-phase processing flow:
  1. **Planning/Routing**: Determines which tools to use for a query
  2. **Function Execution**: Simulates knowledge retrieval from appropriate sources
  3. **Response Generation**: Creates the final response with citations
- **WebSocket Communication**: Handles real-time streaming of thoughts, statuses, and responses
- **Error Handling**: Provides graceful error recovery and user-friendly error messages

#### `helper2.py`
- **Google Generative AI Integration**: Configures and manages the Gemini LLM API
- **Reference Data**: Defines example data structures (user context, business info, available tools)
- **Knowledge Tools**:
  - `payroll_qna_retrieval`: Handles payroll questions with special logic for "contribution" queries
  - `general_product_support_retrieval`: Processes general how-to questions
  - `legal_compliance_retrieval`: Manages legal/compliance queries with standardized responses
  - `user_data_query`: Simulates retrieval of user-specific account data
- **Core LLM Interaction**: Implements structured communication with Gemini via JSON Lines
- **Query Processing Pipeline**:
  - `process_quickbooks_query`: Analyzes query intent and plans function calls
  - `simulate_retrieval_stub`: Performs simulated knowledge retrieval with business rules
  - `generate_final_response`: Synthesizes final responses with proper citation mapping

### Frontend Components

#### `templates/index.html`
- **Application Shell**: Defines the dual-panel layout (chat + admin panel)
- **Initial UI State**: Sets up the welcome message and input controls
- **Admin Panel Structure**: Creates sections for each processing stage (planning, function calls, summarization)
- **Error Display**: Includes dedicated error section for process visibility

#### `static/script.js`
- **WebSocket Client**: Establishes and maintains connection to the server
- **Message Rendering**: Displays user and AI messages with appropriate styling
- **Thinking Process Visualization**: Implements animated display of AI thoughts
- **Admin Panel Updates**: Provides real-time visibility into the processing pipeline
- **UI State Management**: Handles input states, loading indicators, and error displays
- **Animation System**: Manages thought queue processing and fade-in animations
- **Toggle Functionality**: Implements global thinking process visibility controls

#### `static/style.css`
- **Layout System**: Implements the responsive dual-panel interface
- **Message Styling**: Formats user and AI messages with distinct appearances
- **Thinking Process Display**: Styles the collapsible thinking sections with animations
- **Admin Panel Design**: Formats the debugging interface with clear section hierarchy
- **Animation Definitions**: Specifies transitions and fade effects
- **Citation Formatting**: Styles source attribution links and references

## Detailed Process Flow

### 1. Initialization and Connection

1. The server starts with `uvicorn main:app`
2. The frontend loads `index.html` with the chat interface
3. `script.js` establishes a WebSocket connection to the server
4. Upon successful connection, input controls are enabled

### 2. User Query Processing

When a user submits a query:

1. The frontend:
   - Displays the user message in the chat
   - Disables input controls
   - Creates an AI message container with loading indicator
   - Resets the admin panel

2. The WebSocket sends the query to the server (`main.py`)

3. The server:
   - Adds the message to conversation history
   - Starts the three-phase processing pipeline
   - Sends real-time updates via WebSocket

### 3. Planning/Routing Phase

1. `main.py` calls `helper2.process_quickbooks_query()` with:
   - The current user query
   - Conversation history
   - User context and business information
   - Any "sticky" function hint from previous turns

2. The LLM performs a chain-of-thought analysis to understand intent:
   - Each thought is streamed back to the frontend in real-time
   - Thoughts are displayed in the chat and admin panel

3. The LLM determines which function(s) to call:
   - It can select one or more functions or no functions
   - If no functions are selected, it provides a direct explanation

4. The function call plan is sent back to `main.py`

### 4. Function Execution Phase

1. For each planned function call:
   - `main.py` creates an async task to call `helper2.simulate_retrieval_stub()`
   - Function arguments are passed based on the LLM's plan

2. Each function simulation:
   - Applies business rules (e.g., legal handling, contribution detection)
   - Can reject the query with a reason if appropriate
   - Can generate a follow-up question if clarification is needed
   - Can request "sticky" status for the next turn
   - Generates simulated knowledge chunks with source metadata

3. Results are collected and sent to the admin panel in real-time

### 5. Response Generation Phase

1. `main.py` determines the response approach:
   - If a follow-up question was generated, use that directly
   - Otherwise, call `helper2.generate_final_response()` for synthesis

2. For synthesis-based responses:
   - The LLM analyzes all retrieved chunks and rejection reasons
   - Standard warnings are incorporated if applicable
   - Content is synthesized with proper source citations
   - A citation map is generated for the frontend

3. Thoughts from this phase are streamed in real-time

4. The final response package is sent to the frontend:
   - AI message text with citations
   - Citation map for source display
   - Complete thinking process

### 6. Frontend Rendering

1. The frontend processes the final response:
   - Displays the AI message text with formatting
   - Adds source citations with links if applicable
   - Updates the admin panel with complete information
   - Re-enables input controls for the next interaction

2. User can toggle thinking process visibility globally

## Special Features

### Conversational Context Management

- **Sticky Function Hints**: The system can flag a function as "sticky" for the next turn, enhancing follow-up handling
- **Conversation History**: Each turn has access to full conversation history for context

### Business Rule Enforcement

- **Legal Compliance Handling**: Automatic standard responses for potentially sensitive legal queries
- **Payroll Contribution Logic**: Special handling for queries about contributions in payroll
- **Cross-Domain Rejection**: Prevents general support tools from answering payroll/legal questions

### Real-Time Processing Visibility

- **Streaming Thoughts**: All LLM reasoning steps are streamed in real-time
- **Admin Panel**: Provides detailed visibility into each processing stage
- **Rejection Tracking**: Clear flags and explanations for rejected queries
- **Raw Result Inspection**: Expandable details for debugging

### User Experience Enhancements

- **Thinking Process Animation**: Smooth fade-in of thought items
- **Global Thinking Visibility**: Consistent show/hide state across all messages
- **Citation System**: Clean presentation of sources with clickable links
- **Status Updates**: In-line status indicators during processing

## Implementation Details

### LLM Integration

- Uses Google's Gemini 1.5 Flash model via the `google.generativeai` Python SDK
- Implements JSON Lines structured output for reliable parsing
- Employs chain-of-thought prompting for enhanced reasoning
- Handles streaming output for real-time UI updates

### Asynchronous Processing

- FastAPI and WebSockets provide asynchronous request handling
- Multiple function calls are executed concurrently with `asyncio.create_task()`
- Streaming outputs are implemented with async generators
- Error handling is comprehensive across all async operations

### Simulation Logic

- Knowledge retrieval is simulated rather than performing actual lookups
- The system generates plausible content chunks with realistic metadata
- Business rules are enforced during simulation (e.g., legal warnings)
- Rejection logic provides meaningful feedback to users

### UI/UX Design

- Clean, dual-panel interface with responsive layout
- Real-time animations with controlled timing and sequencing
- Collapsible sections with smooth transitions
- Clear visual hierarchy and information organization

## Usage

### Prerequisites

- Python 3.7+ with FastAPI, Uvicorn, and Google Generative AI packages
- Valid Google API key for Gemini access

### Installation

1. Clone the repository
2. Install required packages:
   ```
   pip install fastapi uvicorn google-generativeai
   ```
3. Configure Google API key:
   - Create a `keys.py` file with `google_api_key = "YOUR_API_KEY"` or
   - Update the key directly in `helper2.py`

### Running the Application

1. Start the server:
   ```
   python main.py
   ```
2. Open a browser to `http://localhost:8000`
3. Interact with the QuickBooks Assistant in the chat interface

### Development Notes

- The application runs on port 8000 by default (configurable in `main.py`)
- WebSocket connection issues will be displayed in the chat
- The admin panel provides real-time visibility for debugging
- Function call results can be inspected by expanding details in the admin panel

## Technology Stack

- **Backend**:
  - Python 3.7+
  - FastAPI framework
  - WebSockets for real-time communication
  - Asyncio for concurrent processing
  - Google Generative AI (Gemini) for LLM capabilities

- **Frontend**:
  - Vanilla JavaScript (no frameworks)
  - WebSocket API for real-time updates
  - CSS3 with transitions and animations
  - HTML5 semantic markup

## Extension Points

This application could be extended with:

1. **Real Knowledge Base**: Replace simulation with actual knowledge retrieval
2. **User Authentication**: Add user login and session management
3. **Conversation Persistence**: Save chat history to a database
4. **Additional Tools**: Implement more specialized knowledge functions
5. **Analytics**: Add tracking of query types and tool usage
6. **Feedback Loop**: Implement user feedback collection for responses
7. **Enhanced UI**: Add rich formatting, file uploads, or multimedia responses
