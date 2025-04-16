import google.generativeai as genai
from pydantic import BaseModel, Field
from typing import Optional, List, Type, Dict, Any
import json
import keys


import google.generativeai as genai
from pydantic import BaseModel, Field
from typing import Optional, List, Type, Dict, Any
import re

google_api_key=keys.google_api_key


# def generate_structured_analysis(
#     structured_output_class: Type[BaseModel],
#     user_message: str,
#     message_history: list,
#     google_api_key: str,
#     system_prompt: str
# ) -> dict:
#     """
#     Calls Gemini with the provided parameters, then analyzes the returned structured output.

#     Returns a dictionary with:
#       - 'structured_output': the Pydantic model instance
#       - 'missing_required_fields': list of required fields not populated
#       - 'missing_optional_fields': list of optional fields not populated
#       - 'populated_fields': list of fields that are populated
#       - 'all_missing_fields': list of all fields (required or optional) that are missing
#     """
#     # Configure the Gemini API with your key
#     genai.configure(api_key=google_api_key)
    
#     # Create a model instance
#     model = genai.GenerativeModel('gemini-1.5-pro')
    
#     # Start a chat session
#     chat = model.start_chat(history=[])
    
#     # Build a prompt that explains the structured output format
#     model_schema = structured_output_class.model_json_schema()
#     required_fields = model_schema.get("required", [])
#     properties = model_schema.get("properties", {})
    
#     field_descriptions = []
#     for field_name, field_info in properties.items():
#         desc = field_info.get("description", "")
#         req = "required" if field_name in required_fields else "optional"
#         field_type = field_info.get("type", "")
#         field_descriptions.append(f"- {field_name}: {desc} ({req}, type: {field_type})")
    
#     field_desc_text = "\n".join(field_descriptions)
    
#     # Build complete prompt with system instructions, schema, conversation history, and current message
#     prompt = f"""
# {system_prompt}

# You must respond with valid JSON that matches this schema:
# {json.dumps(model_schema, indent=2)}

# Field descriptions:
# {field_desc_text}

# Please format your response as a JSON object only, with no additional text.

# Conversation history:
# """
    
#     # Add conversation history
#     for msg in message_history:
#         role = msg["role"]
#         content = msg["content"]
#         prompt += f"\n{role.upper()}: {content}"
    
#     # Add current user message
#     prompt += f"\n\nUSER: {user_message}\n\nJSON response:"
    
#     try:
#         # Send the prompt to the model
#         response = chat.send_message(prompt)
#         response_text = response.text
        
#         # Extract JSON from the response
#         try:
#             # Sometimes the model might wrap the JSON in markdown code blocks
#             if "```json" in response_text:
#                 json_text = response_text.split("```json")[1].split("```")[0].strip()
#             elif "```" in response_text:
#                 json_text = response_text.split("```")[1].split("```")[0].strip()
#             else:
#                 json_text = response_text.strip()
            
#             # Parse the JSON
#             output_data = json.loads(json_text)
            
#             # Create a Pydantic model instance
#             output = structured_output_class(**output_data)
            
#             # Field analysis
#             model_fields = structured_output_class.model_fields
#             required_fields = {name for name, field in model_fields.items() if field.default is ...}
#             optional_fields = set(model_fields.keys()) - required_fields
            
#             # Determine which fields are populated (non-None)
#             populated_fields = {name for name in model_fields if getattr(output, name, None) is not None}
            
#             # Identify missing fields
#             missing_required = list(required_fields - populated_fields)
#             missing_optional = list(optional_fields - populated_fields)
#             all_missing = list((required_fields | optional_fields) - populated_fields)
            
#             return {
#                 "structured_output": output,
#                 "missing_required_fields": missing_required,
#                 "missing_optional_fields": missing_optional,
#                 "populated_fields": list(populated_fields),
#                 "all_missing_fields": all_missing,
#                 "raw_response": response_text
#             }
            
#         except json.JSONDecodeError as e:
#             return {
#                 "structured_output": None,
#                 "missing_required_fields": [],
#                 "missing_optional_fields": [],
#                 "populated_fields": [],
#                 "all_missing_fields": [],
#                 "error": f"JSON parsing error: {str(e)}",
#                 "raw_response": response_text
#             }
            
#     except Exception as e:
#         return {
#             "structured_output": None,
#             "missing_required_fields": [],
#             "missing_optional_fields": [],
#             "populated_fields": [],
#             "all_missing_fields": [],
#             "error": str(e),
#             "raw_response": None
#         }


def generate_schema_for_tools(tools_list):
    """
    Generate a custom schema string for tools with parameters and a relevance_score.
    
    Args:
        tools_list: List of tool dictionaries containing 'name', 'description', and 'parameters_json'
        
    Returns:
        Modified tools list with string_schema added to each tool
    """
    result = []
    
    # Start building the schema string
    schema_parts = []
    
    for i, tool in enumerate(tools_list):
        # Parse the parameters_json string into Python object
        try:
            parameters = json.loads(tool['parameters_json'])
        except (json.JSONDecodeError, TypeError):
            parameters = []
        
        # Add tool name to schema
        schema_parts.append(f"    '{tool['name']}':{{")
        
        # Add parameters
        param_lines = []
        for param in parameters:
            required_text = "required" if param.get('required', False) else "optional"
            param_lines.append(
                f"        '{param['name']}' = '{param['type']}',# {required_text} / {param['description']}"
            )
        
        # Add relevance_score parameter
        param_lines.append(
            f"""        'relevance_score' = 'integer',# required / The relevance score of the "{tool['name']}" tool based soley on the function/tool description (not its parameters) from 0 to 100 with 100 being the most relevant and 0 being the least relevant"""
        )
        param_lines.append(
            f"""        'required_fields_completed' = 'integer',# required / Score from 0-100 indicating that the extent that values imputed for the required fields fit the descriptions of the required fields provided. 0 being least fitting the parameter criteria and 100 perfectly fitting the criteria. Even though something can be added for the field, it is not the same thing as fitting the criteria perfectly, for example 'age' field might be populated given that the user is a teen with a value from 13-19, but if the criteria is for 'age' to be a value between 18-65, then the field is not fitting the criteria perfectly. The field 'country' might be populated with 'France' if the context provided gave Paris, but this may not be the correct country for Paris so the score would be less than 100."""
        )
        
        # Join parameter lines
        if param_lines:
            schema_parts.append("\n" + "\n".join(param_lines))
        
        # Close the tool object
        if i < len(tools_list) - 1:
            schema_parts.append("\n    },\n")
        else:
            schema_parts.append("\n    }")
    
    # Close the schema array
    #schema_parts.append("\n]")
    
    # Join all parts to create the final schema string
    schema_string = "".join(schema_parts)
    
    # Add the schema string to each tool in the result
    for tool in tools_list:
        tool_copy = tool.copy()
        tool_copy['string_schema'] = schema_string
        result.append(tool_copy)
    
    return result[0]['string_schema']

def load_all_configs():
    """
    Loads all configuration files (planner, user, tools, content) and returns them as dictionaries.
    
    Returns:
        dict: A dictionary containing all configuration objects with the following keys:
            - 'planner': The planner configuration
            - 'user': The user configuration 
            - 'tools': The tools configuration
            - 'content': The content configuration with 'items' list
            - 'user_data': Parsed user JSON data (as a dictionary rather than a string)
    """
    from plannerv2.core.config_manager import load_json_config
    import json
    
    # Define all config files
    PLANNER_FILE = "planner.json"
    USER_FILE = "user.json"
    TOOLS_FILE = "tools.json"
    CONTENT_FILE = "content.json"
    
    # Load all configs
    planner_config = load_json_config(PLANNER_FILE)
    user_config = load_json_config(USER_FILE)
    tools_config = load_json_config(TOOLS_FILE)
    content_config = load_json_config(CONTENT_FILE)
    
    # Ensure we have valid data structures (with defaults if files are missing/empty)
    if not planner_config:
        planner_config = {"mode": "fast"}
    
    if not user_config:
        user_config = {"user_json": "{}"}
    
    if not isinstance(tools_config, list):
        tools_config = []
    
    if not content_config or "items" not in content_config:
        content_config = {"items": []}
    
    # Parse the user_json string into an actual dictionary
    try:
        user_data = json.loads(user_config.get("user_json", "{}"))
    except json.JSONDecodeError:
        user_data = {}
    
    # Return all configs in a dictionary
    return {
        "planner": planner_config,
        "user": user_config,
        "tools": tools_config,
        "content": content_config,
        "user_data": user_data
    }





def generate_structured_analysis(
    structured_output_class: Type[BaseModel],
    user_message: str,
    message_history: list,
    google_api_key: str,
    system_prompt: str
) -> dict:
    """
    Calls Gemini with the provided parameters, then analyzes the returned structured output.

    Returns a dictionary with:
      - 'structured_output': the Pydantic model instance
      - 'missing_required_fields': list of required fields not populated
      - 'missing_optional_fields': list of optional fields not populated
      - 'populated_fields': list of fields that are populated
      - 'all_missing_fields': list of all fields (required or optional) that are missing
    """
    # Configure the Gemini API with your key
    genai.configure(api_key=google_api_key)
    
    # Create a model instance
    model = genai.GenerativeModel('gemini-1.5-pro')
    
    # Start a chat session
    chat = model.start_chat(history=[])
    
    # Build a prompt that explains the structured output format
    model_schema = structured_output_class.model_json_schema()
    required_fields = model_schema.get("required", [])
    properties = model_schema.get("properties", {})
    
    field_descriptions = []
    for field_name, field_info in properties.items():
        desc = field_info.get("description", "")
        req = "required" if field_name in required_fields else "optional"
        field_type = field_info.get("type", "")
        field_descriptions.append(f"- {field_name}: {desc} ({req}, type: {field_type})")
    
    field_desc_text = "\n".join(field_descriptions)
    
    # Build complete prompt with system instructions, schema, conversation history, and current message
    prompt = f"""
{system_prompt}

You must respond with valid JSON that matches this schema:
{json.dumps(model_schema, indent=2)}

Field descriptions:
{field_desc_text}

Please format your response as a JSON object only, with no additional text.

Conversation history:
"""
    
    # Add conversation history
    for msg in message_history:
        role = msg["role"]
        content = msg["content"]
        prompt += f"\n{role.upper()}: {content}"
    
    # Add current user message
    prompt += f"\n\nUSER: {user_message}\n\nJSON response:"
    
    try:
        # Send the prompt to the model
        response = chat.send_message(prompt)
        response_text = response.text
        
        # Extract JSON from the response
        try:
            # Sometimes the model might wrap the JSON in markdown code blocks
            if "```json" in response_text:
                json_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                json_text = response_text.split("```")[1].split("```")[0].strip()
            else:
                json_text = response_text.strip()
            
            # Parse the JSON
            output_data = json.loads(json_text)
            
            # Create a Pydantic model instance
            output = structured_output_class(**output_data)
            
            # Field analysis
            model_fields = structured_output_class.model_fields
            required_fields = {name for name, field in model_fields.items() if field.default is ...}
            optional_fields = set(model_fields.keys()) - required_fields
            
            # Determine which fields are populated (non-None)
            populated_fields = {name for name in model_fields if getattr(output, name, None) is not None}
            
            # Identify missing fields
            missing_required = list(required_fields - populated_fields)
            missing_optional = list(optional_fields - populated_fields)
            all_missing = list((required_fields | optional_fields) - populated_fields)
            
            return {
                "structured_output": output,
                "missing_required_fields": missing_required,
                "missing_optional_fields": missing_optional,
                "populated_fields": list(populated_fields),
                "all_missing_fields": all_missing,
                "raw_response": response_text
            }
            
        except json.JSONDecodeError as e:
            return {
                "structured_output": None,
                "missing_required_fields": [],
                "missing_optional_fields": [],
                "populated_fields": [],
                "all_missing_fields": [],
                "error": f"JSON parsing error: {str(e)}",
                "raw_response": response_text
            }
            
    except Exception as e:
        return {
            "structured_output": None,
            "missing_required_fields": [],
            "missing_optional_fields": [],
            "populated_fields": [],
            "all_missing_fields": [],
            "error": str(e),
            "raw_response": None
        }



def generate_flexible_structure(
    user_message: str,
    message_history: list,
    google_api_key: str,
    system_prompt: str,
    model_name: str = 'gemini-1.5-pro'
):
    

    # Configure the Gemini API with your key
    genai.configure(api_key=google_api_key)
    
    # Create a model instance
    model = genai.GenerativeModel(model_name)
    
    # Start a chat session
    chat = model.start_chat(history=[])

    prompt = f"""
    {system_prompt}

    """

    # Add conversation history
    for msg in message_history:
        role = msg["role"]
        content = msg["content"]
        prompt += f"\n{role.upper()}: {content}"
    
    # Add current user message
    prompt += f"\n\nUSER: {user_message}\n\nJSON response:"
    
    try:
        # Send the prompt to the model
        response = chat.send_message(prompt)
        response_text = response.text

        return response, response_text

    except Exception as e:
        print(f"error: {e}")
        return None,None





def parse_json_from_text(text):
    """
    Extract JSON from text that might contain extra content.
    
    Args:
        text (str): Text that contains JSON, possibly with prefixes like 'json    '
        
    Returns:
        dict: Parsed JSON object
    """
    # Try to find JSON portion using regex
    json_match = re.search(r'({[\s\S]*}|\[[\s\S]*\])', text)
    if json_match:
        json_text = json_match.group(0)
    else:
        json_text = text
    
    # Try to parse the JSON
    try:
        return json.loads(json_text)
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse JSON: {e}")



def validate_and_coerce_param(value, expected_type):
    """
    Validate a parameter value against an expected type and try to coerce if needed.
    
    Args:
        value: The parameter value to validate
        expected_type (str): The expected type as a string ('string', 'integer', 'float', etc.)
        
    Returns:
        dict: Dictionary with 'valid' (bool) and 'value' (coerced value if valid)
    """
    result = {'valid': False, 'value': value}
    
    # Handle different expected types
    if expected_type == 'string':
        result['valid'] = isinstance(value, str)
    
    elif expected_type == 'integer':
        if isinstance(value, int) and not isinstance(value, bool):
            result['valid'] = True
        elif isinstance(value, (str, float)):
            try:
                result['value'] = int(float(value))
                result['valid'] = True
            except (ValueError, TypeError):
                pass
    
    elif expected_type == 'float' or expected_type == 'number':
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            result['valid'] = True
            if expected_type == 'float':
                result['value'] = float(value)
        elif isinstance(value, str):
            try:
                result['value'] = float(value)
                result['valid'] = True
            except (ValueError, TypeError):
                pass
    
    elif expected_type == 'boolean' or expected_type == 'bool':
        if isinstance(value, bool):
            result['valid'] = True
        elif isinstance(value, (int, str)):
            if isinstance(value, int):
                result['value'] = bool(value)
                result['valid'] = True
            elif value.lower() in ('true', 'false', '1', '0'):
                result['value'] = value.lower() in ('true', '1')
                result['valid'] = True
    
    elif expected_type == 'array' or expected_type == 'list':
        result['valid'] = isinstance(value, list)
    
    elif expected_type == 'object' or expected_type == 'dict':
        result['valid'] = isinstance(value, dict)
        
    else:
        # For any other type, consider it valid as we don't know how to validate it
        result['valid'] = True
    
    return result


def validate_and_restructure(input_json, schema_list):
    """
    Validate the input JSON against the schema and restructure the output.
    
    Args:
        input_json (str or dict): JSON string or dictionary to validate
        schema_list (list): List of tool dictionaries with schema information
        
    Returns:
        dict: Restructured and validated output
    """
    # Parse input if it's a string
    if isinstance(input_json, str):
        parsed_input = parse_json_from_text(input_json)
    else:
        parsed_input = input_json
    
    # Create a schema dictionary for easy lookup
    schema_dict = {}
    for tool in schema_list:
        name = tool['name']
        try:
            params = json.loads(tool['parameters_json'])
        except (json.JSONDecodeError, TypeError):
            params = []
        
        required_params = {p['name']: p['type'] for p in params if p.get('required', False)}
        optional_params = {p['name']: p['type'] for p in params if not p.get('required', False)}
        
        schema_dict[name] = {
            'required': required_params,
            'optional': optional_params
        }
    
    # Initialize result structure
    result = {}
    
    # Process each tool in the input
    for tool_name, tool_data in parsed_input.items():
        # Initialize the result structure for this tool
        result[tool_name] = {
            'parameters': {},
            'relevance_score': None,
            'required_fields_completed': None,
            'validation': {
                'relevance_score_error': False,
                'required_fields_completed_error': False,
                'required_params_error': False,
                'missing_required_params': [],
                'missing_or_invalid_optional_params': [],
                'fields_found': [],
                'error_string': ""
            }
        }
        
        errors = []
        
        # Extract and validate relevance_score
        if 'relevance_score' in tool_data:
            relevance_score = tool_data['relevance_score']
            
            # Try to coerce to integer if needed
            if not isinstance(relevance_score, int):
                try:
                    relevance_score = int(float(relevance_score))
                except (ValueError, TypeError):
                    result[tool_name]['validation']['relevance_score_error'] = True
                    errors.append(f"Relevance score is not a valid integer: {relevance_score}")
            
            # Check range
            if isinstance(relevance_score, int):
                if not (0 <= relevance_score <= 100):
                    result[tool_name]['validation']['relevance_score_error'] = True
                    errors.append(f"Relevance score out of range (0-100): {relevance_score}")
                else:
                    result[tool_name]['relevance_score'] = relevance_score
                    result[tool_name]['validation']['fields_found'].append('relevance_score')
        else:
            result[tool_name]['validation']['relevance_score_error'] = True
            errors.append("Relevance score is missing")


        # Extract and validate required_fields_completed
        if 'required_fields_completed' in tool_data:
            required_fields_completed = tool_data['required_fields_completed']
            
            # Try to coerce to integer if needed
            if not isinstance(required_fields_completed, int):
                try:
                    required_fields_completed = int(float(required_fields_completed))
                except (ValueError, TypeError):
                    result[tool_name]['validation']['required_fields_completed_error'] = True
                    errors.append(f"Relevance score is not a valid integer: {required_fields_completed}")
            
            # Check range
            if isinstance(required_fields_completed, int):
                if not (0 <= required_fields_completed <= 100):
                    result[tool_name]['validation']['required_fields_completed_error'] = True
                    errors.append(f"Relevance score out of range (0-100): {required_fields_completed}")
                else:
                    result[tool_name]['required_fields_completed'] = required_fields_completed
                    result[tool_name]['validation']['fields_found'].append('required_fields_completed')
        else:
            result[tool_name]['validation']['required_fields_completed_error'] = True
            errors.append("Required fields completed score is missing")
        
        # Get the schema for this tool if it exists
        tool_schema = schema_dict.get(tool_name, {'required': {}, 'optional': {}})
        
        # Validate required parameters
        for param_name, expected_type in tool_schema['required'].items():
            if param_name in tool_data:
                param_value = tool_data[param_name]
                # Validate type and try to coerce if needed
                valid_param = validate_and_coerce_param(param_value, expected_type)
                
                if valid_param['valid']:
                    result[tool_name]['parameters'][param_name] = valid_param['value']
                    result[tool_name]['validation']['fields_found'].append(param_name)
                else:
                    result[tool_name]['validation']['required_params_error'] = True
                    result[tool_name]['validation']['missing_required_params'].append(param_name)
                    errors.append(f"Required parameter '{param_name}' has invalid type. Expected {expected_type}, got {type(param_value).__name__}")
            else:
                result[tool_name]['validation']['required_params_error'] = True
                result[tool_name]['validation']['missing_required_params'].append(param_name)
                errors.append(f"Required parameter '{param_name}' is missing")
        
        # Validate optional parameters
        for param_name, expected_type in tool_schema['optional'].items():
            if param_name in tool_data:
                param_value = tool_data[param_name]
                # Validate type and try to coerce if needed
                valid_param = validate_and_coerce_param(param_value, expected_type)
                
                if valid_param['valid']:
                    result[tool_name]['parameters'][param_name] = valid_param['value']
                    result[tool_name]['validation']['fields_found'].append(param_name)
                else:
                    result[tool_name]['validation']['missing_or_invalid_optional_params'].append(param_name)
                    errors.append(f"Optional parameter '{param_name}' has invalid type. Expected {expected_type}, got {type(param_value).__name__}")
        
        # Include any extra parameters found in the input
        for param_name, param_value in tool_data.items():
            if param_name != 'relevance_score' and param_name != 'required_fields_completed' and param_name not in tool_schema['required'] and param_name not in tool_schema['optional']:
                result[tool_name]['parameters'][param_name] = param_value
                if param_name not in result[tool_name]['validation']['fields_found']:
                    result[tool_name]['validation']['fields_found'].append(param_name)
        
        # Compile error string
        if errors:
            result[tool_name]['validation']['error_string'] = "; ".join(errors)
    
    return result