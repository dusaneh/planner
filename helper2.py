# helper2.py

import google.generativeai as genai
import json
import os
import re
from typing import List, Dict, Any, Tuple, Optional, Union, AsyncGenerator
import copy
import asyncio

# --- Configuration ---
# ... (Same as before) ...
try:
    # Assuming keys.py exists and has google_api_key defined
    import keys
    google_api_key = keys.google_api_key
    genai.configure(api_key=google_api_key)
    print("Helper: Google API Key configured successfully.")
except ImportError:
    print("Helper Warning: 'keys.py' not found. Attempting manual configuration.")
    google_api_key = "YOUR_GOOGLE_API_KEY" # <--- PASTE YOUR KEY HERE IF keys.py IS NOT USED
    if google_api_key == "YOUR_GOOGLE_API_KEY":
        print("Helper ERROR: You must provide your Google API Key.")
        raise ValueError("Google API Key not configured.")
    else:
        genai.configure(api_key=google_api_key)
        print("Helper: Google API Key configured manually.")
except AttributeError:
    print("Helper Warning: 'google_api_key' not found in 'keys.py'. Attempting manual configuration.")
    google_api_key = "YOUR_GOOGLE_API_KEY" # <--- PASTE YOUR KEY HERE IF keys.py IS NOT USED
    if google_api_key == "YOUR_GOOGLE_API_KEY":
        print("Helper ERROR: You must provide your Google API Key.")
        raise ValueError("Google API Key not configured.")
    else:
        genai.configure(api_key=google_api_key)
        print("Helper: Google API Key configured manually.")
except Exception as e:
     print(f"Helper Warning: API Key configuration might be missing or invalid: {e}")
     pass


# --- Example Data Setup ---
# ... (user_context, business_summary, available_tools remain the same) ...
user_context = {
    "current_page": "/app/vendordetail?nameid=123", # Example page
    "recent_actions": ["viewed vendor 'Acme Supplies'", "navigated to Vendor Center"],
    "likely_problem": "User needs help managing vendor credits or sales tax.",
    "quickbooks_version": "QuickBooks Online Plus"
}
business_summary = {
    "business_name": "Rosie's Riveting Repairs",
    "business_type": "LLC",
    "industry": "Home Services / Handyman",
    "location": "Oakland, CA",
    "number_of_employees": 3,
    "years_in_business": 5,
    "primary_services": ["Plumbing", "Electrical", "General Home Repair"],
    "accounting_method": "Accrual",
    "qb_features_used": ["Invoicing", "Expense Tracking", "Vendor Management", "Basic Reporting", "Sales Tax"]
}
available_tools = [
    {
        "name": "payroll_qna_retrieval",
        "description": "Answers questions about payroll processing, tax forms (W2, 1099), employee setup, deductions, and payroll regulations. Cannot answer about contributions.",
        "parameters": [
            {"name": "query", "type": "string", "description": "The specific payroll-related question (excluding contributions).", "required": True},
            {"name": "employee_id", "type": "string", "description": "Optional employee identifier if the question relates to a specific employee.", "required": False},
            {"name": "tax_form", "type": "string", "description": "Specify tax form (e.g., 'W2', '1099-NEC') if relevant.", "required": False}
        ]
    },
    {
        "name": "general_product_support_retrieval",
        "description": "Provides answers to general 'how-to' questions about using QuickBooks features like invoicing, expenses, banking, reporting, chart of accounts, vendor/customer management, and product setup/navigation.",
        "parameters": [
            {"name": "query", "type": "string", "description": "The specific how-to question about QuickBooks functionality.", "required": True},
            {"name": "feature_area", "type": "string", "description": "The primary QuickBooks feature area (e.g., 'Invoicing', 'Expenses', 'Vendors', 'Reports').", "required": False},
             {"name": "quickbooks_version", "type": "string", "description": "The user's QuickBooks version (e.g., 'Online Plus', 'Desktop Pro').", "required": False}
        ]
    },
    {
        "name": "legal_compliance_retrieval",
        "description": "Handles questions that appear to relate to illegal activities or circumventing regulations. Also addresses any questions about credit worthiness or why somebody was rejected for an application.", # MODIFIED Description
        "parameters": [
            {"name": "query", "type": "string", "description": "The user's question.", "required": True},
             # Removed other params as they are not used now
        ]
    },
    {
        "name": "user_data_query",
        "description": "Retrieves specific data points directly from the user's QuickBooks account, such as account balances, customer counts, vendor details, transaction summaries.",
        "parameters": [
            {"name": "data_request", "type": "string", "description": "A clear description of the specific data needed (e.g., 'total balance of all bank accounts', 'number of active customers', 'balance for vendor Acme Supplies').", "required": True},
            {"name": "time_period", "type": "string", "description": "Optional time frame for the data (e.g., 'this month', 'last quarter', 'year-to-date').", "required": False},
            {"name": "filter_criteria", "type": "string", "description": "Optional filters (e.g., 'customer_status=active', 'account_type=bank').", "required": False}
        ]
    }
]


# --- Core LLM Interaction Function (Async Yielding - NO CHANGE) ---
async def _execute_llm_json_lines(
    prompt: str,
    expected_keys: List[str],
    model_name: str = 'gemini-1.5-flash-001',
    temperature: float = 0.2
) -> AsyncGenerator[Dict[str, Any], None]:
    """
    Core async generator executing Gemini call, parsing and yielding JSON Lines.
    (Implementation remains the same)
    """
    # ... (Implementation is identical to the previous correct version) ...
    print(f"\n--- Helper: Executing LLM Call (Expecting: {', '.join(expected_keys)}) ---") # Verbose
    model = genai.GenerativeModel(model_name)
    buffer = "" # Buffer for incomplete lines
    found_non_thought_keys = {key: False for key in expected_keys if key != 'thought'}
    line_counter = 0 # For error reporting

    try:
        response = await model.generate_content_async(
            prompt,
            stream=True,
            generation_config=genai.types.GenerationConfig(temperature=temperature)
        )

        async for chunk in response:
            if not chunk.parts:
                 continue

            buffer += chunk.text
            while '\n' in buffer:
                line, buffer = buffer.split('\n', 1)
                line = line.strip()
                line_counter += 1

                if not line or line == '```json' or line == '```':
                    continue

                try:
                    if (line.startswith('{') and line.endswith('}')) or \
                       (line.startswith('[') and line.endswith(']')):
                        parsed_json = json.loads(line)
                        found_key_in_line = False
                        for key in expected_keys:
                            if key in parsed_json:
                                found_key_in_line = True
                                if key == 'thought' and isinstance(parsed_json[key], str):
                                    yield {"type": "thought", "data": parsed_json[key]}
                                elif key != 'thought' and not found_non_thought_keys[key]:
                                    # Yield the specific key and its data
                                    yield {"type": key, "data": parsed_json[key]}
                                    found_non_thought_keys[key] = True
                                break
                except json.JSONDecodeError:
                    print(f"\nHelper WARNING: JSONDecodeError on presumed complete line {line_counter}. Content: {line}")
                except Exception as e:
                    print(f"\nHelper ERROR processing Line {line_counter}: {e}")
                    print(f"Helper Problematic line content: {line}")
                    yield {"type": "error", "data": f"Unexpected processing error on line {line_counter}: {e}"}

        # Process any remaining data in the buffer
        if buffer.strip():
            line = buffer.strip()
            line_counter +=1
            if line == '```json' or line == '```':
                 pass
            else:
                try:
                    if (line.startswith('{') and line.endswith('}')) or \
                       (line.startswith('[') and line.endswith(']')):
                        parsed_json = json.loads(line)
                        found_key_in_line = False
                        for key in expected_keys:
                             if key in parsed_json:
                                found_key_in_line = True
                                if key == 'thought' and isinstance(parsed_json[key], str):
                                    yield {"type": "thought", "data": parsed_json[key]}
                                elif key != 'thought' and not found_non_thought_keys[key]:
                                    yield {"type": key, "data": parsed_json[key]}
                                    found_non_thought_keys[key] = True
                                break
                except json.JSONDecodeError:
                     print(f"\nHelper WARNING: JSONDecodeError on final buffer content. Content: {line}")
                except Exception as e:
                    print(f"\nHelper ERROR processing final buffer: {e}")
                    print(f"Helper Problematic final buffer content: {line}")
                    yield {"type": "error", "data": f"Unexpected processing error on final buffer: {e}"}

    except Exception as e:
        print(f"\n--- Helper ERROR during API call ---")
        print(e)
        yield {"type": "error", "data": f"API call failed - {e}"}
        return


# --- Planning/Routing Function (NO CHANGE from previous) ---
async def process_quickbooks_query(
    new_user_query: str,
    message_history: List[Dict[str, str]],
    user_context: Dict[str, Any],
    business_summary: Dict[str, Any],
    available_tools: List[Dict[str, Any]],
    sticky_function_hint: Optional[str] = None,
    model_name: str = 'gemini-1.5-flash-001',
    temperature: float = 0.2
) -> AsyncGenerator[Dict[str, Any], None]:
    """
    Async generator processing a user query for routing. Includes sticky function hint.
    (Implementation remains the same as previous correct version)
    """
    # ... (Implementation is identical to the previous correct version) ...
    history_for_prompt = message_history + [{"role": "user", "content": new_user_query}]
    history_str = json.dumps(history_for_prompt, indent=2)
    context_str = json.dumps(user_context, indent=2)
    business_str = json.dumps(business_summary, indent=2)
    tools_str = json.dumps(available_tools, indent=2)

    hint_text = ""
    if sticky_function_hint:
        hint_text = f"\nHint: The previous turn involved a follow-up question from the function: '{sticky_function_hint}'. Consider routing back to this function if the user's current query seems to answer that question or is directly related, unless the query is clearly about a different topic."

    system_prompt = f"""You are an AI assistant for QuickBooks. Your task is to analyze the user's query, chat history, user context, and business summary to determine the best way to route the query using the available tools.
{hint_text}

Follow these steps precisely:

1.  **Chain of Thought (CoT):** First, perform a chain of thought analysis. Output this reasoning process as 2-4 separate JSON Lines payloads. Each payload must be a valid JSON object containing a single key "thought" with the reasoning step as its string value. Consider the hint if provided.

2.  **Function Call Selection:** After the CoT JSON Lines, output a *single* JSON Line payload. This payload must be a valid JSON object containing a single key "function_calls". The value of "function_calls" must be a *list* of JSON objects, each containing "name" and "arguments". If no function call is needed, output an empty list: {{"function_calls": []}}.

3.  **Final Explanation:** If and only if *no* function calls are selected (i.e., "function_calls" is an empty list), output one *last* JSON Line payload containing a single key "explanation". The value should be a brief string explaining *why* no tool was needed and potentially providing a direct answer if possible. Do *not* output an "explanation" if function calls are made.

**Available Tools:**
{tools_str}

User's Last Query:
"{new_user_query}"

Chat History:
{history_str}

User Context:
{context_str}

Business Summary:
{business_str}

Output Format Reminder:
Your entire output must be a sequence of valid JSON Lines. Start with the 'thought' lines, then the 'function_calls' line. Only include the 'explanation' line if 'function_calls' was empty. Do not include any text outside of these JSON Line payloads. No markdown formatting.
"""
    expected_keys = ['thought', 'function_calls', 'explanation']
    try:
        async for item in _execute_llm_json_lines(
            prompt=system_prompt,
            expected_keys=expected_keys,
            model_name=model_name,
            temperature=temperature
        ):
            yield item
    except Exception as e:
        print(f"Helper ERROR in process_quickbooks_query calling core LLM: {e}")
        yield {"type": "error", "data": f"Core LLM error during planning: {e}"}


# --- LLM Simulation Stub Function (MODIFIED for Legal Logic) ---
async def simulate_retrieval_stub(
    function_name: str,
    queries: List[str], # Expecting a list with one query from main.py
    top_k: int = 3,
    model_name: str = 'gemini-1.5-flash-001'
) -> Dict[str, Any]:
    """
    ASYNC function simulating retrieval.
    Handles legal standard response, payroll contribution logic, rejection, and sticky flag.
    Returns a dict with: function_name, retrieved_chunks, present_as_is,
                         follow_up_question, asked_for_sticky, rejected, rejection_reason, error
    """
    print(f"\n--- Helper: Simulating Retrieval for Tool: '{function_name}' (Async w/ Flags) ---")
    query = queries[0] if queries else "" # Get the single query

    # Default return values
    result = {
        "function_name": function_name,
        "retrieved_chunks": None, # Will be populated if successful
        "present_as_is": False, # Default to False, override below if needed
        "follow_up_question": None,
        "asked_for_sticky": False,
        "rejected": False,
        "rejection_reason": None,
        "error": None
    }

    # --- MODIFIED: Legal Specific Logic (Standard Response) ---
    if function_name == "legal_compliance_retrieval":
        print(f"Helper Stub: Handling legal query with standard response: '{query}'")
        standard_legal_warning = "I cannot process requests related to potentially illegal activities or provide guidance on circumventing laws or regulations. Also, I cannot address any questions about credit worthiness or why somebody was rejected for an application. Please ensure your questions comply with legal and ethical standards."
        result["retrieved_chunks"] = [
            {
                "chunk_content": standard_legal_warning,
                "source_article": "System Policy",
                "source_link": "#policy-illegal-activities" # Example placeholder link
            }
        ]
        result["present_as_is"] = True # CRITICAL: Ensure this is presented directly
        result["rejected"] = False   
        result["rejection_reason"] = "Query potentially relates to illegal activities or advice."
        return result # Return immediately with the standard response

    # --- Payroll Specific Logic (Contributions) ---
    if function_name == "payroll_qna_retrieval":
        has_contribution = "contribution" in query.lower()
        if has_contribution:
            print(f"Helper Stub: Payroll query is about contribution: '{query}'. Asking follow-up.")
            result["follow_up_question"] = "I see you want to know about payroll, but I can't answer questions about contributions. Did you want to know about W2s?"
            result["asked_for_sticky"] = True
            return result # Return immediately

    # --- General Support Rejection Logic ---
    if function_name == "general_product_support_retrieval":
        # Reject if query is clearly about payroll or legal (including contributions)
        if re.search(r'\b(payroll|tax advice|legal|w2|1099|contribution)\b', query, re.IGNORECASE):
            print(f"Helper Stub: Rejecting general support query about payroll/legal: '{query}'")
            result["rejected"] = True
            result["rejection_reason"] = "This question seems related to payroll or legal matters. Please try asking the specific payroll or legal tool."
            return result

    # --- Proceed with Normal Simulation (Only if not handled above) ---
    print(f"Helper Stub: Proceeding with normal simulation for '{function_name}'")
    all_generated_chunks = {}
    try:
        model = genai.GenerativeModel(model_name)
    except Exception as e:
        print(f"Helper ERROR initializing simulation model '{model_name}': {e}")
        result["error"] = f"Model init failed: {e}"
        result["rejected"] = True # Mark as rejected due to error
        result["rejection_reason"] = "Internal error during tool initialization."
        return result

    simulation_prompt = f"""
    You are simulating a QuickBooks knowledge base retrieval system.
    For the following QuickBooks-related user query, generate {top_k} plausible-sounding, relevant content chunks, source article titles, and source URLs.
    The content should seem like it came from QuickBooks help articles but does not need to be factually correct. Make the URLs look realistic (e.g., https://quickbooks.intuit.com/learn-support/...). Make the content distinct for each chunk.

    User Query: "{query}"

    Respond ONLY with a valid JSON object containing a single key "simulated_results".
    The value of "simulated_results" must be a list of JSON objects, where each object has the following keys:
    - "chunk_content": A short paragraph (2-4 sentences) simulating the relevant help content.
    - "source_article": A plausible title for the source help article.
    - "source_link": A plausible, unique URL for the source article.

    JSON response:
    """
    try:
        response = await model.generate_content_async(
            simulation_prompt,
            generation_config=genai.types.GenerationConfig(temperature=0.6)
        )
        raw_llm_output = response.text
        json_match = re.search(r'```json\s*({.*?})\s*```', raw_llm_output, re.DOTALL | re.IGNORECASE)
        if not json_match:
             json_match = re.search(r'({.*?})', raw_llm_output, re.DOTALL)

        if json_match:
            json_text = json_match.group(1)
            parsed_llm_output = json.loads(json_text)
            if "simulated_results" in parsed_llm_output and isinstance(parsed_llm_output["simulated_results"], list):
                simulated_chunks_for_query = parsed_llm_output["simulated_results"]
                for chunk in simulated_chunks_for_query:
                    if all(k in chunk for k in ("chunk_content", "source_article", "source_link")):
                        link = chunk["source_link"]
                        if link not in all_generated_chunks:
                            all_generated_chunks[link] = chunk
        # else:
        #     print(f"  Helper Stub Warning: Could not extract JSON for query '{query}'. Output: {raw_llm_output[:200]}...")

    except json.JSONDecodeError as e:
        print(f"  Helper Stub Error: Failed to parse JSON from LLM simulation response: {e}")
        result["error"] = f"JSON parsing failed: {e}"
        result["rejected"] = True # Mark as rejected due to error
        result["rejection_reason"] = "Internal error processing tool results."
    except Exception as e:
        print(f"  Helper Stub Error during async LLM simulation call or processing for query '{query}': {e}")
        result["error"] = f"LLM call failed: {e}"
        result["rejected"] = True # Mark as rejected due to error
        result["rejection_reason"] = "Internal error during tool execution."

    # Add retrieved chunks if successful and not already rejected
    retrieved_chunks = list(all_generated_chunks.values())
    if retrieved_chunks and not result["rejected"]:
         result["retrieved_chunks"] = retrieved_chunks
         # Determine present_as_is based on function name (already done for legal)
         result["present_as_is"] = bool(re.search(r'compliance', function_name, re.IGNORECASE)) # Example: only legal/compliance is as-is by default
    elif not result["error"] and not result["rejected"]: # No chunks but no specific error reported
        print(f"  Helper Stub Warning: No chunks generated for query '{query}' but no error reported.")
        # Optionally mark as rejected if no content found is considered a rejection
        result["rejected"] = True
        result["rejection_reason"] = "Could not find relevant information for this query."

    return result


# --- Final Response Generation Function (MODIFIED to handle present_as_is from rejected) ---
async def generate_final_response(
    original_user_query: str,
    message_history: List[Dict[str, str]],
    user_context: Dict[str, Any],
    business_summary: Dict[str, Any],
    all_retrieval_results: List[Dict[str, Any]], # Contains full stub result dicts
    model_name: str = 'gemini-1.5-flash-001',
    temperature: float = 0.3
) -> AsyncGenerator[Dict[str, Any], None]:
    """
    Async generator for final response synthesis with citations.
    Handles rejected results and ensures 'present_as_is' chunks from rejected tools are handled.
    Yields dicts for 'thought', 'final_response_text', 'citation_map', or 'error'.
    """
    print(f"\n--- Helper: Generating Final Response w/ Citations & Rejection Handling ---")

    # 1. Process Retrieval Results for Citation, Rejection, and Present As Is
    processed_chunks_for_citation = []
    successful_results_chunks = [] # Chunks from non-rejected results
    rejected_results = []
    present_as_is_from_rejected = [] # Store chunks marked 'as_is' from REJECTED results (e.g., legal warning)
    citation_id_counter = 1
    source_details_for_prompt = [] # For the LLM prompt (only for successful chunks)

    for result in all_retrieval_results:
        is_rejected = result.get("rejected", False)
        chunks = result.get("retrieved_chunks") # Can be None or list
        present_as_is = result.get("present_as_is", False)

        if is_rejected:
            rejected_results.append(result)
            # --- ADDED: Check for present_as_is chunks even in rejected results ---
            if present_as_is and chunks:
                for chunk in chunks:
                    content = chunk.get("chunk_content", "")
                    if content:
                        present_as_is_from_rejected.append(content)
            # --------------------------------------------------------------------
        elif chunks: # Has chunks and is not rejected
            # Process successful chunks for potential citation/summarization
            successful_results_chunks.extend(chunks) # Add all chunks from this successful result
            for chunk in chunks:
                content = chunk.get("chunk_content", "")
                article = chunk.get("source_article", "Unknown Source")
                link = chunk.get("source_link", "#")

                if content and link:
                    chunk_id = citation_id_counter
                    processed_chunks_for_citation.append({
                        "id": chunk_id,
                        "content": content,
                        "title": article,
                        "link": link,
                        "present_as_is": present_as_is # Use flag from successful result
                    })
                    source_details_for_prompt.append(f"[{chunk_id}] Title: {article} | URL: {link}")
                    citation_id_counter += 1

    # --- Handle cases based on results ---
    if not successful_results_chunks and rejected_results:
        # ALL results were rejected OR had errors preventing chunk retrieval
        print("Helper: All function calls resulted in rejection or error.")
        yield {"type": "thought", "data": "All tools rejected the request or could not provide data."}

        # Combine standard rejection messages and specific reasons
        final_rejection_message = ""
        if present_as_is_from_rejected:
            # If we have a standard warning (like legal), use that primarily
            final_rejection_message = "\n".join(present_as_is_from_rejected)
        else:
            # Otherwise, summarize rejection reasons
            reasons = [r.get('rejection_reason', 'No specific reason provided.') for r in rejected_results if r.get('rejection_reason')]
            if reasons:
                rejection_summary = "I couldn't process your request fully because: " + " ".join(reasons)
            else:
                rejection_summary = "I was unable to process your request with the available tools."
            final_rejection_message = rejection_summary

        yield {"type": "final_response_text", "data": final_rejection_message}
        yield {"type": "citation_map", "data": {}} # No citations for rejected-only path
        return

    if not successful_results_chunks and not rejected_results:
         # No successful results, no rejections (e.g., planning failed before execution)
        print("Helper Warning: No successful or rejected results found for summarization.")
        yield {"type": "thought", "data": "No usable information retrieved from functions."}
        yield {"type": "final_response_text", "data": "I couldn't find specific information to answer your question based on the search results."}
        yield {"type": "citation_map", "data": {}}
        return

    # --- Proceed with summarization using successful results ---
    # Prepare chunks based on 'present_as_is' flag ONLY from successful results
    present_as_is_chunks_prompt = "\n".join([f"[{c['id']}] {c['content']}" for c in processed_chunks_for_citation if c['present_as_is']]) or "None"
    summarizable_chunks_prompt = "\n".join([f"[{c['id']}] {c['content']}" for c in processed_chunks_for_citation if not c['present_as_is']]) or "None"
    all_sources_prompt = "\n".join(source_details_for_prompt)

    # Prepare rejection info (mentioning reasons from rejected tools)
    rejected_info_prompt = ""
    if rejected_results:
         rejected_reasons = [f"- {r.get('function_name')}: {r.get('rejection_reason', 'Rejected')}" for r in rejected_results]
         rejected_info_prompt = "\nNote: Some parts of the query could not be processed:\n" + "\n".join(rejected_reasons) # Simplified message

    # Prepend any standard 'present_as_is' warnings from rejected tools
    standard_warnings_prompt = ""
    if present_as_is_from_rejected:
        standard_warnings_prompt = "\n".join(present_as_is_from_rejected) + "\n\n" # Add spacing


    # 2. Construct Prompt
    history_str = json.dumps(message_history, indent=2)
    context_str = json.dumps(user_context, indent=2)
    business_str = json.dumps(business_summary, indent=2)

    system_prompt = f"""You are an AI assistant for QuickBooks. Your task is to synthesize a helpful and concise final response. Start with any standard warnings provided. Then, incorporate information from the successful sources, citing them accurately using bracketed numerical IDs `[id]`. Also consider mentioning limitations based on rejected parts of the query.

Follow these steps precisely:

1.  **Standard Warnings First:** Check the 'Standard Warnings' section below. If it contains text, begin your final response *exactly* with that text, followed by two newlines.
2.  **Chain of Thought (CoT):** Perform a chain of thought analysis (output as JSON Lines with key "thought"). Consider:
    *   User's query: "{original_user_query}" and history: {history_str}.
    *   Standard Warnings (already handled in step 1).
    *   'Content to Present Verbatim' (from successful sources): Plan inclusion with citation `[id]`.
    *   'Content to Summarize' (from successful sources): Plan synthesis, citing *all* used info with `[id]`. Use `[1][2]` if needed.
    *   'Rejected Query Parts': Decide if/how to briefly mention this limitation *after* presenting the successful information.
    *   Drafting the core message (after any standard warning), ensuring correct citations for successful content.
    *   Refining the final response for clarity, conciseness, tone.

3.  **Cited Response Generation:** After CoT, output a *single* JSON Line (key "final_response_text"). The value is the complete response string: Standard Warnings (if any) + Synthesized/Cited Answer + Optional Rejection Note. Include bracketed citations `[id]` for successful content.

4.  **Citation Map Generation:** Immediately after "final_response_text", output *one more* JSON Line (key "citation_map"). Value is a JSON object mapping string IDs used in the text (only from successful sources) to their {{"title": ..., "link": ...}}. Example: {{ "1": {{ "title": "A", "link": "..." }}, "3": {{ "title": "B", "link": "..." }} }}

**Context:**
*   User's Original Query: "{original_user_query}"
*   Conversation History: {history_str}.
*   User Context: {context_str}.
*   Business Summary: {business_str}.

**Standard Warnings (Start response with this text if present):**
{standard_warnings_prompt}

**Retrieved Information Sources (Cite using the bracketed ID - ONLY for successful content below):**
{all_sources_prompt}

**Content to Present Verbatim (From SUCCESSFUL sources - Include citation ID):**
{present_as_is_chunks_prompt}

**Content to Summarize (From SUCCESSFUL sources - Include citation ID):**
{summarizable_chunks_prompt}

**Rejected Query Parts (For context, mention briefly if needed AFTER main answer):**
{rejected_info_prompt}

Output Format Reminder:
Sequence of JSON Lines: 'thought' lines, then 'final_response_text', then 'citation_map'. No markdown formatting outside JSON Lines. Ensure all cited IDs exist in the citation map and correspond to successful sources.
"""

    # 3. Define expected keys
    expected_keys = ['thought', 'final_response_text', 'citation_map']

    # 4. Call the core LLM async generator
    try:
        async for item in _execute_llm_json_lines(
            prompt=system_prompt,
            expected_keys=expected_keys,
            model_name=model_name,
            temperature=temperature
        ):
            yield item
    except Exception as e:
        print(f"Helper ERROR in generate_final_response calling core LLM: {e}")
        yield {"type": "error", "data": f"Core LLM error during citation/rejection response generation: {e}"}

    print("\n--- Helper: Finished Generating Final Response w/ Citations & Rejection Handling ---")