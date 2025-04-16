from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field
from typing import List
import json

app = FastAPI()

# -------------------------
#  Data Models
# -------------------------

class PlannerData(BaseModel):
    # Stores the entire planner schema as a JSON string
    schema_json: str = "{}"

class ToolData(BaseModel):
    name: str = "Untitled Tool"
    description: str = "No description"
    priority: int = 100
    display_mode: str = "as-is"  # or "summarizable"
    index_name: str = ""         # blank if no index is used
    top_k: int = 1               # how many items to retrieve
    reranker: str = "none"       # e.g., "none" or "simple"
    parameters_json: str = "[]"  # JSON array describing tool parameters
    planner_fields_mapping: str = "{}"  # JSON dict for each planner field -> ignore/pass/filter

class ContentData(BaseModel):
    title: str = "Untitled Content"
    body: str = ""
    index_name: str = ""
    tagging_json: str = "{}"  # extra tags or fields relevant to tools/planner

class UserData(BaseModel):
    # Now storing user data as a JSON string, minimal validation
    user_json: str = "{}"

class GlobalConfig(BaseModel):
    planner: PlannerData = PlannerData()
    tools: List[ToolData] = Field(default_factory=list)
    content: List[ContentData] = Field(default_factory=list)
    user: UserData = UserData()

global_config = GlobalConfig()

# -------------------------
#  Helper Functions
# -------------------------

def validate_json_or_keep_old(new_value: str, old_value: str) -> str:
    """
    Tries to parse new_value as JSON. If invalid, returns old_value.
    If valid, returns new_value.
    """
    try:
        json.loads(new_value)
        return new_value
    except json.JSONDecodeError:
        return old_value

# -------------------------
#  Admin Page (Tabs)
# -------------------------

@app.get("/admin", response_class=HTMLResponse)
async def admin_page():
    """
    Returns a single HTML page with four tabs:
    - Planner
    - Tools
    - Content
    - User
    """
    html_content = f"""
    <html>
    <head>
        <title>Admin Configuration</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                margin: 20px;
                background: #f4f4f4;
            }}
            .tab-buttons {{
                margin-bottom: 20px;
            }}
            .tab-buttons button {{
                margin-right: 10px;
                padding: 10px 16px;
                cursor: pointer;
                background: #337ab7;
                color: #fff;
                border: none;
                border-radius: 4px;
                font-size: 14px;
            }}
            .tab-buttons button:hover {{
                background: #286090;
            }}
            .tab {{
                display: none;
                background: #fff;
                padding: 20px;
                border-radius: 6px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.2);
                margin-bottom: 30px;
            }}
            .tab h2 {{
                margin-top: 0;
            }}
            .active-tab {{
                display: block;
            }}
            .config-section {{
                margin-top: 20px;
                border: 1px solid #ccc;
                padding: 15px;
                border-radius: 8px;
                background: #fafafa;
            }}
            label {{
                display: inline-block;
                width: 160px;
                margin-right: 10px;
                font-weight: bold;
                vertical-align: top;
            }}
            input[type='text'], textarea, select {{
                width: 300px;
                margin-bottom: 10px;
                border: 1px solid #ccc;
                border-radius: 4px;
                padding: 6px;
                font-size: 14px;
            }}
            .save-button {{
                margin-top: 10px;
                background: #5cb85c;
                color: #fff;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                cursor: pointer;
            }}
            .save-button:hover {{
                background: #4cae4c;
            }}
            .instructions {{
                background: #e9f5f8;
                border: 1px solid #bce0ea;
                padding: 10px;
                margin-bottom: 20px;
                border-radius: 6px;
            }}
            pre {{
                background: #eee;
                padding: 8px;
                border-radius: 4px;
            }}
            .delete-button {{
                background: #d9534f;
                color: #fff;
                border: none;
                border-radius: 4px;
                padding: 6px 12px;
                cursor: pointer;
            }}
            .delete-button:hover {{
                background: #c9302c;
            }}
        </style>
        <script>
        function showTab(tabId) {{
            // Hide all tabs
            const tabs = document.querySelectorAll('.tab');
            tabs.forEach(tab => tab.style.display = 'none');

            // Show the selected tab
            document.getElementById(tabId).style.display = 'block';
        }}
        </script>
    </head>
    <body>
        <h1>Admin Configuration</h1>
        <div class="tab-buttons">
            <button onclick="showTab('planner-tab')">Planner</button>
            <button onclick="showTab('tools-tab')">Tools</button>
            <button onclick="showTab('content-tab')">Content</button>
            <button onclick="showTab('user-tab')">User</button>
        </div>

        <!-- Planner Tab -->
        <div id="planner-tab" class="tab active-tab">
            <h2>Planner Configuration</h2>
            <div class="instructions">
                <p><strong>Instructions:</strong> Provide a JSON object describing the planner's schema. 
                   Each key is a planner field, and its value can be an object with 
                   <code>type</code>, <code>required</code>, and <code>description</code>. No nested objects needed.</p>
                <p>Example:</p>
                <pre>
{{
  "customerType": {{
    "type": "string",
    "required": false,
    "description": "Subscription tier of the customer"
  }},
  "region": {{
    "type": "string",
    "required": true,
    "description": "Geographical region"
  }}
}}
                </pre>
            </div>
            <form action="/update_planner" method="post" class="config-section">
                <textarea name="schema_json" rows="12">{global_config.planner.schema_json}</textarea><br/>
                <button type="submit" class="save-button">Save Planner Config</button>
            </form>
        </div>

        <!-- Tools Tab -->
        <div id="tools-tab" class="tab">
            <h2>Tools Configuration</h2>
            <div class="instructions">
                <p><strong>Instructions:</strong> Each tool can optionally use a retrieval <em>index</em>, specify <em>top_k</em> results, 
                   and define how it uses each planner field (ignore/pass/filter).</p>
                <p>For <code>parameters_json</code>, provide an array of objects, each with 
                   <code>name</code>, <code>type</code>, <code>required</code>, and <code>description</code>. 
                   For example:</p>
                <pre>
[
  {{
    "name": "userId",
    "type": "string",
    "required": true,
    "description": "ID of the user"
  }},
  {{
    "name": "region",
    "type": "string",
    "required": false,
    "description": "User's region"
  }}
]
                </pre>
                <p>For <code>planner_fields_mapping</code>, use an object mapping each planner field 
                   to one of "ignore", "pass", or "filter". For example:</p>
                <pre>
{{
  "customerType": "pass",
  "region": "filter"
}}
                </pre>
            </div>
            {generate_tools_html(global_config.tools)}
        </div>

        <!-- Content Tab -->
        <div id="content-tab" class="tab">
            <h2>Content Configuration</h2>
            <div class="instructions">
                <p><strong>Instructions:</strong> Each piece of content can be assigned to an <code>index_name</code>. 
                   Tools referencing that index can retrieve it. The <code>tagging_json</code> can include extra tags 
                   or metadata relevant to the planner or tools.</p>
                <p>Example <code>tagging_json</code>:</p>
                <pre>
{{
  "topic": "payroll",
  "difficulty": "basic"
}}
                </pre>
            </div>
            {generate_content_html(global_config.content)}
        </div>

        <!-- User Tab -->
        <div id="user-tab" class="tab">
            <h2>User Configuration</h2>
            <div class="instructions">
                <p><strong>Instructions:</strong> Provide a JSON object representing the user data. 
                   Ideally, it aligns with the <strong>planner fields</strong> (e.g., <code>customerType</code>, <code>region</code>), 
                   plus an <code>other_context</code> field for anything else. Example:</p>
                <pre>
{{
  "customerType": "premium",
  "region": "US",
  "other_context": "some free text"
}}
                </pre>
            </div>
            <form action="/update_user" method="post" class="config-section">
                <label>User Data (JSON):</label><br/>
                <textarea name="user_json" rows="10">{global_config.user.user_json}</textarea><br/>
                <button type="submit" class="save-button">Save User Config</button>
            </form>
        </div>
    </body>
    </html>
    """
    return html_content

# -------------------------
#  Generate Tools HTML
# -------------------------

def generate_tools_html(tools: List[ToolData]) -> str:
    html = []
    # Existing tools
    for i, tool in enumerate(tools):
        tool_form = f"""
        <form action="/update_tool" method="post" class="config-section">
            <input type="hidden" name="tool_index" value="{i}" />
            <h3>Tool #{i+1}</h3>
            <label>Name:</label>
            <input type="text" name="name" value="{tool.name}" /><br/>
            
            <label>Description:</label>
            <textarea name="description" rows="2">{tool.description}</textarea><br/>
            
            <label>Priority:</label>
            <input type="text" name="priority" value="{tool.priority}" /><br/>
            
            <label>Display Mode:</label>
            <select name="display_mode">
              <option value="as-is" {"selected" if tool.display_mode == "as-is" else ""}>as-is</option>
              <option value="summarizable" {"selected" if tool.display_mode == "summarizable" else ""}>summarizable</option>
            </select><br/>
            
            <label>Index Name:</label>
            <input type="text" name="index_name" value="{tool.index_name}" /><br/>
            
            <label>Top K:</label>
            <input type="text" name="top_k" value="{tool.top_k}" /><br/>
            
            <label>Reranker:</label>
            <select name="reranker">
              <option value="none" {"selected" if tool.reranker == "none" else ""}>none</option>
              <option value="simple" {"selected" if tool.reranker == "simple" else ""}>simple</option>
            </select><br/>
            
            <label>Parameters JSON:</label><br/>
            <textarea name="parameters_json" rows="4">{tool.parameters_json}</textarea><br/>
            
            <label>Planner Fields Mapping:</label><br/>
            <textarea name="planner_fields_mapping" rows="4">{tool.planner_fields_mapping}</textarea><br/>
            
            <button type="submit" class="save-button">Save Tool</button>
        </form>
        <form action="/delete_tool" method="post" style="margin-top:-20px;">
            <input type="hidden" name="tool_index" value="{i}" />
            <button type="submit" class="delete-button">Delete Tool</button>
        </form>
        """
        html.append(tool_form)

    # New tool form
    new_tool_form = f"""
    <form action="/add_tool" method="post" class="config-section">
        <h3>Add New Tool</h3>
        <label>Name:</label>
        <input type="text" name="name" value="New Tool" /><br/>
        
        <label>Description:</label>
        <textarea name="description" rows="2">No description</textarea><br/>
        
        <label>Priority:</label>
        <input type="text" name="priority" value="100" /><br/>
        
        <label>Display Mode:</label>
        <select name="display_mode">
          <option value="as-is">as-is</option>
          <option value="summarizable">summarizable</option>
        </select><br/>
        
        <label>Index Name:</label>
        <input type="text" name="index_name" value="" /><br/>
        
        <label>Top K:</label>
        <input type="text" name="top_k" value="1" /><br/>
        
        <label>Reranker:</label>
        <select name="reranker">
          <option value="none">none</option>
          <option value="simple">simple</option>
        </select><br/>
        
        <label>Parameters JSON:</label><br/>
        <textarea name="parameters_json" rows="4">[]</textarea><br/>
        
        <label>Planner Fields Mapping:</label><br/>
        <textarea name="planner_fields_mapping" rows="4">{{}}</textarea><br/>
        
        <button type="submit" class="save-button">Add Tool</button>
    </form>
    """
    html.append(new_tool_form)

    return "".join(html)

# -------------------------
#  Generate Content HTML
# -------------------------

def generate_content_html(content_items: List[ContentData]) -> str:
    html = []
    for i, item in enumerate(content_items):
        content_form = f"""
        <form action="/update_content_item" method="post" class="config-section">
            <input type="hidden" name="content_index" value="{i}" />
            <h3>Content #{i+1}</h3>
            <label>Title:</label>
            <input type="text" name="title" value="{item.title}" /><br/>
            
            <label>Body:</label><br/>
            <textarea name="body" rows="4">{item.body}</textarea><br/>
            
            <label>Index Name:</label>
            <input type="text" name="index_name" value="{item.index_name}" /><br/>
            
            <label>Tagging JSON:</label><br/>
            <textarea name="tagging_json" rows="4">{item.tagging_json}</textarea><br/>
            
            <button type="submit" class="save-button">Save Content</button>
        </form>
        <form action="/delete_content_item" method="post" style="margin-top:-20px;">
            <input type="hidden" name="content_index" value="{i}" />
            <button type="submit" class="delete-button">Delete Content</button>
        </form>
        """
        html.append(content_form)

    # New content form
    new_content_form = f"""
    <form action="/add_content_item" method="post" class="config-section">
        <h3>Add New Content Item</h3>
        <label>Title:</label>
        <input type="text" name="title" value="Untitled Content" /><br/>
        
        <label>Body:</label><br/>
        <textarea name="body" rows="4"></textarea><br/>
        
        <label>Index Name:</label>
        <input type="text" name="index_name" value="" /><br/>
        
        <label>Tagging JSON:</label><br/>
        <textarea name="tagging_json" rows="4">{{}}</textarea><br/>
        
        <button type="submit" class="save-button">Add Content</button>
    </form>
    """
    html.append(new_content_form)
    return "".join(html)

# -------------------------
#  Update Endpoints
# -------------------------

@app.post("/update_planner")
async def update_planner(schema_json: str = Form(...)):
    global global_config
    old_value = global_config.planner.schema_json
    global_config.planner.schema_json = validate_json_or_keep_old(schema_json, old_value)
    return {"status": "success", "message": "Planner config updated."}

# Tools
@app.post("/add_tool")
async def add_tool(
    name: str = Form(...),
    description: str = Form(...),
    priority: str = Form(...),
    display_mode: str = Form(...),
    index_name: str = Form(...),
    top_k: str = Form(...),
    reranker: str = Form(...),
    parameters_json: str = Form(...),
    planner_fields_mapping: str = Form(...)
):
    global global_config
    new_tool = ToolData()
    new_tool.name = name.strip()
    new_tool.description = description.strip()
    # parse int priority
    try:
        new_tool.priority = int(priority)
    except ValueError:
        new_tool.priority = 100
    new_tool.display_mode = display_mode
    new_tool.index_name = index_name.strip()
    # parse int top_k
    try:
        new_tool.top_k = int(top_k)
    except ValueError:
        new_tool.top_k = 1
    new_tool.reranker = reranker

    # validate JSON fields
    new_tool.parameters_json = validate_json_or_keep_old(parameters_json, "[]")
    new_tool.planner_fields_mapping = validate_json_or_keep_old(planner_fields_mapping, "{}")

    global_config.tools.append(new_tool)
    return {"status": "success", "message": "New tool added."}

@app.post("/update_tool")
async def update_tool(request: Request):
    global global_config
    form_data = await request.form()
    tool_index = int(form_data["tool_index"])
    if 0 <= tool_index < len(global_config.tools):
        tool = global_config.tools[tool_index]
        tool.name = form_data["name"].strip()
        tool.description = form_data["description"].strip()

        try:
            tool.priority = int(form_data["priority"])
        except ValueError:
            pass

        tool.display_mode = form_data["display_mode"]
        tool.index_name = form_data["index_name"].strip()

        try:
            tool.top_k = int(form_data["top_k"])
        except ValueError:
            pass

        tool.reranker = form_data["reranker"]

        # Validate JSON
        old_params = tool.parameters_json
        old_mapping = tool.planner_fields_mapping
        tool.parameters_json = validate_json_or_keep_old(form_data["parameters_json"], old_params)
        tool.planner_fields_mapping = validate_json_or_keep_old(form_data["planner_fields_mapping"], old_mapping)

    return {"status": "success", "message": "Tool updated."}

@app.post("/delete_tool")
async def delete_tool(tool_index: int = Form(...)):
    global global_config
    if 0 <= tool_index < len(global_config.tools):
        global_config.tools.pop(tool_index)
    return {"status": "success", "message": "Tool deleted."}

# Content
@app.post("/add_content_item")
async def add_content_item(
    title: str = Form(...),
    body: str = Form(...),
    index_name: str = Form(...),
    tagging_json: str = Form(...)
):
    global global_config
    new_content = ContentData()
    new_content.title = title.strip()
    new_content.body = body.strip()
    new_content.index_name = index_name.strip()
    new_content.tagging_json = validate_json_or_keep_old(tagging_json, "{}")
    global_config.content.append(new_content)
    return {"status": "success", "message": "New content item added."}

@app.post("/update_content_item")
async def update_content_item(request: Request):
    global global_config
    form_data = await request.form()
    c_index = int(form_data["content_index"])
    if 0 <= c_index < len(global_config.content):
        item = global_config.content[c_index]
        item.title = form_data["title"].strip()
        item.body = form_data["body"].strip()
        item.index_name = form_data["index_name"].strip()

        old_tagging = item.tagging_json
        item.tagging_json = validate_json_or_keep_old(form_data["tagging_json"], old_tagging)

    return {"status": "success", "message": "Content item updated."}

@app.post("/delete_content_item")
async def delete_content_item(content_index: int = Form(...)):
    global global_config
    if 0 <= content_index < len(global_config.content):
        global_config.content.pop(content_index)
    return {"status": "success", "message": "Content item deleted."}

# User
@app.post("/update_user")
async def update_user(user_json: str = Form(...)):
    global global_config
    old_value = global_config.user.user_json
    global_config.user.user_json = validate_json_or_keep_old(user_json, old_value)
    return {"status": "success", "message": "User config updated."}

# -------------------------
#  Optional Health Check
# -------------------------
@app.get("/health")
def health_check():
    return {"status": "ok"}

# -------------------------
#  Main
# -------------------------
if __name__ == "__main__":
    import uvicorn
    # Access at http://127.0.0.1:8000/admin
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
