import os
import json
import duckdb
import chromadb
from chromadb.utils import embedding_functions
from dotenv import load_dotenv

from typing import TypedDict, Annotated, Sequence
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langchain_core.tools import tool
from langchain_groq import ChatGroq
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode

load_dotenv()

# --- 1. Define Agent Tools ---

@tool
def query_latest_telemetry() -> str:
    """Queries the industrial historian in DuckDB for the latest telemetry reading and any active error codes."""
    con = duckdb.connect("plant_data.duckdb", read_only=True)
    res = con.execute("""
        SELECT recorded_at, machine_id, temp_c, speed_cpm, error_code 
        FROM raw_telemetry 
        ORDER BY recorded_at DESC 
        LIMIT 1
    """).fetchone()
    con.close()
    
    if not res:
        return "No telemetry records found."
    return json.dumps({
        "timestamp": str(res[0]),
        "machine_id": res[1],
        "temperature_c": res[2],
        "speed_cpm": res[3],
        "error_code": res[4]
    })

@tool
def query_maintenance_history(error_code: int) -> str:
    """Queries CMMS records in DuckDB for historical resolutions associated with a specific error code."""
    con = duckdb.connect("plant_data.duckdb", read_only=True)
    res = con.execute("""
        SELECT failure_mode, root_cause, resolution 
        FROM cmms_history 
        WHERE error_code = ?
    """, [error_code]).fetchone()
    con.close()
    
    if not res:
        return f"No prior maintenance history found for Error Code {error_code}."
    return json.dumps({
        "error_code": error_code,
        "failure_mode": res[0],
        "historical_root_cause": res[1],
        "standard_resolution": res[2]
    })

@tool
def search_sop_guidelines(query: str) -> str:
    """Searches the ChromaDB SOP knowledge base for relevant standard operating procedures and compliance rules."""
    client = chromadb.PersistentClient(path="chroma_db")
    col = client.get_collection(
        name="pharma_sops", 
        embedding_function=embedding_functions.DefaultEmbeddingFunction()
    )
    results = col.query(query_texts=[query], n_results=1)
    if not results["documents"] or not results["documents"][0]:
        return "No relevant SOP found."
    return json.dumps({
        "sop_id": results["ids"][0][0],
        "content": results["documents"][0][0]
    })

tools = [query_latest_telemetry, query_maintenance_history, search_sop_guidelines]
tool_node = ToolNode(tools)

# --- 2. State Definition with 'add_messages' Reducer ---

class AgentState(TypedDict):
    # add_messages ensures tool outputs and responses append rather than overwrite
    messages: Annotated[Sequence[BaseMessage], add_messages]

SYSTEM_PROMPT = """You are AsepticOps-Copilot, an expert AI diagnostics agent for pharmaceutical manufacturing.
Your role is to investigate active line anomalies by:
1. Inspecting the latest telemetry to identify temperature excursions, speed drops, and error codes.
2. Checking CMMS maintenance history for the identified error code.
3. Searching the SOP knowledge base for standard operating procedures.
4. Synthesizing a structured root-cause summary and drafting an auditable GxP Deviation Report.

Structure your final deviation report clearly:
- Anomaly Summary (Machine ID, Metric Excursion, Active Error Code)
- Probable Root Cause (Corroborated by CMMS history)
- Mandatory SOP Corrective Actions
- Status: PENDING SUPERVISOR REVIEW
"""

from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage

# Switch to Qwen 27B for robust tool-calling compliance
llm = ChatGroq(
    model_name="qwen/qwen3.8-27b",
    temperature=0
).bind_tools(tools)

# Ensure your call_model node injects a strict system message:
SYSTEM_PROMPT = SystemMessage(
    content="You are a GxP-compliant Diagnostic AI for pharmaceutical packaging lines. "
            "When given an error, query the DuckDB historian and ChromaDB SOP database using your tools. "
            "Do not output conversational filler. Execute tool calls directly."
)

def call_model(state):
    messages = state["messages"]
    if not any(isinstance(m, SystemMessage) for m in messages):
        messages = [SYSTEM_PROMPT] + messages
    response = llm.invoke(messages)
    return {"messages": [response]}

    from langgraph.graph import StateGraph, END
from langchain_core.messages import SystemMessage

# 1. System Prompt & Model Setup
SYSTEM_PROMPT = SystemMessage(
    content="You are a GxP-compliant Diagnostic AI for pharmaceutical packaging lines. "
            "When given an error, query the DuckDB historian and ChromaDB SOP database using your tools. "
            "Do not output conversational filler. Execute tool calls directly."
)

def call_model(state):
    messages = state["messages"]
    if not any(isinstance(m, SystemMessage) for m in messages):
        messages = [SYSTEM_PROMPT] + messages
    response = llm.invoke(messages)
    return {"messages": [response]}

# 2. Define the Conditional Edge Router (MUST be defined before adding to workflow)
def should_continue(state):
    messages = state["messages"]
    last_message = messages[-1]
    # If the LLM returned tool calls, branch to the tools node
    if hasattr(last_message, "tool_calls") and len(last_message.tool_calls) > 0:
        return "tools"
    # Otherwise, stop reasoning and return the final response
    return END

# 3. Assemble and Compile Workflow
workflow = StateGraph(AgentState)

workflow.add_node("agent", call_model)
workflow.add_node("tools", tool_node)

workflow.set_entry_point("agent")

# Wire conditional routing
workflow.add_conditional_edges(
    "agent",
    should_continue,
    {
        "tools": "tools",
        END: END
    }
)

workflow.add_edge("tools", "agent")

app = workflow.compile()

# Build LangGraph workflow
workflow = StateGraph(AgentState)
workflow.add_node("agent", call_model)
workflow.add_node("tools", tool_node)

workflow.set_entry_point("agent")
workflow.add_conditional_edges("agent", should_continue, {"tools": "tools", END: END})
workflow.add_edge("tools", "agent")

app = workflow.compile()

# --- 3. Execution Pipeline ---

def run_diagnostics():
    print("\n--- Initializing Autonomous Line Diagnostics (Gemini) ---")
    initial_input = {
        "messages": [
            HumanMessage(content="The packaging line triggered an alarm. Investigate the current telemetry, check maintenance history, find the matching SOP, and draft a deviation report.")
        ]
    }
    
    for event in app.stream(initial_input, stream_mode="values"):
        last_msg = event["messages"][-1]
        if last_msg.type == "ai" and getattr(last_msg, "tool_calls", None):
            for call in last_msg.tool_calls:
                print(f"[Agent Tool Invocation] -> {call['name']}({call['args']})")
        elif last_msg.type == "ai" and not getattr(last_msg, "tool_calls", None):
            print("\n================ FINAL AGENT DIAGNOSTIC REPORT ================\n")
            print(last_msg.content)
            print("\n===============================================================\n")

if __name__ == "__main__":
    run_diagnostics()