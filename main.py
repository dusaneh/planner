# main.py

import json
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from typing import List, Dict, Any, Optional
import uvicorn
import copy
import asyncio
import traceback # For detailed error logging

# --- Import your helper functions ---
try:
    import helper2 as hlp
    print("Main: Helper functions loaded successfully.")
    user_context = copy.deepcopy(hlp.user_context)
    business_summary = copy.deepcopy(hlp.business_summary)
    available_tools = copy.deepcopy(hlp.available_tools)
except ImportError:
    print("Main ERROR: helper2.py not found.")
    # Dummy data/functions
    user_context = {"error": "helper missing"}
    business_summary = {"error": "helper missing"}
    available_tools = []
    async def process_quickbooks_query(*args, **kwargs): yield {"type": "thought", "data": "Dummy plan thought"}; yield {"type": "function_calls", "data": []}; yield {"type": "explanation", "data": "Dummy explanation"}
    async def simulate_retrieval_stub(*args, **kwargs): return {"function_name": "dummy_tool", "retrieved_chunks": None, "present_as_is": False, "follow_up_question": None, "asked_for_sticky": False, "rejected": False, "rejection_reason": None, "error": None}
    async def generate_final_response(*args, **kwargs): yield {"type": "thought", "data": "Dummy summary thought"}; yield {"type": "final_response_text", "data": "Dummy final response"}; yield {"type": "citation_map", "data": {}}
    hlp = None
except AttributeError as e:
    print(f"Main ERROR: Missing expected variables/functions in helper2.py: {e}")
    raise

# --- FastAPI App Setup ---
app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# --- In-memory storage ---
chat_history: List[Dict[str, str]] = []
sticky_hint_for_next_turn: Optional[str] = None

# --- Routes ---

@app.get("/", response_class=HTMLResponse)
async def get_chat_page(request: Request):
    """Serves the main chat HTML page."""
    return templates.TemplateResponse("index.html", {"request": request})

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """Handles WebSocket connections for chat."""
    await websocket.accept()
    global chat_history, sticky_hint_for_next_turn

    try:
        while True:
            raw_data = await websocket.receive_text()
            message_data = json.loads(raw_data)
            current_user_query = message_data.get("message")

            if not current_user_query:
                continue

            print(f"\n>>> Received User Query via WS: {current_user_query}")

            current_turn_history = list(chat_history)
            current_sticky_hint = sticky_hint_for_next_turn
            sticky_hint_for_next_turn = None # Reset hint for this turn

            admin_steps = {
                "understanding_thoughts": [],
                "function_calls_made": [],
                "summarization_thoughts": [],
                "error": None
            }
            plan_calls_local = None
            retrieval_results_local = []
            final_response_text_local = None
            citation_map_local = None
            explanation_local = None
            follow_up_question_asked = None
            all_thoughts_this_turn = []

            try:
                # --- Step 1: Planning/Routing ---
                print(f"--- Main: Step 1: Planning/Routing (Hint: {current_sticky_hint}) ---")
                async for item in hlp.process_quickbooks_query(
                    new_user_query=current_user_query,
                    message_history=current_turn_history,
                    user_context=user_context,
                    business_summary=business_summary,
                    available_tools=available_tools,
                    sticky_function_hint=current_sticky_hint
                ):
                    item_type = item.get("type")
                    item_data = item.get("data")

                    if item_type == "thought":
                        admin_steps["understanding_thoughts"].append(item_data)
                        all_thoughts_this_turn.append(item_data)
                        await websocket.send_json({"type": "thought", "data": item_data})
                        # --- MODIFIED: Send admin update immediately on thought ---
                        await websocket.send_json({"type": "admin_update", "data": admin_steps})
                        # ---------------------------------------------------------
                    elif item_type == "function_calls":
                        plan_calls_local = item_data
                        admin_steps["function_calls_made"] = []
                        if plan_calls_local:
                             for call in plan_calls_local:
                                 admin_steps["function_calls_made"].append({
                                     "name": call.get("name"),
                                     "query": call.get("arguments", {}).get("query") or call.get("arguments", {}).get("data_request"),
                                     "all_args": call.get("arguments", {}),
                                     "raw_result": None
                                 })
                        # Send admin update after function calls are decided
                        await websocket.send_json({"type": "admin_update", "data": admin_steps})
                    elif item_type == "explanation":
                        explanation_local = item_data
                    elif item_type == "error":
                        raise Exception(f"Planning Error: {item_data}")

                # --- Step 2: Simulate Function Execution ---
                print("\n--- Main: Step 2: Simulate Function Execution ---")
                if plan_calls_local:
                    retrieval_results_local = []
                    simulation_tasks = []
                    call_indices = {}

                    for index, call_plan in enumerate(plan_calls_local):
                        tool_name = call_plan.get("name")
                        arguments = call_plan.get("arguments", {})
                        query_arg = arguments.get("query") or arguments.get("data_request")

                        if tool_name and query_arg:
                            task = asyncio.create_task(hlp.simulate_retrieval_stub(
                                function_name=tool_name,
                                queries=[query_arg],
                                top_k=2
                            ))
                            simulation_tasks.append(task)
                            call_indices[task] = index
                        else:
                            print(f"Main Skipping simulation for invalid call structure: {call_plan}")
                            if index < len(admin_steps["function_calls_made"]):
                                admin_steps["function_calls_made"][index]["raw_result"] = {"error": "Invalid call structure, skipped simulation.", "rejected": True, "rejection_reason": "Invalid call structure"}

                    if simulation_tasks:
                        completed_tasks, _ = await asyncio.wait(simulation_tasks)
                        for task in completed_tasks:
                            original_index = call_indices[task]
                            try:
                                sim_data = task.result()
                                retrieval_results_local.append(sim_data)

                                if sim_data.get("follow_up_question"):
                                    follow_up_question_asked = sim_data["follow_up_question"]
                                    print(f"Main: Follow-up question received from {sim_data.get('function_name')}")
                                if sim_data.get("asked_for_sticky"):
                                    sticky_hint_for_next_turn = sim_data.get("function_name")
                                    print(f"Main: Sticky hint set for next turn: {sticky_hint_for_next_turn}")

                                if original_index < len(admin_steps["function_calls_made"]):
                                     admin_steps["function_calls_made"][original_index]["raw_result"] = sim_data

                            except Exception as sim_exc:
                                print(f"Main ERROR during simulation task result retrieval for call index {original_index}: {sim_exc}")
                                traceback.print_exc()
                                error_result = {"error": f"Simulation task failed: {sim_exc}", "rejected": True, "rejection_reason": "Simulation task execution error"}
                                if original_index < len(admin_steps["function_calls_made"]):
                                    admin_steps["function_calls_made"][original_index]["raw_result"] = error_result
                                retrieval_results_local.append(error_result) # Add error to results

                    # Send admin update *after* all function calls simulated
                    await websocket.send_json({"type": "admin_update", "data": admin_steps})
                else:
                    print("Main No function calls proposed.")


                # --- Step 3: Generate Final Response OR Use Follow-up Question ---
                print("\n--- Main: Step 3: Determine Final Response ---")

                if follow_up_question_asked:
                    print(f"Main: Using follow-up question as response: {follow_up_question_asked}")
                    final_response_text_local = follow_up_question_asked
                    citation_map_local = {}
                    admin_steps["summarization_thoughts"] = ["Skipped summarization - Follow-up question asked by function."]
                    await websocket.send_json({"type": "status", "data": "Asking a clarifying question..."})
                    # --- MODIFIED: Send admin update after setting follow-up status ---
                    await websocket.send_json({"type": "admin_update", "data": admin_steps})
                    # -----------------------------------------------------------------

                else:
                    history_for_summary = current_turn_history + [{"role": "user", "content": current_user_query}]
                    should_generate_response = bool(retrieval_results_local)
                    should_use_explanation = not should_generate_response and explanation_local

                    if should_generate_response or should_use_explanation:
                         await websocket.send_json({"type": "status", "data": "Generating answer..."})

                    if should_generate_response:
                        final_response_text_local = None
                        citation_map_local = None
                        async for item in hlp.generate_final_response(
                            original_user_query=current_user_query,
                            message_history=history_for_summary,
                            user_context=user_context,
                            business_summary=business_summary,
                            all_retrieval_results=retrieval_results_local
                        ):
                            item_type = item.get("type")
                            item_data = item.get("data")

                            if item_type == "thought":
                                admin_steps["summarization_thoughts"].append(item_data)
                                all_thoughts_this_turn.append(item_data)
                                await websocket.send_json({"type": "thought", "data": item_data})
                                # --- MODIFIED: Send admin update immediately on thought ---
                                await websocket.send_json({"type": "admin_update", "data": admin_steps})
                                # ---------------------------------------------------------
                            elif item_type == "final_response_text":
                                final_response_text_local = item_data
                            elif item_type == "citation_map":
                                citation_map_local = item_data
                            elif item_type == "error":
                                 raise Exception(f"Summarization/Citation Error: {item_data}")

                        if not final_response_text_local:
                             final_response_text_local = "I found information but encountered an issue summarizing it."
                             admin_steps["error"] = "Summarization completed but no final_response_text key found."
                        if citation_map_local is None:
                             citation_map_local = {}

                    elif should_use_explanation:
                        print("Main Using planner explanation as final response.")
                        final_response_text_local = explanation_local
                        citation_map_local = {}
                        admin_steps["summarization_thoughts"] = ["No summarization needed - used planner explanation."]
                        # --- MODIFIED: Send admin update after setting explanation status ---
                        await websocket.send_json({"type": "admin_update", "data": admin_steps})
                        # --------------------------------------------------------------------
                    else: # Fallback
                        print("Main No retrieval results or planner explanation.")
                        final_response_text_local = "I wasn't able to retrieve or generate a specific answer for that."
                        citation_map_local = {}
                        admin_steps["error"] = "Could not generate response from planning or retrieval."
                        # --- MODIFIED: Send admin update after setting fallback status ---
                        await websocket.send_json({"type": "admin_update", "data": admin_steps})
                        # -----------------------------------------------------------------

                # --- Send Final Response Package ---
                # This happens after all thoughts/status updates for the turn
                await websocket.send_json({
                    "type": "final_response",
                    "data": {
                        "ai_message": final_response_text_local,
                        "citations": citation_map_local or {},
                        "thinking_process": all_thoughts_this_turn
                    }
                })
                # Send final admin state just to be sure (might be redundant if thoughts were sent)
                await websocket.send_json({"type": "admin_update", "data": admin_steps})


            except Exception as e:
                print(f"!!! Main ERROR during processing turn: {e}")
                traceback.print_exc()
                error_msg = f"An error occurred: {e}"
                admin_steps["error"] = error_msg
                await websocket.send_json({"type": "error", "data": error_msg})
                await websocket.send_json({"type": "admin_update", "data": admin_steps})
                final_response_text_local = f"Sorry, an internal error occurred."


            # --- Step 4: Update Global History ---
            chat_history.append({"role": "user", "content": current_user_query})
            if final_response_text_local:
                chat_history.append({"role": "assistant", "content": final_response_text_local})
            print(f"Main History updated. Length: {len(chat_history)}")
            print(f"Main Sticky hint for next turn is now: {sticky_hint_for_next_turn}")


    except WebSocketDisconnect:
        print("Main Client disconnected")
        sticky_hint_for_next_turn = None
    except Exception as e:
        print(f"Main WebSocket Error: {e}")
        traceback.print_exc()
        sticky_hint_for_next_turn = None
        try:
            await websocket.send_json({"type": "error", "data": f"WebSocket error: {e}"})
        except:
            pass
        await websocket.close()


# --- Run the app ---
if __name__ == "__main__":
    print("Starting FastAPI server with WebSocket support...")
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)