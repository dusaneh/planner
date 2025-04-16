# plannerv2/routers/chatbot.py

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
import json
import asyncio
import time
from typing import List, Dict, Any, Optional
import random

from plannerv2.core.config_manager import load_json_config
from plannerv2.models.content import ContentConfig
from plannerv2.models.tool import ToolData
import plannerv2.helper as hlp

router = APIRouter()

message_history = []

# Connected WebSocket clients
connected_clients = set()

@router.get("/chat", response_class=HTMLResponse)
async def chat_page():
    """
    Render the chatbot UI page with the 3-panel layout.
    """
    return HTMLResponse(content=html_content)

@router.websocket("/chat/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint to handle real-time chat communication.
    """
    await websocket.accept()
    connected_clients.add(websocket)
    
    try:
        while True:
            # Wait for messages from the client
            data = await websocket.receive_text()
            user_input = json.loads(data)
            user_message = user_input.get("message", "")
            
            if not user_message.strip():
                continue
                
            # Process the message and get response
            await process_message(websocket, user_message)
            
    except WebSocketDisconnect:
        connected_clients.remove(websocket)

async def process_message(websocket: WebSocket, message: str):
    """
    Process user message and generate responses with simulated async processing.
    """

    # 1. Send acknowledgment of user message
    await websocket.send_json({
        "type": "user_message",
        "message": message
    })
    
    # 2. Simulate processing steps with updates to the knowledge panel
    await websocket.send_json({
        "type": "knowledge_update",
        "message": "Analyzing your question..."
    })
    
    # 3. Search content knowledge base
    content_items = search_content(message)
    if content_items:
        await websocket.send_json({
            "type": "knowledge_update",
            "message": f"Found {len(content_items)} relevant content items in knowledge base."
        })
        # Show content items in knowledge panel
        for item in content_items:
            await websocket.send_json({
                "type": "knowledge_update",
                "message": f"<div class='content-item'><strong>{item['title']}</strong><p>{item['body'][:100]}...</p></div>"
            })
    else:
        await websocket.send_json({
            "type": "knowledge_update",
            "message": "No exact matches found in knowledge base. Generating response..."
        })
    
    
    # 4. Update execution plan panel with a visualization
    plan_data = generate_execution_plan(message)
    await websocket.send_json({
        "type": "execution_plan",
        "data": plan_data
    })
    
    # 5. Generate and send the final bot response
    response = generate_response(message, content_items)
    
##############################################################################################
    # Define your structured output model:
    from pydantic import BaseModel, Field


    import helper as hlp

    # Load all configurations
    configs = hlp.load_all_configs()

    # Access individual configs
    planner_config = configs["planner"]
    user_data = configs["user_data"]  # This is the parsed user_json as a dict
    tools = configs["tools"]
    content_items = configs["content"]["items"]

    # Use the configuration data...
    planner_mode = planner_config.get("mode", "fast")
    combined_result = hlp.generate_schema_for_tools(tools)

    class StructuredOutput(BaseModel):
        joke: str = Field(..., description="Your sarcastic joke about the user's question (required)")
        bot_reply: str = Field(None, description="your final reply, serious")
        conversation_length: int = Field(..., description="number of turns in the conversation so far")

    # ----- Usage Example -----
    system_prompt = """You are a helpful product support chatbot for Intuit Quickbooks. You have access to the chat history with the user and you should provide output in strict JSON mode according to the following schema:
    {combined_result}
    """

    # Example conversation history with proper format for the direct API approach
    message_history.append({"role": "user", "content": message})

    # Replace with your actual Google API key

    output_dict = hlp.generate_structured_analysis(
        StructuredOutput,
        message,
        message_history,
        hlp.google_api_key,
        system_prompt
    )

    bot_reply = output_dict.get("structured_output").bot_reply

    message_history.append({"role": "assistant", "content": bot_reply})

    await websocket.send_json({
        "type": "knowledge_update",
        "message": "User info: " + str(user_region)+ " and planner mode: " + str(planner_mode['mode'])
    })
    await websocket.send_json({
        "type": "knowledge_update",
        "message": "Number of turns in the covo so far: " + str(output_dict.get("structured_output").conversation_length)
    })
    await websocket.send_json({
        "type": "knowledge_update",
        "message": "A little joke?: " + str(output_dict.get("structured_output").joke)
    })

    if "error" in output_dict:
        print("\nError:", output_dict.get("error"))
        print("Raw Response:", output_dict.get("raw_response"))

##############################################################################################
    await websocket.send_json({
        "type": "bot_message",
        "message": bot_reply
    })
    
    # 6. Final knowledge update
    await websocket.send_json({
        "type": "knowledge_update",
        "message": "<div class='processing-complete'>✓ Processing complete</div>"
    })

def search_content(query: str) -> List[Dict[str, Any]]:
    """
    Search the content database for relevant items based on the query.
    Returns a list of matching content items.
    """
    # Load content from config
    content_data = load_json_config("content.json")
    if not content_data or "items" not in content_data:
        return []
    
    content_model = ContentConfig(**content_data)
    
    # Simple keyword matching (this can be enhanced with vector search or other techniques)
    matches = []
    query_lower = query.lower()
    
    for item in content_model.items:
        # Check if query matches any of the query strings
        if any(q.lower() in query_lower for q in item.query_strings):
            matches.append({
                "title": item.title,
                "body": item.body,
                "index_name": item.index_name,
                "tagging_json": item.tagging_json
            })
        # If no direct match, check for keywords in title or body
        elif query_lower in item.title.lower() or query_lower in item.body.lower():
            matches.append({
                "title": item.title,
                "body": item.body, 
                "index_name": item.index_name,
                "tagging_json": item.tagging_json
            })
    
    return matches

def generate_execution_plan(query: str) -> Dict[str, Any]:
    """
    Generate a visualization plan based on the query.
    Returns data for the execution plan visualization.
    """
    # Load tools from config
    tools_data = load_json_config("tools.json")
    
    # Create a mock execution plan
    tools = []
    if isinstance(tools_data, list):
        for tool_data in tools_data[:2]:  # Just use the first couple tools
            tool = ToolData(**tool_data)
            tools.append({
                "name": tool.name,
                "priority": tool.priority,
                "selected": random.choice([True, False])  # Randomly select tools for the mock
            })
    
    # Add some fixed nodes for the plan
    plan = {
        "nodes": [
            {"id": "user_query", "name": "User Query", "type": "input"},
            {"id": "planner", "name": "Query Planner", "type": "process"},
        ],
        "links": [
            {"source": "user_query", "target": "planner"}
        ]
    }
    
    # Add tools to the plan
    for i, tool in enumerate(tools):
        tool_id = f"tool_{i}"
        plan["nodes"].append({
            "id": tool_id,
            "name": tool["name"],
            "type": "tool",
            "selected": tool["selected"],
            "priority": tool["priority"]
        })
        plan["links"].append({
            "source": "planner",
            "target": tool_id,
            "value": 10 - (tool["priority"] // 10)  # Thicker lines for higher priority
        })
        
    # Add response node
    plan["nodes"].append({"id": "response", "name": "Final Response", "type": "output"})
    
    # Connect selected tools to response
    for i, tool in enumerate(tools):
        if tool["selected"]:
            plan["links"].append({
                "source": f"tool_{i}",
                "target": "response"
            })
    
    return plan

def generate_response(query: str, content_items: List[Dict[str, Any]]) -> str:
    """
    Generate a response based on the user query and any matched content.
    """
    if "payroll" in query.lower():
        if content_items:
            # Use content from knowledge base
            content = content_items[0]["body"]
            return f"Based on our knowledge base: {content}"
        else:
            return "To add payroll features, you'll need to navigate to the Settings menu, then select 'Payroll Configuration'. From there, you can follow the step-by-step wizard to set up your payroll system."
    
    elif "tax" in query.lower():
        return "For tax-related questions, I recommend using our TaxToolz feature. Would you like me to explain how to access and use this tool?"
    
    elif "tool" in query.lower() or "config" in query.lower():
        return "Tools can be configured in the admin panel. Navigate to the Tools tab and you can add, edit, or delete tools as needed. Each tool has properties like priority, disambiguation level, and whether it can be overridden."
    
    elif "help" in query.lower():
        return "I'm your assistant bot! I can help with questions about payroll, taxes, and system configuration. Try asking something specific about these topics."
    
    else:
        return "I'm not sure I understand your question. Could you provide more details or rephrase? I'm best at helping with payroll setup, tax questions, and system configuration."

# HTML content for the chat UI
html_content = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PlannerV2 Chatbot</title>
    <script src="https://d3js.org/d3.v7.min.js"></script>
    <style>
        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }
        
        body {
            background-color: #f5f5f5;
            height: 100vh;
            display: flex;
            flex-direction: column;
        }
        
        .navbar {
            background-color: #2c3e50;
            color: white;
            padding: 1rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        
        .container {
            display: flex;
            flex: 1;
            height: calc(100vh - 60px);
            overflow: hidden;
        }
        
        .panel {
            display: flex;
            flex-direction: column;
            background: white;
            border-radius: 5px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            margin: 1rem;
            overflow: hidden;
        }
        
        .panel-header {
            padding: 0.75rem;
            background: #34495e;
            color: white;
            font-weight: bold;
            border-top-left-radius: 5px;
            border-top-right-radius: 5px;
        }
        
        .knowledge-panel {
            width: 25%;
            max-width: 400px;
        }
        
        .chat-panel {
            flex: 1;
            max-width: 800px;
            margin: 1rem auto;
        }
        
        .execution-panel {
            width: 25%;
            max-width: 400px;
        }
        
        .panel-content {
            flex: 1;
            overflow-y: auto;
            padding: 1rem;
        }
        
        .knowledge-content {
            display: flex;
            flex-direction: column;
            font-size: 0.9rem;
        }
        
        .knowledge-content > div {
            margin-bottom: 0.5rem;
            padding: 0.5rem;
            border-radius: 3px;
        }
        
        .processing-step {
            background-color: #f8f9fa;
            border-left: 3px solid #6c757d;
        }
        
        .content-item {
            background-color: #e3f2fd;
            border-left: 3px solid #2196f3;
            padding: 0.5rem;
            margin-bottom: 0.5rem;
        }
        
        .processing-complete {
            color: #28a745;
            font-weight: bold;
        }
        
        .chat-content {
            display: flex;
            flex-direction: column;
        }
        
        .message {
            max-width: 80%;
            padding: 0.75rem;
            margin-bottom: 1rem;
            border-radius: 1rem;
            position: relative;
            line-height: 1.5;
        }
        
        .user-message {
            background-color: #dcf8c6;
            align-self: flex-end;
            border-bottom-right-radius: 0.2rem;
        }
        
        .bot-message {
            background-color: #f0f0f0;
            align-self: flex-start;
            border-bottom-left-radius: 0.2rem;
        }
        
        .chat-input-container {
            display: flex;
            padding: 1rem;
            background-color: #f8f9fa;
            border-top: 1px solid #dee2e6;
        }
        
        .chat-input {
            flex: 1;
            padding: 0.75rem;
            border: 1px solid #ced4da;
            border-radius: 0.25rem;
            font-size: 1rem;
            outline: none;
        }
        
        .chat-input:focus {
            border-color: #80bdff;
            box-shadow: 0 0 0 0.2rem rgba(0,123,255,.25);
        }
        
        .send-button {
            margin-left: 0.5rem;
            padding: 0.75rem 1.5rem;
            background-color: #007bff;
            color: white;
            border: none;
            border-radius: 0.25rem;
            cursor: pointer;
            font-weight: bold;
        }
        
        .send-button:hover {
            background-color: #0069d9;
        }
        
        #execution-graph {
            width: 100%;
            height: 100%;
        }

        .admin-link {
            background-color: #e74c3c;
            color: white;
            padding: 8px 16px;
            text-decoration: none;
            border-radius: 5px;
            font-weight: bold;
            transition: background-color 0.3s;
        }
        
        .admin-link:hover {
            background-color: #c0392b;
            text-decoration: none;
        }
    </style>
</head>
<body>
    <div class="navbar">
        <h1>PlannerV2 Chatbot</h1>
        <a href="/admin" class="admin-link">Admin Panel</a>
    </div>
    
    <div class="container">
        <!-- Knowledge Panel -->
        <div class="panel knowledge-panel">
            <div class="panel-header">Knowledge Processing</div>
            <div id="knowledge-content" class="panel-content knowledge-content"></div>
        </div>
        
        <!-- Chat Panel -->
        <div class="panel chat-panel">
            <div class="panel-header">Chat</div>
            <div id="chat-content" class="panel-content chat-content"></div>
            <div class="chat-input-container">
                <input id="chat-input" class="chat-input" type="text" placeholder="Type your message here..." autofocus>
                <button id="send-button" class="send-button">Send</button>
            </div>
        </div>
        
        <!-- Execution Plan Panel -->
        <div class="panel execution-panel">
            <div class="panel-header">Execution Plan</div>
            <div id="execution-content" class="panel-content">
                <svg id="execution-graph"></svg>
            </div>
        </div>
    </div>
    
    <script>
        const chatContent = document.getElementById('chat-content');
        const knowledgeContent = document.getElementById('knowledge-content');
        const executionContent = document.getElementById('execution-content');
        const chatInput = document.getElementById('chat-input');
        const sendButton = document.getElementById('send-button');
        
        // WebSocket connection
        const socket = new WebSocket(`ws://${window.location.host}/chat/ws`);
        
        socket.onopen = function(e) {
            console.log('WebSocket connection established');
            addKnowledgeUpdate('Connected to chat server. Ready to assist you!');
        };
        
        socket.onmessage = function(event) {
            const data = JSON.parse(event.data);
            
            if (data.type === 'user_message') {
                addMessage(data.message, 'user');
            } else if (data.type === 'bot_message') {
                addMessage(data.message, 'bot');
            } else if (data.type === 'knowledge_update') {
                addKnowledgeUpdate(data.message);
            } else if (data.type === 'execution_plan') {
                renderExecutionPlan(data.data);
            }
        };
        
        socket.onclose = function(event) {
            console.log('WebSocket connection closed');
            addKnowledgeUpdate('Disconnected from chat server. Please refresh the page to reconnect.');
        };
        
        socket.onerror = function(error) {
            console.error('WebSocket error:', error);
            addKnowledgeUpdate('Error connecting to chat server. Please refresh the page to try again.');
        };
        
        // Send message when button is clicked or Enter is pressed
        sendButton.addEventListener('click', sendMessage);
        chatInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                sendMessage();
            }
        });
        
        function sendMessage() {
            const message = chatInput.value.trim();
            if (message) {
                socket.send(JSON.stringify({ message }));
                chatInput.value = '';
                
                // Clear knowledge and execution panels for new question
                knowledgeContent.innerHTML = '';
                d3.select('#execution-graph').html('');
            }
        }
        
        function addMessage(message, sender) {
            const messageDiv = document.createElement('div');
            messageDiv.classList.add('message', `${sender}-message`);
            messageDiv.textContent = message;
            
            chatContent.appendChild(messageDiv);
            messageDiv.scrollIntoView({ behavior: 'smooth' });
        }
        
        function addKnowledgeUpdate(html) {
            const div = document.createElement('div');
            div.classList.add('processing-step');
            div.innerHTML = html;
            
            knowledgeContent.appendChild(div);
            div.scrollIntoView({ behavior: 'smooth' });
        }
        
        function renderExecutionPlan(data) {
            // Clear the existing graph
            d3.select('#execution-graph').html('');
            
            const svg = d3.select('#execution-graph');
            const width = executionContent.offsetWidth;
            const height = executionContent.offsetHeight;
            
            svg.attr('width', width)
               .attr('height', height);
            
            // Create force simulation
            const simulation = d3.forceSimulation(data.nodes)
                .force('link', d3.forceLink(data.links).id(d => d.id).distance(100))
                .force('charge', d3.forceManyBody().strength(-300))
                .force('center', d3.forceCenter(width / 2, height / 2))
                .force('collision', d3.forceCollide().radius(50));
                
            // Add links
            const link = svg.append('g')
                .selectAll('line')
                .data(data.links)
                .enter().append('line')
                .attr('stroke', '#999')
                .attr('stroke-opacity', 0.6)
                .attr('stroke-width', d => d.value ? d.value : 1);
                
            // Add nodes
            const node = svg.append('g')
                .selectAll('g')
                .data(data.nodes)
                .enter().append('g')
                .call(d3.drag()
                    .on('start', dragstarted)
                    .on('drag', dragged)
                    .on('end', dragended));
                
            // Node circles
            node.append('circle')
                .attr('r', 25)
                .attr('fill', d => {
                    switch(d.type) {
                        case 'input': return '#4CAF50';
                        case 'process': return '#2196F3';
                        case 'tool': return d.selected ? '#FF9800' : '#9E9E9E';
                        case 'output': return '#F44336';
                        default: return '#9C27B0';
                    }
                })
                .attr('stroke', '#fff')
                .attr('stroke-width', 2);
                
            // Node labels
            node.append('text')
                .text(d => d.name)
                .attr('text-anchor', 'middle')
                .attr('dy', 40)
                .attr('font-size', '10px')
                .attr('fill', '#333');
                
            // Update positions during simulation
            simulation.on('tick', () => {
                link
                    .attr('x1', d => d.source.x)
                    .attr('y1', d => d.source.y)
                    .attr('x2', d => d.target.x)
                    .attr('y2', d => d.target.y);
                    
                node
                    .attr('transform', d => `translate(${d.x},${d.y})`);
            });
            
            // Drag functions
            function dragstarted(event, d) {
                if (!event.active) simulation.alphaTarget(0.3).restart();
                d.fx = d.x;
                d.fy = d.y;
            }
            
            function dragged(event, d) {
                d.fx = event.x;
                d.fy = event.y;
            }
            
            function dragended(event, d) {
                if (!event.active) simulation.alphaTarget(0);
                d.fx = null;
                d.fy = null;
            }
        }
    </script>
</body>
</html>
"""