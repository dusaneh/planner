# plannerv2/routers/admin_planner.py

from plannerv2.models.planner import PlannerConfig

def render_planner_tab(planner_model: PlannerConfig) -> str:
    """
    Returns HTML snippet for the Planner tab fields.
    The <form> and action will be wrapped in admin_main.py.
    """
    return f"""
    <h2>Planner Configuration</h2>
    <p>The Planner decides how the chatbot routes user questions to the appropriate tools.</p>
    
    <label>Planner Mode:</label>
    <select name="mode">
        <option value="fast" {"selected" if planner_model.mode == "fast" else ""}>Fast</option>
        <option value="fast_listen_override" {"selected" if planner_model.mode == "fast_listen_override" else ""}>Fast Listen Override</option>
        <option value="smart" {"selected" if planner_model.mode == "smart" else ""}>Smart</option>
    </select>
    <div class="help-text">
        <ul>
            <li><strong>Fast:</strong> Minimizes latency; picks answers quickly, prioritizing speed over thoroughness.</li>
            <li><strong>Fast Listen Override:</strong> Similar to Fast, but can interrupt an ongoing session if user questions change focus.</li>
            <li><strong>Smart:</strong> Performs deeper analysis for better accuracy but with higher latency.</li>
        </ul>
    </div>

    <label>Relevance Threshold (0-100): <span id="relevance_threshold_value">{planner_model.relevance_threshold}</span></label>
    <input type="range" name="relevance_threshold" min="0" max="100" value="{planner_model.relevance_threshold}"
           oninput="document.getElementById('relevance_threshold_value').innerText = this.value">
    <div class="help-text">
        Higher values make routing to tools less likely. At 100, the system requires a very strong match to select a tool.
    </div>

    <button type="submit" class="save-button">Save Planner Config</button>
    """