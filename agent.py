import os
from typing import TypedDict, Annotated
from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage, AIMessage, ToolMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END, START
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.memory import MemorySaver
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Import tools
from tools import tools

# Load env vars (safe to call multiple times)
load_dotenv()

# --- Models ---
# Switching to gpt-5-nano as requested
args = {
    "model": "gpt-5-nano",
    "api_key": os.getenv("OPENAI_API_KEY")
}
llm = ChatOpenAI(**args)
llm_with_tools = llm.bind_tools(tools)

# --- State ---
class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]

# --- Helpers ---
def get_safe_history(messages: list[BaseMessage], k: int = 6) -> list[BaseMessage]:
    """
    Safely retrieves the last k messages, ensuring that we do not slice in the middle
    of a tool execution sequence (i.e. starting with a ToolMessage).
    """
    if len(messages) <= k:
        return messages
    
    start_idx = len(messages) - k
    
    # If the starting message is a ToolMessage, we must include the preceding AIMessage 
    # (and any other preceding ToolMessages) to maintain a valid conversation structure.
    while start_idx > 0 and isinstance(messages[start_idx], ToolMessage):
        start_idx -= 1
        
    return messages[start_idx:]

# --- Nodes ---

# --- Prompt Loading (Optimized) ---
# Load prompts once at module level to avoid file I/O on every request
try:
    with open("prompts/agent.md", "r") as f:
        AGENT_PROMPT = f.read()
except FileNotFoundError as e:
    raise RuntimeError(f"Critical Error: Prompt file not found: {e}")

# --- Helpers ---
def get_safe_history(messages: list[BaseMessage], k: int = 6) -> list[BaseMessage]:
    """
    Safely retrieves the last k messages, ensuring that we do not slice in the middle
    of a tool execution sequence (i.e. starting with a ToolMessage).
    """
    if len(messages) <= k:
        return messages
    
    start_idx = len(messages) - k
    
    # If the starting message is a ToolMessage, we must include the preceding AIMessage 
    # (and any other preceding ToolMessages) to maintain a valid conversation structure.
    while start_idx > 0 and isinstance(messages[start_idx], ToolMessage):
        start_idx -= 1
        
    return messages[start_idx:]

# --- Nodes ---

def run_agent_reasoning(state: AgentState):
    """
    The main reasoning node.
    It analyzes the conversation state and decides whether to call tools or proceed.
    Uses 'prompts/agent.md' which now includes style guidelines.
    """
    messages = state["messages"]
    
    # Context Windowing: Keep last 6 messages (approx 3 turns), ensuring valid tool sequences
    recent_messages = get_safe_history(messages, k=6)
    
    # Use the tool-bound LLM with the unified agent prompt
    response = llm_with_tools.invoke([SystemMessage(content=AGENT_PROMPT)] + recent_messages)
    return {"messages": [response]}

# --- Graph Construction ---

workflow = StateGraph(AgentState)

# Add nodes
workflow.add_node("agent", run_agent_reasoning)
workflow.add_node("tools", ToolNode(tools))

# Define edges
# Start by running the agent reasoning
workflow.add_edge(START, "agent")

def should_continue(state: AgentState):
    """
    Determines the next step based on the agent's output.
    If the agent requests a tool call, route to 'tools'.
    If the agent has a final answer (no tool calls), the conversation turn ends.
    """
    last_message = state["messages"][-1]
    if last_message.tool_calls:
        return "tools"
    # If no tool calls, the agent has generated the final answer directly
    return END

workflow.add_conditional_edges("agent", should_continue, {
    "tools": "tools",
    END: END
})

# Tool outputs flow back to the agent reasoning node to decide next steps
workflow.add_edge("tools", "agent")

memory = MemorySaver()
graph = workflow.compile(checkpointer=memory)
