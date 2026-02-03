"""
Gradio UI definition for the Agent.
"""
import gradio as gr
import logging
from typing import List, Tuple, Any
from agent import graph

# --- Configuration ---
DEFAULT_THREAD_ID = "web_user_default"

# --- Initialization ---
logger = logging.getLogger(__name__)

# --- Handlers ---

async def gradio_chat(message: str, history: List[List[str]]) -> str:
    """
    Wrapper for Gradio to interact with the LangGraph agent.
    """
    try:
        inputs = {"messages": [("user", message)]}
        
        # Configuration for the agent execution
        config = {
            "configurable": {"thread_id": DEFAULT_THREAD_ID}, 
            "run_name": "CV Agent"
        }
        
        # Invoke the graph asynchronously
        result = await graph.ainvoke(inputs, config=config)
        
        # Extract the final response
        last_msg = result["messages"][-1]
        return last_msg.content
        
    except Exception as e:
        logger.error(f"Gradio Interaction Error: {e}", exc_info=True)
        return f"System Error: {str(e)}"

# --- UI Setup ---

# Customizing the Gradio interface
demo = gr.ChatInterface(
    fn=gradio_chat,
    title="Marcello's Personal Agent",
    description="Ask me anything about Marcello!<br><br>Made with ❤️ by Marcello Martini",
    examples=[
        "Who is Marcello?", 
        "What are his skills?", 
        "Show me his projects"
    ]
)

# Hide the API button for a cleaner look
demo.show_api = False
