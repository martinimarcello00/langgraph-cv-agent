import os
from typing import TypedDict, Annotated
from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage, AIMessage
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

# --- Nodes ---

def agent_node(state: AgentState):
    """The main agent that calls tools."""
    messages = state["messages"]
    
    # Context Windowing: Keep last 6 messages (approx 3 turns)
    recent_messages = messages[-6:]
    
    # Load system prompt
    with open("prompts/system.md", "r") as f:
        system_prompt = f.read()
        
    response = llm_with_tools.invoke([SystemMessage(content=system_prompt)] + recent_messages)
    return {"messages": [response]}

def final_answer_node(state: AgentState):
    """Generates the final answer after tool usage, without access to further tools."""
    messages = state["messages"]
    
    # Context Windowing: Keep last 6 messages (approx 3 turns)
    recent_messages = messages[-6:]
    
    # Load system prompt
    with open("prompts/system.md", "r") as f:
        system_prompt = f.read()
    
    # Use the LLM *without* tools bound to prevent further tool calls
    response = llm.invoke([SystemMessage(content=system_prompt)] + recent_messages)
    return {"messages": [response]}

# --- Graph ---

workflow = StateGraph(AgentState)

workflow.add_node("agent", agent_node)
workflow.add_node("tools", ToolNode(tools))
workflow.add_node("final_answer", final_answer_node)

workflow.add_edge(START, "agent")

def should_continue(state: AgentState):
    last_message = state["messages"][-1]
    if last_message.tool_calls:
        return "tools"
    # If no tool calls, it might be a direct answer or a refusal handled by the LLM
    return END

workflow.add_conditional_edges("agent", should_continue)
workflow.add_edge("tools", "final_answer")
workflow.add_edge("final_answer", END)

memory = MemorySaver()
graph = workflow.compile(checkpointer=memory)
