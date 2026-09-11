import os
from collections import OrderedDict
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
from usage_utils import MODEL_NAME, budget

# Load env vars (safe to call multiple times)
load_dotenv()

# --- Models ---
llm = ChatOpenAI(
    model=MODEL_NAME,
    api_key=os.getenv("OPENAI_API_KEY"),
    # Left at the default on purpose: reasoning_effort="minimal" cut latency but
    # made the model skip tool calls on roughly two questions in three.
    reasoning_effort=os.getenv("OPENAI_REASONING_EFFORT", "medium"),
    stream_usage=True,
)
llm_with_tools = llm.bind_tools(tools)

# --- State ---
class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]

# --- Nodes ---

# --- Prompt Loading (Optimized) ---
# Load prompts once at module level to avoid file I/O on every request
try:
    with open("prompts/agent.md", "r") as f:
        AGENT_PROMPT = f.read()
except FileNotFoundError as e:
    raise RuntimeError(f"Critical Error: Prompt file not found: {e}")

# The catalogue lets the model answer "what has he written about X" with no tool
# call, and stops it guessing at ids it cannot see.
try:
    with open("corpus/catalog.txt", "r") as f:
        CATALOG = f.read()
except FileNotFoundError as e:
    raise RuntimeError(f"Critical Error: catalogue missing, run build_index.py: {e}")

# Built once so the prefix stays byte-identical and stays eligible for prompt caching.
SYSTEM_MESSAGE = SystemMessage(content=f"{AGENT_PROMPT}\n\n{CATALOG}")

# --- Helpers ---
def get_safe_history(messages: list[BaseMessage], k: int = 4) -> list[BaseMessage]:
    """
    Safely retrieves the last k messages (reduced to 4 for better performance),
    ensuring that we do not slice in the middle of a tool execution sequence.
    
    k=4 means approximately 2 conversation turns, which is sufficient for
    most interactions while reducing token usage and improving response time.
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

async def run_agent_reasoning(state: AgentState):
    """
    The main reasoning node.
    It analyzes the conversation state and decides whether to call tools or proceed.
    Uses 'prompts/agent.md' which now includes style guidelines.
    """
    messages = state["messages"]
    
    # Context Windowing: Keep last 4 messages (approx 2 turns), ensuring valid tool sequences
    recent_messages = get_safe_history(messages, k=4)
    
    # Must be awaited: a sync call here would block the event loop and defeat token streaming.
    response = await llm_with_tools.ainvoke([SYSTEM_MESSAGE] + recent_messages)
    budget.record(getattr(response, "usage_metadata", None))
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


class BoundedMemorySaver(MemorySaver):
    """MemorySaver with an LRU cap.

    thread_id comes from the visitor's localStorage, so without a cap the checkpointer
    grows with every unique visitor for as long as the process lives.
    """

    def __init__(self, max_threads: int = 500) -> None:
        super().__init__()
        self._max_threads = max_threads
        self._recent_threads: OrderedDict[str, None] = OrderedDict()

    def _track(self, config) -> None:
        thread_id = (config or {}).get("configurable", {}).get("thread_id")
        if thread_id is None:
            return
        self._recent_threads.pop(thread_id, None)
        self._recent_threads[thread_id] = None
        while len(self._recent_threads) > self._max_threads:
            oldest, _ = self._recent_threads.popitem(last=False)
            # Eviction is best effort: a full checkpointer must never break a reply.
            try:
                self.delete_thread(oldest)
            except Exception:
                pass

    def put(self, config, checkpoint, metadata, new_versions):
        result = super().put(config, checkpoint, metadata, new_versions)
        self._track(config)
        return result

    async def aput(self, config, checkpoint, metadata, new_versions):
        result = await super().aput(config, checkpoint, metadata, new_versions)
        self._track(config)
        return result


memory = BoundedMemorySaver(max_threads=int(os.getenv("MAX_CHAT_THREADS", "500")))
graph = workflow.compile(checkpointer=memory)
