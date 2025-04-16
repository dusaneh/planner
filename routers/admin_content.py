# plannerv2/routers/admin_content.py

from fastapi import APIRouter, Request, Form
from starlette.responses import RedirectResponse
from typing import List, Dict, Any, Union
import json
import plannerv2.helper as hlp

from plannerv2.core.config_manager import load_json_config, save_json_config
from plannerv2.models.content import ContentConfig, ContentItem
import plannerv2.retrieval as ret

CONTENT_FILE = "content.json"
router_content = APIRouter()

def render_content_tab(content_list: List[ContentItem]) -> str:
    # Guide text at the top of the tab
    intro_guide = """
    <div class="guide-panel">
        <h3>How to Configure Content</h3>
        <p>Content items are knowledge-base articles that the chatbot can retrieve and present to users.</p>
        <ol>
            <li><strong>Create content items</strong> with useful information for common questions.</li>
            <li><strong>Add query strings</strong> to match different ways users might ask for this information.</li>
            <li><strong>Set the index name</strong> to match with retrieval tools that should access this content.</li>
            <li><strong>Configure User Fields Filters</strong> to show content only to certain types of users.</li>
            <li><strong>Add Tags</strong> to categorize and help with filtering content.</li>
        </ol>
        <p>Click on any existing content item below to edit it.</p>
    </div>
    """
    
    existing_html = ""
    for i, item in enumerate(content_list):
        qstrings = ", ".join(item.query_strings)
        tags = ", ".join(item.tags) if item.tags else "None"
        
        # Convert user_fields_mapping to a JSON string for the data attribute
        user_fields_json = json.dumps(item.user_fields_mapping)
        tags_json = json.dumps(item.tags)
        
        # Ensure index_name has a value for display
        display_index_name = item.index_name if item.index_name else "(none)"
            
        existing_html += f"""
        <div class="content-entry" data-content-index="{i}"
             data-title="{item.title}"
             data-body="{item.body.replace('"','&#34;')}"
             data-index_name="{item.index_name}"
             data-query_strings="{json.dumps(item.query_strings).replace('"','&#34;')}"
             data-user_fields_mapping="{user_fields_json.replace('"','&#34;')}"
             data-tags="{tags_json.replace('"','&#34;')}"
             style="border:1px solid #ddd; padding:10px; margin-bottom:10px; border-radius:5px; cursor:pointer;">
          <strong>Title:</strong> {item.title}<br/>
          <strong>Body:</strong> {item.body[:100]}{"..." if len(item.body) > 100 else ""}<br/>
          <strong>Index Name:</strong> {display_index_name}<br/>
          <strong>Query Strings:</strong> {qstrings}<br/>
          <strong>User Fields Filters:</strong> <pre>{user_fields_json}</pre>
          <strong>Tags:</strong> {tags}<br/>

          <!-- Delete button -->
          <form action="/admin/content/delete" method="post" style="margin-top:10px;">
            <input type="hidden" name="content_index" value="{i}" />
            <input type="hidden" name="return_tab" value="content" />
            <button type="submit" style="color:white; background:#d9534f; border:none; border-radius:4px; padding:5px 10px; cursor:pointer;">
              Delete Content
            </button>
          </form>
        </div>
        """

    add_form = f"""
    <h3>Add New Content Item</h3>
    <div class="help-text">Create new knowledge-base content that the chatbot can present to users.</div>
    <form action="/admin/content/add" method="post">
        <input type="hidden" name="return_tab" value="content" />
        
        <label>Title:</label>
        <input type="text" name="title" placeholder="Enter a descriptive title">
        <div class="help-text">A short, descriptive title for this content item (e.g., "How to Add Payroll").</div>

        <label>Body:</label>
        <textarea name="body" placeholder="Enter the main content..." rows="6"></textarea>
        <div class="help-text">The main content or answer that will be shown to users. Be concise but thorough.</div>

        <label>Index Name:</label>
        <input type="text" name="index_name" placeholder="e.g., taxIndex, payrollIndex">
        <div class="help-text">The index this content belongs to. Tools with matching index names can retrieve this content.</div>

        <label>Query Strings (JSON array format):</label>
        <textarea name="query_strings" placeholder='["how do I add payroll?", "setting up payroll"]'></textarea>
        <div class="help-text">Enter as a JSON array. These are different ways users might ask for this information.</div>

        <label>Tags (JSON array format):</label>
        <textarea name="tags" placeholder='["payroll", "setup", "configuration"]'></textarea>
        <div class="help-text">Enter as a JSON array. These tags categorize the content and help with filtering.</div>

        <label>User Fields Filters:</label>
        <!-- Hidden field to store the actual JSON mapping -->
        <textarea name="user_fields_mapping" id="add-content-user-fields" style="display:none"></textarea>
        <!-- Container for dynamically generated filter fields -->
        <div class="field-filters-container" data-target="add-content-user-fields"></div>
        <div class="help-text">Set filter values for user profile fields. The content will only be shown to users matching these filters. For multiple values, use JSON array format: ["value1", "value2"]</div>

        <button type="submit" class="save-button" style="margin-top:15px;">Add Content Item</button>
    </form>
    """

    update_form = f"""
    <h3>Update Content Item</h3>
    <div class="help-text">Edit the selected content item.</div>
    <form id="update-content-form" action="/admin/content/update" method="post" style="display:none;">
        <input type="hidden" name="content_index" id="update-content-index">
        <input type="hidden" name="return_tab" value="content" />

        <label>Title:</label>
        <input type="text" name="title" id="update-title">
        <div class="help-text">A short, descriptive title for this content item (e.g., "How to Add Payroll").</div>

        <label>Body:</label>
        <textarea name="body" id="update-body" rows="6"></textarea>
        <div class="help-text">The main content or answer that will be shown to users. Be concise but thorough.</div>

        <label>Index Name:</label>
        <input type="text" name="index_name" id="update-index-name">
        <div class="help-text">The index this content belongs to. Tools with matching index names can retrieve this content.</div>

        <label>Query Strings (JSON array format):</label>
        <textarea name="query_strings" id="update-query-strings"></textarea>
        <div class="help-text">Enter as a JSON array. These are different ways users might ask for this information.</div>

        <label>Tags (JSON array format):</label>
        <textarea name="tags" id="update-tags"></textarea>
        <div class="help-text">Enter as a JSON array. These tags categorize the content and help with filtering.</div>

        <label>User Fields Filters:</label>
        <!-- Hidden field to store the actual JSON mapping -->
        <textarea name="user_fields_mapping" id="update-content-user-fields" style="display:none"></textarea>
        <!-- Container for dynamically generated filter fields -->
        <div class="field-filters-container" data-target="update-content-user-fields"></div>
        <div class="help-text">Set filter values for user profile fields. The content will only be shown to users matching these filters. For multiple values, use JSON array format: ["value1", "value2"]</div>

        <button type="submit" class="save-button" style="margin-top:15px;">Update Content Item</button>
    </form>
    """

    script = """
    <script>
    // When a content entry is clicked, show the update form and populate it
    // When a content entry is clicked, show the update form and populate it
// When a content entry is clicked, show the update form and populate it
document.querySelectorAll('.content-entry').forEach(entry => {
  entry.addEventListener('click', () => {
    document.getElementById('update-content-form').style.display = 'block';
    document.getElementById('update-content-index').value = entry.dataset.contentIndex;
    document.getElementById('update-title').value = entry.dataset.title;
    document.getElementById('update-body').value = entry.dataset.body;
    
    // This is the critical line - make sure it exactly matches your input field's ID
    document.getElementById('update-index-name').value = entry.dataset.index_name;
    
    document.getElementById('update-query-strings').value = entry.dataset.query_strings;
    document.getElementById('update-tags').value = entry.dataset.tags;
    document.getElementById('update-content-user-fields').value = entry.dataset.user_fields_mapping;
    
    // Refresh the dynamic field filters
    refreshDynamicUserFields();
    
    // Scroll to the form
    document.getElementById('update-content-form').scrollIntoView({behavior: 'smooth'});
  });
});
    
    // Initialize field filters on page load
    document.addEventListener('DOMContentLoaded', () => {
      // Initial load of user fields
      if (document.getElementById('content').classList.contains('active')) {
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
                } else if (value.includes(',')) {
                    // If it contains commas, split it into an array of strings
                    newMapping[field] = value.split(',').map(item => item.trim()).filter(item => item);
                } else {
                    newMapping[field] = value;
                }
            } catch (e) {
                // If JSON parsing fails, use as string
                if (value.includes(',')) {
                    // If it contains commas, split it into an array of strings
                    newMapping[field] = value.split(',').map(item => item.trim()).filter(item => item);
                } else {
                    newMapping[field] = value;
                }
            }
        }
    });
    
    // Update the hidden input
    jsonInput.value = JSON.stringify(newMapping);
    }
    </script>
    """

    return f"""
    <h2>Content Configuration</h2>
    {intro_guide}
    <p><strong>Existing Content Items:</strong> (Click on an item to edit)</p>
    {existing_html}
    {add_form}
    {update_form}
    {script}
    """

#
# Endpoints for Content
@router_content.post("/admin/content/add")
async def add_content_item(request: Request):
    form_data = await request.form()
    return_tab = form_data.get("return_tab", "content")
    
    title = form_data.get("title", "").strip()
    body = form_data.get("body", "").strip()
    index_name = form_data.get("index_name", "").strip()
    raw_qstrings = form_data.get("query_strings", "").strip()
    raw_tags = form_data.get("tags", "").strip()
    user_fields_mapping_str = form_data.get("user_fields_mapping", "{}").strip()

    # Parse query strings as JSON array
    try:
        q_list = json.loads(raw_qstrings) if raw_qstrings else []
        # Ensure it's a list of strings
        if not isinstance(q_list, list):
            q_list = [str(q_list)]
        else:
            q_list = [str(q) for q in q_list]
    except json.JSONDecodeError:
        # Fallback to comma-separated handling
        q_list = [q.strip() for q in raw_qstrings.split(",") if q.strip()]
    
    # Parse tags as JSON array
    try:
        tags_list = json.loads(raw_tags) if raw_tags else []
        # Ensure it's a list of strings
        if not isinstance(tags_list, list):
            tags_list = [str(tags_list)]
        else:
            tags_list = [str(tag) for tag in tags_list]
    except json.JSONDecodeError:
        # Fallback to comma-separated handling
        tags_list = [tag.strip() for tag in raw_tags.split(",") if tag.strip()]
    
    # Parse user_fields_mapping as JSON object
    try:
        user_fields_mapping = json.loads(user_fields_mapping_str) if user_fields_mapping_str else {}
    except json.JSONDecodeError:
        user_fields_mapping = {}

    existing_data = load_json_config(CONTENT_FILE)
    if not existing_data or "items" not in existing_data:
        existing_data = {"items": []}

    content_config = ContentConfig(**existing_data)
    new_item = ContentItem(
        title=title,
        body=body,
        index_name=index_name,
        query_strings=q_list,
        user_fields_mapping=user_fields_mapping,
        tags=tags_list
    )
    content_config.items.append(new_item)
    save_json_config(CONTENT_FILE, content_config.dict())
    
    # Print the index_name that was just added for debugging
    print(f"Added new content item with index_name: '{index_name}'")
    
    # Rebuild indexes with improved error handling
    try:
        print("Starting index rebuild after content addition...")
        # Use the helper to load all configs
        configs = hlp.load_all_configs()
        # Create an indexer
        indexer = ret.ContentIndexer()
        # Print all index names for debugging
        unique_indexes = set(item.index_name for item in content_config.items if item.index_name)
        print(f"Unique indexes in content: {list(unique_indexes)}")
        # Build all indexes with the complete content config
        ret.build_all_indexes(configs["content"], indexer)
        print("Index rebuild completed successfully")
    except Exception as e:
        print(f"Error building indexes: {e}")
        import traceback
        print(traceback.format_exc())
    
    return RedirectResponse(url=f"/admin?tab={return_tab}", status_code=302)


@router_content.post("/admin/content/update")
async def update_content_item(request: Request):
    form_data = await request.form()
    c_index = int(form_data.get("content_index", "-1"))
    return_tab = form_data.get("return_tab", "content")
    
    title = form_data.get("title", "").strip()
    body = form_data.get("body", "").strip()
    index_name = form_data.get("index_name", "").strip()
    raw_qstrings = form_data.get("query_strings", "").strip()
    raw_tags = form_data.get("tags", "").strip()
    user_fields_mapping_str = form_data.get("user_fields_mapping", "{}").strip()

    # Print received data for debugging
    print(f"Updating content item {c_index} with index_name: '{index_name}'")

    # Parse query strings as JSON array
    try:
        q_list = json.loads(raw_qstrings) if raw_qstrings else []
        # Ensure it's a list of strings
        if not isinstance(q_list, list):
            q_list = [str(q_list)]
        else:
            q_list = [str(q) for q in q_list]
    except json.JSONDecodeError:
        # Fallback to comma-separated handling
        q_list = [q.strip() for q in raw_qstrings.split(",") if q.strip()]
    
    # Parse tags as JSON array
    try:
        tags_list = json.loads(raw_tags) if raw_tags else []
        # Ensure it's a list of strings
        if not isinstance(tags_list, list):
            tags_list = [str(tags_list)]
        else:
            tags_list = [str(tag) for tag in tags_list]
    except json.JSONDecodeError:
        # Fallback to comma-separated handling
        tags_list = [tag.strip() for tag in raw_tags.split(",") if tag.strip()]
    
    # Parse user_fields_mapping as JSON object
    try:
        user_fields_mapping = json.loads(user_fields_mapping_str) if user_fields_mapping_str else {}
    except json.JSONDecodeError:
        user_fields_mapping = {}

    existing_data = load_json_config(CONTENT_FILE)
    if not existing_data or "items" not in existing_data:
        existing_data = {"items": []}

    content_config = ContentConfig(**existing_data)
    
    if 0 <= c_index < len(content_config.items):
        # Store old index name for debugging
        old_index_name = content_config.items[c_index].index_name
        
        # Update the content item
        content_config.items[c_index].title = title
        content_config.items[c_index].body = body
        content_config.items[c_index].index_name = index_name
        content_config.items[c_index].query_strings = q_list
        content_config.items[c_index].user_fields_mapping = user_fields_mapping
        content_config.items[c_index].tags = tags_list

        # Print index update for debugging
        print(f"Updated index_name from '{old_index_name}' to '{index_name}'")

        # Save the updated config
        save_json_config(CONTENT_FILE, content_config.dict())
        
        try:
            # Print all content items with their index names for debugging
            print("Current content items:")
            for idx, item in enumerate(content_config.items):
                print(f"  Item {idx}: '{item.title}' - index_name: '{item.index_name}'")
            
            # Get unique index names
            unique_indexes = set(item.index_name for item in content_config.items if item.index_name)
            print(f"Unique indexes in content: {list(unique_indexes)}")
            
            # Rebuild indexes
            print("Starting index rebuild after content update...")
            # Use the helper to load all configs
            configs = hlp.load_all_configs()
            # Create an indexer
            indexer = ret.ContentIndexer()
            # Build all indexes with the complete content config
            ret.build_all_indexes(configs["content"], indexer)
            print("Index rebuild completed successfully")
            
            # Run diagnosis
            # print("Running retrieval system diagnosis...")
            # ret.diagnose_retrieval_system()
            
        except Exception as e:
            print(f"Error building indexes: {e}")
            import traceback
            print(traceback.format_exc())
        
    return RedirectResponse(url=f"/admin?tab={return_tab}", status_code=302)


@router_content.post("/admin/content/delete")
async def delete_content_item(content_index: int = Form(...), return_tab: str = Form("content")):
    existing_data = load_json_config(CONTENT_FILE)
    if not existing_data or "items" not in existing_data:
        existing_data = {"items": []}

    content_config = ContentConfig(**existing_data)
    
    if 0 <= content_index < len(content_config.items):
        # Store deleted item's index name for debugging
        deleted_index_name = content_config.items[content_index].index_name
        print(f"Deleting content item with index_name: '{deleted_index_name}'")
        
        # Remove the item
        content_config.items.pop(content_index)
        save_json_config(CONTENT_FILE, content_config.dict())
        
        # Rebuild indexes after content is deleted
        try:
            # Get unique index names after deletion
            unique_indexes = set(item.index_name for item in content_config.items if item.index_name)
            print(f"Remaining unique indexes after deletion: {list(unique_indexes)}")
            
            # Create an indexer
            indexer = ret.ContentIndexer()
            # Build all indexes with the updated content
            ret.build_all_indexes(content_config.dict(), indexer)
            print("Index rebuild completed after deletion")
        except Exception as e:
            print(f"Error building indexes: {e}")
            import traceback
            print(traceback.format_exc())

    return RedirectResponse(url=f"/admin?tab={return_tab}", status_code=302)