import os
import json
import sqlite3
from dotenv import load_dotenv

from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage, ToolMessage
from langchain_core.tools import tool

load_dotenv()

DB_PATH = "plant_data.db"
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

def get_connection():
    conn = sqlite3.connect(DB_PATH, timeout=15.0)
    conn.execute("PRAGMA journal_mode=WAL;")
    return conn

@tool
def fetch_cmms_records(alarm_code: int) -> str:
    """Retrieves CMMS equipment failure history and standard SOP recommendations."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT subsystem, historical_root_cause, recommended_action 
            FROM cmms_history 
            WHERE alarm_code = ?
        """, (alarm_code,))
        row = cursor.fetchone()

    if row:
        return json.dumps({
            "subsystem": row[0],
            "historical_root_cause": row[1],
            "recommended_action": row[2]
        })
    return json.dumps({
        "subsystem": "Packaging Line",
        "historical_root_cause": "Unclassified stoppage.",
        "recommended_action": "Execute line clearance."
    })

@tool
def fetch_pre_incident_telemetry(line_id: str, limit: int = 5) -> str:
    """Retrieves the last N seconds of telemetry before the downtime alarm."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT recorded_at, vial_counter, line_speed_vpm, changeover_active, changeover_duration_min, alarm_code
            FROM packaging_telemetry
            WHERE line_id = ?
            ORDER BY recorded_at DESC
            LIMIT ?
        """, (line_id, limit))
        rows = cursor.fetchall()

    telemetry = []
    for r in rows:
        telemetry.append({
            "timestamp": r[0],
            "vials_packed": r[1],
            "speed_vpm": r[2],
            "changeover_active": bool(r[3]),
            "changeover_min": r[4],
            "alarm_code": r[5]
        })
    return json.dumps(telemetry)

tools = [fetch_cmms_records, fetch_pre_incident_telemetry]
tools_by_name = {t.name: t for t in tools}

def get_llm():
    if not GROQ_API_KEY:
        return None
    return ChatGroq(
        model_name="qwen/qwen3.8-27b",
        temperature=0
    ).bind_tools(tools)

def run_diagnostic_agent(incident: dict) -> dict:
    alarm_code = incident["alarm_code"]
    line_id = incident["line_id"]
    reason = incident["qualification_reason"]
    vials = incident["vial_count_snapshot"]
    inc_id = incident["incident_id"]

    llm = get_llm()

    if not llm:
        raw_cmms = json.loads(fetch_cmms_records.invoke({"alarm_code": alarm_code}))
        summary = f"Alarm {alarm_code} on {raw_cmms['subsystem']}: {raw_cmms['historical_root_cause']}"
        transcript = (
            f"### GxP Deviation Investigation: {inc_id}\n"
            f"- **Subsystem**: {raw_cmms['subsystem']}\n"
            f"- **Observation**: Line stopped at {vials:,} vials due to '{reason}'.\n"
            f"- **Direct Root Cause**: {raw_cmms['historical_root_cause']}\n"
            f"- **Containment Action**: {raw_cmms['recommended_action']}\n"
            f"- **CAPA Proposal**: Execute optical recalibration and verify 10 consecutive vials."
        )
        return {"deviation_summary": summary, "agent_raw_transcript": transcript}

    system_prompt = (
        "You are an expert GxP Packaging Reliability & QA Agent for vial manufacturing. "
        "Query the CMMS failure records and pre-incident telemetry to diagnose the root cause.\n"
        "Output a formal investigation report with Observation, Root Cause, Containment, and Long-Term CAPA."
    )

    user_prompt = (
        f"Incident ID: {inc_id} | Asset: {line_id} | Alarm: {alarm_code}\n"
        f"Reason: {reason} | Vials: {vials:,}\n"
        "Investigate the incident using available tools."
    )

    messages = [SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)]

    for _ in range(5):
        ai_msg = llm.invoke(messages)
        messages.append(ai_msg)
        if not ai_msg.tool_calls:
            break

        for tool_call in ai_msg.tool_calls:
            selected_tool = tools_by_name.get(tool_call["name"])
            tool_output = selected_tool.invoke(tool_call["args"]) if selected_tool else "{}"
            messages.append(ToolMessage(content=str(tool_output), tool_call_id=tool_call["id"]))

    final_content = messages[-1].content
    first_line = final_content.strip().split("\n")[0].replace("#", "").strip()
    summary = first_line if len(first_line) > 10 else f"Investigation for Alarm {alarm_code} on {line_id}"

    return {"deviation_summary": summary, "agent_raw_transcript": final_content}