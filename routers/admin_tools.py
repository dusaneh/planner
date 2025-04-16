# plannerv2/routers/admin_tools.py

from fastapi import APIRouter, Request, Form
from starlette.responses import RedirectResponse
from typing import List, Dict, Any, Union
import json

from plannerv2.core.config_manager import load_json_config, save_json_config
from plannerv2.models.tool import ToolData

TOOLS_FILE = "tools.json"
router_tools = APIRouter()

def render_tools_tab(tools_list: List[ToolData]) -> str:
    """
    Returns HTML for the Tools tab, listing existing tools
    plus forms for Add and Update.
    """
    # Guide text at the top of the tab
    intro_guide = """
    <div class="guide-panel">
        <h3>How to Configure Tools</h3>
        <p>Tools are specialized components that the chatbot can use to handle specific types of queries.</p>
        <ol>
            <li><strong>Create tools</strong> for different functions like retrieval, tax help, or payroll assistance.</li>
            <li><strong>Set priorities</strong> to control which tools execute when multiple matches occur.</li>
            <li><strong>Configure user field filters</strong> to personalize responses based on user attributes.</li>
            <li><strong>Choose rerankers</strong> for retrieval tools to improve result quality.</li>
        </ol>
        <p>Click on any existing tool below to edit its configuration.</p>
    </div>
    """
    
    existing_tools_html = ""
    for i, tool in enumerate(tools_list):
        # Convert user_fields_mapping to a JSON string for the data attribute
        user_fields_json = json.dumps(tool.user_fields_mapping)
            
        existing_tools_html += f"""
        <div class="tool-entry" data-tool-index="{i}"
             data-name="{tool.name}"
             data-description="{tool.description}"
             data-priority="{tool.priority}"
             data-display_mode="{tool.display_mode}"
             data-index_name="{tool.index_name}"
             data-top_k="{tool.top_k}"
             data-reranker="{tool.reranker}"
             data-parameters_json="{tool.parameters_json.replace('"','&#34;')}"
             data-user_fields_mapping="{user_fields_json.replace('"','&#34;')}"
             data-disambiguation_level="{tool.disambiguation_level}"
             data-can_be_overridden_when_sticky={"true" if tool.can_be_overridden_when_sticky else "false"}
             style="border:1px solid #ddd; padding:10px; margin-bottom:10px; border-radius:5px; cursor:pointer;">
          <strong>Name:</strong> {tool.name}<br/>
          <strong>Description:</strong> {tool.description}<br/>
          <strong>Priority:</strong> {tool.priority}<br/>
          <strong>Display Mode:</strong> {tool.display_mode}<br/>
          <strong>Index Name:</strong> {tool.index_name}<br/>
          <strong>Top K:</strong> {tool.top_k}<br/>
          <strong>Reranker:</strong> {tool.reranker}<br/>
          <strong>Parameters JSON:</strong> <pre>{tool.parameters_json}</pre>
          <strong>User Fields Mapping:</strong> <pre>{user_fields_json}</pre>
          <strong>Disambiguation Level:</strong> {tool.disambiguation_level}<br/>
          <strong>Can Be Overridden When Sticky?</strong> {tool.can_be_overridden_when_sticky}<br/>

          <!-- Delete button -->
          <form action="/admin/tools/delete" method="post" style="margin-top:10px;">
            <input type="hidden" name="tool_index" value="{i}" />
            <input type="hidden" name="return_tab" value="tools" />
            <button type="submit" style="color:white; background:#d9534f; border:none; border-radius:4px; padding:5px 10px; cursor:pointer;">
              Delete Tool
            </button>
          </form>
        </div>
        """

    # The 'Add Tool' form
    params_json_placeholder = '[{"name": "region", "type": "string", "required": true}]'
    
    add_tool_form = f"""
    <h3>Add New Tool</h3>
    <div class="help-text">Tools are specialized components that handle specific user requests. Configure each tool's behavior and how it interacts with user data.</div>
    <form action="/admin/tools/add" method="post">
        <input type="hidden" name="return_tab" value="tools" />
        
        <label>Name:</label>
        <input type="text" name="name" placeholder="Enter a unique tool name">
        <div class="help-text">A short, unique identifier for this tool (e.g., "TaxTool", "PayrollAssistant").</div>

        <label>Description:</label>
        <textarea name="description" placeholder="Describe what this tool does"></textarea>
        <div class="help-text">Explain what this tool does and when it should be used. This helps maintain the system and isn't shown to users.</div>

        <label>Priority:</label>
        <input type="number" name="priority" value="100">
        <div class="help-text">Lower numbers = higher priority. If two tools match a query, the lower priority number wins. Tools with equal priority can run in parallel.</div>

        <label>Display Mode:</label>
        <select name="display_mode">
            <option value="as-is">As-Is</option>
            <option value="summarizable">Summarizable</option>
        </select>
        <div class="help-text">'As-is' shows exact tool output to users; 'Summarizable' allows the system to paraphrase or condense the results.</div>

        <label>Index Name:</label>
        <input type="text" name="index_name" placeholder="e.g., taxIndex, payrollIndex">
        <div class="help-text">For retrieval tools, the name of the content index to search. Should match index names in your Content items.</div>

        <label>Top K:</label>
        <input type="number" name="top_k" value="1">
        <div class="help-text">For retrieval tools, the number of documents to fetch initially from the index.</div>

        <label>Reranker:</label>
        <select name="reranker">
            <option value="top1">Top 1</option>
            <option value="top3">Top 3</option>
            <option value="uprank_sdr">Uprank SDR</option>
        </select>
        <div class="help-text">'Top 1' = use best match only; 'Top 3' = consider top 3 matches; 'Uprank SDR' = boost semantically diverse results.</div>

        <label>Parameters JSON:</label>
        <textarea name="parameters_json" placeholder="{params_json_placeholder}">[]</textarea>
        <div class="help-text">Define the parameters this tool accepts as a JSON array of objects. Each parameter should have name, type, and required fields.</div>

        <label>User Fields Filters:</label>
        <!-- Hidden field to store the actual JSON mapping -->
        <textarea name="user_fields_mapping" id="add-user-fields" style="display:none"></textarea>
        <!-- Container for dynamically generated filter fields -->
        <div class="field-filters-container" data-target="add-user-fields"></div>
        <div class="help-text">Set filter values for user profile fields. The tool will only be used when the user's attributes match these filters. For multiple values, use JSON array format: ["value1", "value2"]</div>

        <label>Disambiguation Level (0-10): <span id="add_dval">5</span></label>
        <input type="range" name="disambiguation_level" min="0" max="10" value="5"
               oninput="document.getElementById('add_dval').innerText = this.value">
        <div class="help-text">Controls how often the tool asks users to clarify ambiguous requests: 0 = never ask, 10 = always seek clarification.</div>

        <label style="display:flex; align-items:center;">
            <input type="checkbox" name="can_be_overridden_when_sticky" checked style="margin-right:5px; width: auto;">
            Can Be Overridden When Sticky
        </label>
        <div class="help-text">If checked, the system can switch to another tool mid-conversation when appropriate. Uncheck for multi-step workflows that shouldn't be interrupted.</div>

        <button type="submit" class="save-button" style="margin-top:15px;">Add Tool</button>
    </form>
    """

    # The 'Update Tool' form (hidden by default, populated by JS on click)
    update_tool_form = f"""
    <h3>Update Tool</h3>
    <div class="help-text">Edit the selected tool's configuration.</div>
    <form id="update-tool-form" action="/admin/tools/update" method="post" style="display:none;">
        <input type="hidden" name="tool_index" id="update-tool-index">
        <input type="hidden" name="return_tab" value="tools" />

        <label>Name:</label>
        <input type="text" name="name" id="update-name">
        <div class="help-text">A short, unique identifier for this tool (e.g., "TaxTool", "PayrollAssistant").</div>

        <label>Description:</label>
        <textarea name="description" id="update-description"></textarea>
        <div class="help-text">Explain what this tool does and when it should be used. This helps maintain the system and isn't shown to users.</div>

        <label>Priority:</label>
        <input type="number" name="priority" id="update-priority" value="100">
        <div class="help-text">Lower numbers = higher priority. If two tools match a query, the lower priority number wins. Tools with equal priority can run in parallel.</div>

        <label>Display Mode:</label>
        <select name="display_mode" id="update-display-mode">
            <option value="as-is">As-Is</option>
            <option value="summarizable">Summarizable</option>
        </select>
        <div class="help-text">'As-is' shows exact tool output to users; 'Summarizable' allows the system to paraphrase or condense the results.</div>

        <label>Index Name:</label>
        <input type="text" name="index_name" id="update-index-name">
        <div class="help-text">For retrieval tools, the name of the content index to search. Should match index names in your Content items.</div>

        <label>Top K:</label>
        <input type="number" name="top_k" id="update-top-k" value="1">
        <div class="help-text">For retrieval tools, the number of documents to fetch initially from the index.</div>

        <label>Reranker:</label>
        <select name="reranker" id="update-reranker">
            <option value="top1">Top 1</option>
            <option value="top3">Top 3</option>
            <option value="uprank_sdr">Uprank SDR</option>
        </select>
        <div class="help-text">'Top 1' = use best match only; 'Top 3' = consider top 3 matches; 'Uprank SDR' = boost semantically diverse results.</div>

        <label>Parameters JSON:</label>
        <textarea name="parameters_json" id="update-params-json">[]</textarea>
        <div class="help-text">Define the parameters this tool accepts as a JSON array of objects. Each parameter should have name, type, and required fields.</div>

        <label>User Fields Filters:</label>
        <!-- Hidden field to store the actual JSON mapping -->
        <textarea name="user_fields_mapping" id="update-user-fields" style="display:none"></textarea>
        <!-- Container for dynamically generated filter fields -->
        <div class="field-filters-container" data-target="update-user-fields"></div>
        <div class="help-text">Set filter values for user profile fields. The tool will only be used when the user's attributes match these filters. For multiple values, use JSON array format: ["value1", "value2"]</div>

        <label>Disambiguation Level (0-10): <span id="update_dval">5</span></label>
        <input type="range" name="disambiguation_level" min="0" max="10" value="5"
               id="update-disambiguation-level"
               oninput="document.getElementById('update_dval').innerText = this.value">
        <div class="help-text">Controls how often the tool asks users to clarify ambiguous requests: 0 = never ask, 10 = always seek clarification.</div>

        <label style="display:flex; align-items:center;">
            <input type="checkbox" name="can_be_overridden_when_sticky" id="update-sticky" style="margin-right:5px; width: auto;">
            Can Be Overridden When Sticky
        </label>
        <div class="help-text">If checked, the system can switch to another tool mid-conversation when appropriate. Uncheck for multi-step workflows that shouldn't be interrupted.</div>

        <button type="submit" class="save-button" style="margin-top:15px;">Update Tool</button>
    </form>
    """

    # JavaScript to populate the update form on click and handle the dynamic fields
    script = """
    <script>
    // When a tool entry is clicked, show the update form and populate it
    document.querySelectorAll('.tool-entry').forEach(entry => {
      entry.addEventListener('click', () => {
        // Show the update form
        document.getElementById('update-tool-form').style.display = 'block';

        // Fill the hidden index
        document.getElementById('update-tool-index').value = entry.dataset.toolIndex;

        // Fill each field
        document.getElementById('update-name').value = entry.dataset.name;
        document.getElementById('update-description').value = entry.dataset.description;
        document.getElementById('update-priority').value = entry.dataset.priority;
        document.getElementById('update-display-mode').value = entry.dataset.display_mode;
        document.getElementById('update-index-name').value = entry.dataset.index_name;
        document.getElementById('update-top-k').value = entry.dataset.top_k;
        document.getElementById('update-reranker').value = entry.dataset.reranker;
        document.getElementById('update-params-json').value = entry.dataset.parameters_json;
        document.getElementById('update-user-fields').value = entry.dataset.user_fields_mapping;

        // Disambiguation level slider
        let disLvl = parseInt(entry.dataset.disambiguation_level || '5');
        document.getElementById('update-disambiguation-level').value = disLvl;
        document.getElementById('update_dval').innerText = disLvl;

        // Sticky checkbox
        let sticky = (entry.dataset.can_be_overridden_when_sticky === 'true');
        document.getElementById('update-sticky').checked = sticky;
        
        // Refresh the dynamic field filters
        refreshDynamicUserFields();
        
        // Scroll to the form
        document.getElementById('update-tool-form').scrollIntoView({behavior: 'smooth'});
      });
    });
    
    // Initialize field filters on page load
    document.addEventListener('DOMContentLoaded', () => {
      // Initial load of user fields
      if (document.getElementById('tools').classList.contains('active')) {
        refreshDynamicUserFields();
      }
    });

    // Helper to update the field mappings for user fields that allow arrays
    function updateFieldMappingInput(inputId) {
      const jsonInput = document.getElementById(inputId);
      if (!jsonInput) return;
      
      // Get the container for this input
      const container = document.querySelector(`[data-target="${inputId}"]`);
      if (!container) return;
      
      // Create a new mapping based on current filter values
      const newMapping = {};
      container.querySelectorAll('.filter-value').forEach(input => {
        const field = input.getAttribute('data-field');
        const value = input.value.trim();
        
        // Only add non-empty values
        if (value) {
            try {
                // Try to parse as JSON (for arrays)
                if (value.startsWith('[') && value.endsWith(']')) {
                    newMapping[field] = JSON.parse(value);
                } else {
                    newMapping[field] = value;
                }
            } catch (e) {
                // If JSON parsing fails, use as string
                newMapping[field] = value;
            }
        }
      });
      
      // Update the hidden input
      jsonInput.value = JSON.stringify(newMapping);
    }
    </script>
    """

    return f"""
    <h2>Tools Configuration</h2>
    {intro_guide}
    <p><strong>Existing Tools:</strong> (Click on a tool to edit)</p>
    {existing_tools_html}

    {add_tool_form}
    {update_tool_form}
    {script}
    """

#
# Endpoints for Tools
#
@router_tools.post("/admin/tools/add")
async def add_tool(request: Request):
    form_data = await request.form()
    return_tab = form_data.get("return_tab", "tools")
    
    # Parse user_fields_mapping as JSON object
    user_fields_mapping_str = form_data.get("user_fields_mapping", "{}").strip()
    try:
        user_fields_mapping = json.loads(user_fields_mapping_str) if user_fields_mapping_str else {}
    except json.JSONDecodeError:
        user_fields_mapping = {}
    
    new_tool = ToolData(
        name=form_data.get("name", "Untitled Tool").strip(),
        description=form_data.get("description", "No description").strip(),
        priority=int(form_data.get("priority", "100")),
        display_mode=form_data.get("display_mode", "as-is"),
        index_name=form_data.get("index_name", "").strip(),
        top_k=int(form_data.get("top_k", "1")),
        reranker=form_data.get("reranker", "top1"),
        parameters_json=form_data.get("parameters_json", "[]"),
        user_fields_mapping=user_fields_mapping,
        disambiguation_level=int(form_data.get("disambiguation_level", "5")),
        can_be_overridden_when_sticky=("can_be_overridden_when_sticky" in form_data)
    )

    existing_tools = load_json_config(TOOLS_FILE)
    if not isinstance(existing_tools, list):
        existing_tools = []

    existing_tools.append(new_tool.dict())
    save_json_config(TOOLS_FILE, existing_tools)
    return RedirectResponse(url=f"/admin?tab={return_tab}", status_code=302)


@router_tools.post("/admin/tools/update")
async def update_tool(request: Request):
    form_data = await request.form()
    tool_index = int(form_data.get("tool_index", "-1"))
    return_tab = form_data.get("return_tab", "tools")

    # Parse user_fields_mapping as JSON object
    user_fields_mapping_str = form_data.get("user_fields_mapping", "{}").strip()
    try:
        user_fields_mapping = json.loads(user_fields_mapping_str) if user_fields_mapping_str else {}
    except json.JSONDecodeError:
        user_fields_mapping = {}

    existing_tools = load_json_config(TOOLS_FILE)
    if not isinstance(existing_tools, list):
        existing_tools = []

    if 0 <= tool_index < len(existing_tools):
        updated_tool = ToolData(
            name=form_data.get("name", "Untitled Tool").strip(),
            description=form_data.get("description", "No description").strip(),
            priority=int(form_data.get("priority", "100")),
            display_mode=form_data.get("display_mode", "as-is"),
            index_name=form_data.get("index_name", "").strip(),
            top_k=int(form_data.get("top_k", "1")),
            reranker=form_data.get("reranker", "top1"),
            parameters_json=form_data.get("parameters_json", "[]"),
            user_fields_mapping=user_fields_mapping,
            disambiguation_level=int(form_data.get("disambiguation_level", "5")),
            can_be_overridden_when_sticky=("can_be_overridden_when_sticky" in form_data)
        )
        existing_tools[tool_index] = updated_tool.dict()
        save_json_config(TOOLS_FILE, existing_tools)

    return RedirectResponse(url=f"/admin?tab={return_tab}", status_code=302)


@router_tools.post("/admin/tools/delete")
async def delete_tool(tool_index: int = Form(...), return_tab: str = Form("tools")):
    existing_tools = load_json_config(TOOLS_FILE)
    if not isinstance(existing_tools, list):
        existing_tools = []

    if 0 <= tool_index < len(existing_tools):
        existing_tools.pop(tool_index)
        save_json_config(TOOLS_FILE, existing_tools)

    return RedirectResponse(url=f"/admin?tab={return_tab}", status_code=302)