# PlannerV2 - Modular Chatbot Administration System

PlannerV2 is a modular administration system for managing chatbot configurations. It provides a web-based interface for configuring and controlling various aspects of a chatbot, including the planner mode, user attributes, tools, and content items. The system makes it easy to define which tools should be used for different types of user queries and allows for content filtering based on user attributes.

## Features

- **Modular Design**: Each component is self-contained and independent.
- **Real-time Configuration**: Make changes to your chatbot's behavior without restarting the system.
- **User-Aware Filtering**: Personalize content and tool selection based on user attributes.
- **Dynamic User Interface**: Administrative forms adapt based on user fields.
- **Integrated Chat Interface**: Test your configurations directly through the included chat UI.

## Project Structure

```
plannerv2/
├── main.py                    # Application entry point
├── core/
│   ├── __init__.py
│   └── config_manager.py      # JSON configuration file handling
├── models/
│   ├── __init__.py
│   ├── planner.py             # PlannerConfig model
│   ├── user.py                # UserConfig model
│   ├── tool.py                # ToolData model
│   └── content.py             # ContentConfig and ContentItem models
├── routers/
│   ├── __init__.py
│   ├── admin_main.py          # Main admin dashboard
│   ├── admin_planner.py       # Planner configuration UI
│   ├── admin_user.py          # User configuration UI
│   ├── admin_tools.py         # Tools configuration UI
│   ├── admin_content.py       # Content configuration UI
│   └── chatbot.py             # Chat interface and logic
└── config/                    # Storage for JSON configuration files
    ├── planner.json           # Planner configuration
    ├── user.json              # User attributes
    ├── tools.json             # Tool definitions
    └── content.json           # Content items
```

## File Descriptions

### Core Files

- **main.py**: The entry point for the application that sets up FastAPI and includes the various routers.
- **config_manager.py**: Provides functions for loading and saving JSON configuration files.

### Models

- **planner.py**: Defines the `PlannerConfig` model which controls the chatbot's decision-making approach.
- **user.py**: Defines the `UserConfig` model for storing user attributes that affect content and tool selection.
- **tool.py**: Defines the `ToolData` model for specialized functions the chatbot can invoke.
- **content.py**: Defines the `ContentConfig` and `ContentItem` models for knowledge base content.

### Routers

- **admin_main.py**: The main admin dashboard that combines all configuration tabs.
- **admin_planner.py**: UI and endpoints for planner configuration.
- **admin_user.py**: UI and endpoints for user attributes configuration.
- **admin_tools.py**: UI and endpoints for managing tools.
- **admin_content.py**: UI and endpoints for managing knowledge base content.
- **chatbot.py**: The chat interface and processing logic.

## Configuration Components

### 1. Planner Configuration

The planner controls how the chatbot decides which tools to use for each user query.

Options:
- **fast**: Prioritizes speed, choosing tools quickly.
- **fast_listen_override**: Like fast, but can switch tools mid-conversation.
- **smart**: More thorough analysis of queries, potentially slower but more accurate.

### 2. User Configuration

Defines attributes about the user that can affect which content is shown and which tools are used.

Example user configuration:
```json
{
  "customerType": "premium",
  "region": "US",
  "other_context": "Some extra info"
}
```

### 3. Tools Configuration

Tools are specialized components that the chatbot can use to handle specific types of queries.

Key settings:
- **Name & Description**: Identifies the tool.
- **Priority**: Controls execution order (lower numbers have higher priority).
- **Display Mode**: Whether to show tool output directly or summarize it.
- **Index Name**: For retrieval tools, which content index to search.
- **User Fields Mapping**: Filters that determine when the tool should be used.
- **Disambiguation Level**: Controls how aggressively the tool clarifies ambiguous queries.

### 4. Content Configuration

Content items are knowledge base articles that the chatbot can present to users.

Key components:
- **Title & Body**: The main content.
- **Index Name**: Associates content with specific tools.
- **Query Strings**: Examples of how users might ask for this information.
- **User Fields Mapping**: Filters that control who should see this content.

## Getting Started

1. **Clone the repository**

2. **Install dependencies**
   ```
   pip install fastapi uvicorn pydantic
   ```

3. **Run the application**
   ```
   python -m plannerv2.main
   ```

4. **Access the interfaces**
   - Admin Dashboard: http://127.0.0.1:8000/admin
   - Chat Interface: http://127.0.0.1:8000/chat

## User Workflow

1. **Configure the System**:
   - Set up user attributes in the User tab
   - Define tools in the Tools tab
   - Add knowledge base content in the Content tab
   - Select a planner mode in the Planner tab

2. **Test with the Chat Interface**:
   - Navigate to the chat interface
   - Ask questions to see how the system responds
   - Observe how different tools and content are selected based on your query

3. **Refine Your Configuration**:
   - Return to the admin panel to adjust settings
   - Add or modify user field filters to personalize content
   - Update tool settings for better query handling

## Dynamic User Fields

When you define fields in the User JSON configuration, those fields automatically appear as filter options in the Tools and Content sections. This allows you to create personalized experiences based on user attributes:

1. Add fields to the User JSON (e.g., `{"region": "US", "customerType": "premium"}`)
2. These fields then appear as filter options in Tools and Content
3. Enter specific values to filter when that tool/content should be used
4. Empty filter values mean no filtering on that field

## Notes

- The system automatically cleans up outdated filter fields when user configuration changes.
- All configuration is stored in JSON files in the config directory.
- Changes take effect immediately without restarting the server.