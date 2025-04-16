# plannerv2/routers/admin_user.py

from plannerv2.models.user import UserConfig
from plannerv2.core.config_manager import load_json_config, save_json_config
import json

# Tool and Content file paths
TOOLS_FILE = "tools.json"
CONTENT_FILE = "content.json"

def clean_outdated_filters(user_json_str):
    """
    Removes any filter fields from tools and content that 
    no longer exist in the user configuration.
    """
    try:
        # Parse the user json to get available fields
        user_fields = set(json.loads(user_json_str).keys())
        
        # Load tools
        tools_data = load_json_config(TOOLS_FILE)
        if isinstance(tools_data, list):
            modified = False
            for tool in tools_data:
                if "user_fields_mapping" in tool:
                    try:
                        mapping = json.loads(tool["user_fields_mapping"])
                        # Remove fields that don't exist in user config
                        outdated_fields = [k for k in mapping.keys() if k not in user_fields]
                        if outdated_fields:
                            modified = True
                            for field in outdated_fields:
                                del mapping[field]
                            tool["user_fields_mapping"] = json.dumps(mapping)
                    except json.JSONDecodeError:
                        # Skip if not valid JSON
                        pass
            
            if modified:
                save_json_config(TOOLS_FILE, tools_data)
        
        # Load content
        content_data = load_json_config(CONTENT_FILE)
        if content_data and "items" in content_data:
            modified = False
            for item in content_data["items"]:
                if "user_fields_mapping" in item:
                    try:
                        mapping = json.loads(item["user_fields_mapping"])
                        # Remove fields that don't exist in user config
                        outdated_fields = [k for k in mapping.keys() if k not in user_fields]
                        if outdated_fields:
                            modified = True
                            for field in outdated_fields:
                                del mapping[field]
                            item["user_fields_mapping"] = json.dumps(mapping)
                    except json.JSONDecodeError:
                        # Skip if not valid JSON
                        pass
                        
            if modified:
                save_json_config(CONTENT_FILE, content_data)
                
    except (json.JSONDecodeError, TypeError, KeyError):
        # If there's an error parsing the user JSON, don't make any changes
        pass

def render_user_tab(user_model: UserConfig) -> str:
    """
    Returns HTML snippet for the User tab fields.
    """
    intro_guide = """
    <div class="guide-panel">
        <h3>How to Configure User Settings</h3>
        <p>User settings define attributes and context that personalize the chatbot's responses.</p>
        <p>The JSON structure below should match fields referenced in Tool and Content configurations.</p>
        <p><strong>Common Fields:</strong></p>
        <ul>
            <li><strong>customerType</strong>: e.g., "premium", "basic", "trial"</li>
            <li><strong>region</strong>: e.g., "US", "EU", "APAC"</li>
            <li><strong>other_context</strong>: Any additional information about the user</li>
        </ul>
        <p>These fields can be used by tools through "User Fields Mapping" to filter or personalize content.</p>
        <p><strong>Note:</strong> When you update user fields, any filter references in Tools and Content will be automatically cleaned up.</p>
    </div>
    """
    
    return f"""
    <h2>User Configuration</h2>
    {intro_guide}
    <label>User JSON:</label>
    <textarea name="user_json" rows="8" id="user-json-field" placeholder='{{"customerType": "premium", "region": "US", "other_context": "Some extra info"}}'>{user_model.user_json}</textarea>
    <div class="help-text">Define user attributes in JSON format. These fields can be referenced by Tools and Content to personalize responses.</div>
    <button type="submit" class="save-button">Save User Config</button>
    
    <script>
    // This script makes the user JSON available to other tabs
    window.getUserFields = function() {{
        const userJson = document.getElementById('user-json-field').value;
        try {{
            return Object.keys(JSON.parse(userJson));
        }} catch (e) {{
            return [];
        }}
    }};
    </script>
    """