# plannerv2/routers/admin_main.py

from fastapi import APIRouter, Form, Query
from fastapi.responses import HTMLResponse
from starlette.responses import RedirectResponse
from typing import List, Optional
import json

from plannerv2.core.config_manager import load_json_config, save_json_config
from plannerv2.models.planner import PlannerConfig
from plannerv2.models.user import UserConfig

# Import the separate router modules for Tools/Content
# (They have their own endpoints for add/update/delete)
from plannerv2.routers.admin_tools import router_tools, render_tools_tab
from plannerv2.routers.admin_content import router_content, render_content_tab

# Import the small tab functions for Planner & User
from plannerv2.routers.admin_planner import render_planner_tab
from plannerv2.routers.admin_user import render_user_tab, clean_outdated_filters

router = APIRouter()
router.include_router(router_tools)   # merges /admin/tools/add, etc.
router.include_router(router_content) # merges /admin/content/add, etc.

PLANNER_FILE = "planner.json"
USER_FILE = "user.json"

@router.get("/admin", response_class=HTMLResponse)
async def admin_dashboard(tab: Optional[str] = Query("planner")):
    # Set default tab to planner unless specified
    active_tab = tab if tab in ["planner", "user", "tools", "content"] else "planner"
    
    # 1. Load Planner
    planner_data = load_json_config(PLANNER_FILE)
    planner_model = PlannerConfig(**planner_data) if planner_data else PlannerConfig()

    # 2. Load User
    user_data = load_json_config(USER_FILE)
    user_model = UserConfig(**user_data) if user_data else UserConfig()

    # 3. Load Tools (for the Tools tab)
    from plannerv2.routers.admin_tools import TOOLS_FILE
    from plannerv2.models.tool import ToolData
    tools_data = load_json_config(TOOLS_FILE)
    tools_list: List[ToolData] = []
    if isinstance(tools_data, list):
        for t in tools_data:
            tools_list.append(ToolData(**t))

    # 4. Load Content (for the Content tab)
    from plannerv2.routers.admin_content import CONTENT_FILE
    from plannerv2.models.content import ContentConfig
    content_data = load_json_config(CONTENT_FILE)
    if content_data and "items" in content_data:
        content_model = ContentConfig(**content_data)
    else:
        content_model = ContentConfig()

    # Compose each tab's HTML
    planner_html = f"""
    <form action="/admin/planner/update" method="post" class="config-section" id="planner">
        {render_planner_tab(planner_model)}
        <input type="hidden" name="return_tab" value="planner">
    </form>
    """

    user_html = f"""
    <form action="/admin/user/update" method="post" class="config-section" id="user">
        {render_user_tab(user_model)}
        <input type="hidden" name="return_tab" value="user">
    </form>
    """

    tools_html = f"""
    <div class="config-section" id="tools">
        {render_tools_tab(tools_list)}
    </div>
    """

    content_html = f"""
    <div class="config-section" id="content">
        {render_content_tab(content_model.items)}
    </div>
    """

    page = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Admin Panel</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                margin: 20px;
                background-color: #f4f4f4;
                padding: 20px;
            }}
            .top-nav {{
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 20px;
                padding-bottom: 10px;
                border-bottom: 1px solid #ddd;
            }}
            .chat-link {{
                background-color: #28a745;
                color: white;
                padding: 8px 16px;
                text-decoration: none;
                border-radius: 5px;
                font-weight: bold;
                transition: background-color 0.3s;
            }}
            .chat-link:hover {{
                background-color: #218838;
                text-decoration: none;
            }}
            .tab-buttons {{
                display: flex;
                margin-bottom: 20px;
            }}
            .tab-btn {{
                padding: 10px 16px;
                cursor: pointer;
                background-color: #007bff;
                color: #fff;
                border-radius: 5px;
                margin-right: 10px;
                font-weight: bold;
                transition: background 0.3s;
            }}
            .tab-btn:hover {{
                background-color: #0056b3;
            }}
            .tab-btn.active {{
                background-color: #0056b3;
            }}
            .config-section {{
                display: none;
                background: white;
                padding: 20px;
                border-radius: 10px;
                box-shadow: 0px 0px 10px rgba(0,0,0,0.1);
                margin-top: 10px;
            }}
            .config-section.active {{
                display: block;
            }}
            .guide-panel {{
                background-color: #f8f9fa;
                border-left: 4px solid #17a2b8;
                padding: 15px;
                margin-bottom: 20px;
                border-radius: 5px;
            }}
            .guide-panel h3 {{
                margin-top: 0;
                color: #17a2b8;
            }}
            .guide-panel ul, .guide-panel ol {{
                padding-left: 20px;
            }}
            .guide-panel li {{
                margin-bottom: 5px;
            }}
            .help-text {{
                margin-top: 5px;
                font-size: 12px;
                color: #6c757d;
                font-style: italic;
            }}
            label {{
                font-weight: bold;
                display: block;
                margin-top: 10px;
            }}
            input, select, textarea {{
                width: 100%;
                padding: 8px;
                margin-top: 5px;
                border-radius: 5px;
                border: 1px solid #ccc;
                font-size: 14px;
            }}
            textarea {{
                min-height: 80px;
            }}
            .save-button {{
                margin-top: 20px;
                padding: 10px;
                background: #28a745;
                color: white;
                border: none;
                border-radius: 5px;
                cursor: pointer;
                font-size: 16px;
            }}
            .save-button:hover {{
                background: #218838;
            }}
            h2 {{
                color: #343a40;
                margin-bottom: 20px;
                border-bottom: 1px solid #dee2e6;
                padding-bottom: 10px;
            }}
            pre {{
                background-color: #f8f9fa;
                padding: 10px;
                border-radius: 5px;
                overflow-x: auto;
                font-size: 12px;
            }}
            .tool-entry, .content-entry {{
                transition: all 0.2s;
            }}
            .tool-entry:hover, .content-entry:hover {{
                background-color: #f0f7ff;
                transform: translateY(-2px);
                box-shadow: 0 4px 8px rgba(0,0,0,0.1);
            }}
            .field-filters {{
                background-color: #e9f7ef;
                padding: 10px;
                border-radius: 5px;
                margin: 10px 0;
            }}
            .field-filters h4 {{
                margin-top: 0;
                color: #28a745;
            }}
            .filter-row {{
                display: flex;
                align-items: center;
                margin-bottom: 5px;
            }}
            .filter-row label {{
                margin-top: 0;
                flex: 1;
                font-weight: normal;
            }}
            .filter-row input {{
                width: 60%;
            }}
        </style>
        <script>
        function showTab(tabName) {{
            document.querySelectorAll('.config-section').forEach(sec => sec.classList.remove('active'));
            document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
            document.getElementById(tabName).classList.add('active');
            document.querySelector(`[data-tab="${{tabName}}"]`).classList.add('active');
            
            // Update URL to reflect current tab
            history.replaceState(null, null, `/admin?tab=${{tabName}}`);
            
            // If switching to tools or content tab, refresh the user field filters
            if (tabName === 'tools' || tabName === 'content') {{
                refreshDynamicUserFields();
            }}
        }}
        
        // This function will be called when tabs change or when the page loads
        function refreshDynamicUserFields() {{
            if (typeof window.getUserFields === 'function') {{
                const userFields = window.getUserFields();
                
                // Update any field filter containers with the current fields
                document.querySelectorAll('.field-filters-container').forEach(container => {{
                    const targetInput = container.getAttribute('data-target');
                    const currentMapping = getFieldMappingFromInput(targetInput);
                    
                    // Clear existing fields
                    container.innerHTML = '';
                    
                    if (userFields.length > 0) {{
                        const filtersDiv = document.createElement('div');
                        filtersDiv.className = 'field-filters';
                        filtersDiv.innerHTML = '<h4>Filter Values</h4><p class="help-text">Enter values to require for each field. Empty values mean no filtering.</p>';
                        
                        userFields.forEach(field => {{
                            const filterValue = currentMapping[field] || '';
                            
                            const row = document.createElement('div');
                            row.className = 'filter-row';
                            
                            row.innerHTML = `
                                <label>${{field}}:</label>
                                <input type="text" class="filter-value" data-field="${{field}}" value="${{filterValue}}" placeholder="No filter">
                            `;
                            
                            // Add listener to update the hidden field
                            row.querySelector('input').addEventListener('input', e => {{
                                updateFieldMappingInput(targetInput);
                            }});
                            
                            filtersDiv.appendChild(row);
                        }});
                        
                        container.appendChild(filtersDiv);
                    }}
                }});
            }}
        }}
        
        // Helper to parse the current mapping JSON from an input
        function getFieldMappingFromInput(inputId) {{
            const input = document.getElementById(inputId);
            if (!input) return {{}};
            
            try {{
                return JSON.parse(input.value || '{{}}');
            }} catch (e) {{
                return {{}};
            }}
        }}
        
        // Update hidden JSON input with values from filters
        function updateFieldMappingInput(inputId) {{
            const jsonInput = document.getElementById(inputId);
            if (!jsonInput) return;
            
            // Get the container for this input
            const container = document.querySelector(`[data-target="${{inputId}}"]`);
            if (!container) return;
            
            // Create a new mapping based on current filter values
            const newMapping = {{}};
            container.querySelectorAll('.filter-value').forEach(input => {{
                const field = input.getAttribute('data-field');
                const value = input.value.trim();
                
                // Only add non-empty values
                if (value) {{
                    newMapping[field] = value;
                }}
            }});
            
            // Update the hidden input
            jsonInput.value = JSON.stringify(newMapping);
        }}
        
        window.onload = () => {{
            showTab('{active_tab}');
        }};
        </script>
    </head>
    <body>
        <div class="top-nav">
            <h1>Admin Panel</h1>
            <a href="/chat" class="chat-link">Go to Chat Interface</a>
        </div>
        <div class="tab-buttons">
            <div class="tab-btn" data-tab="planner" onclick="showTab('planner')">Planner</div>
            <div class="tab-btn" data-tab="user" onclick="showTab('user')">User</div>
            <div class="tab-btn" data-tab="tools" onclick="showTab('tools')">Tools</div>
            <div class="tab-btn" data-tab="content" onclick="showTab('content')">Content</div>
        </div>

        {planner_html}
        {user_html}
        {tools_html}
        {content_html}
    </body>
    </html>
    """
    return HTMLResponse(page)


@router.post("/admin/planner/update")
async def update_planner(
    mode: str = Form(...), 
    relevance_threshold: int = Form(50), 
    return_tab: str = Form("planner")
):
    existing_data = load_json_config(PLANNER_FILE)
    from plannerv2.models.planner import PlannerConfig
    if existing_data:
        planner_model = PlannerConfig(**existing_data)
    else:
        planner_model = PlannerConfig()

    planner_model.mode = mode.strip()
    planner_model.relevance_threshold = relevance_threshold
    save_json_config(PLANNER_FILE, planner_model.dict())
    return RedirectResponse(url=f"/admin?tab={return_tab}", status_code=302)


@router.post("/admin/user/update")
async def update_user(user_json: str = Form(...), return_tab: str = Form("user")):
    existing_data = load_json_config(USER_FILE)
    from plannerv2.models.user import UserConfig
    if existing_data:
        user_model = UserConfig(**existing_data)
    else:
        user_model = UserConfig()

    # Update the user config
    user_model.user_json = user_json.strip()
    save_json_config(USER_FILE, user_model.dict())
    
    # Clean up outdated filter fields
    clean_outdated_filters(user_json.strip())
    
    return RedirectResponse(url=f"/admin?tab={return_tab}", status_code=302)