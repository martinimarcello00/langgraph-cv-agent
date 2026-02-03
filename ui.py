import gradio as gr
import logging
from agent import graph

logger = logging.getLogger(__name__)

async def gradio_chat(message, history):
    """
    Wrapper for Gradio to interact with the LangGraph agent.
    """
    try:
        inputs = {"messages": [("user", message)]}
        thread_id = "web_user_default" 
        config = {"configurable": {"thread_id": thread_id}, "run_name": "CV Agent"}
        
        result = await graph.ainvoke(inputs, config=config)
        last_msg = result["messages"][-1]
        return last_msg.content
        
    except Exception as e:
        logger.error(f"Gradio Error: {e}", exc_info=True)
        return f"Error: {str(e)}"

# Create Gradio App
demo = gr.ChatInterface(
    fn=gradio_chat,
    title="Marcello's Personal Agent",
    description="Ask me anything about Marcello!<br><br>Made with ❤️ by Marcello Martini",
    examples=["Who is Marcello?", "What are his skills?", "Show me his projects"]
)
demo.show_api = False
