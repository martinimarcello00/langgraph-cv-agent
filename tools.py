import os
import yaml
import logging
from typing import Literal
from dotenv import load_dotenv
import requests

# --- Initialization ---
load_dotenv()
logger = logging.getLogger(__name__)

from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma

# --- Configuration ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PERSONAL_DATA_DIR = os.path.join(BASE_DIR, "personal_data")
PROJECTS_DIR = os.path.join(PERSONAL_DATA_DIR, "projects")
CHROMA_DB_DIR = os.path.join(BASE_DIR, "chroma_db")
EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
MAILGUN_API_KEY = os.getenv("MAILGUN_API_KEY")
MAILGUN_URL = os.getenv("MAILGUN_URL")
MAILGUN_FROM = os.getenv("MAILGUN_SENDER")

# --- Tools ---

def get_profile_section(section_name: Literal["activities", "awards", "certifications", "education", "experience", "volunteer"]) -> str:
    """
    Retrieves a specific section of the user's profile data (YAML).
    """
    try:
        file_path = os.path.join(Config.PERSONAL_DATA_DIR, f"{section_name}.yml")
        
        if not os.path.exists(file_path):
            logger.warning(f"Profile section not found: {section_name}")
            return f"Error: Section '{section_name}' not found."
        
        with open(file_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
            
        return yaml.dump(data, sort_keys=False)
        
    except Exception as e:
        logger.error(f"Error reading profile section {section_name}: {e}")
        return f"Error retrieving section {section_name}: {str(e)}"

def list_projects() -> str:
    """
    Returns a list of available projects with their descriptions.
    """
    try:
        if not os.path.exists(Config.PROJECTS_DIR):
            logger.warning("Projects directory missing.")
            return "No projects directory found."
        
        project_list = []
        
        # Iterate over markdown files in the projects directory
        for filename in sorted(os.listdir(Config.PROJECTS_DIR)):
            if filename.endswith(".md"):
                project_id = filename.replace(".md", "")
                file_path = os.path.join(Config.PROJECTS_DIR, filename)
                
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read()
                        
                    # Extract frontmatter (simple split)
                    if content.startswith("---"):
                        parts = content.split("---", 2)
                        if len(parts) >= 3:
                            frontmatter = yaml.safe_load(parts[1])
                            title = frontmatter.get("title", project_id)
                            description = frontmatter.get("description", "No description available.")
                            project_list.append(f"- {project_id}: **{title}** - {description}")
                        else:
                            project_list.append(f"- {project_id}: (No metadata)")
                    else:
                        project_list.append(f"- {project_id}")
                        
                except Exception as e:
                    logger.warning(f"Failed to read project {filename}: {e}")
                    project_list.append(f"- {project_id} (Error reading file)")

        if not project_list:
            return "No projects available."
        
        return "\n".join(project_list)
        
    except Exception as e:
        logger.error(f"Error listing projects: {e}")
        return f"Error listing projects: {str(e)}"

def get_project_details(project_id: str) -> str:
    """
    Retrieves the full details of a specific project by its ID.
    """
    try:
        # Security: Prevent directory traversal
        if ".." in project_id or "/" in project_id or "\\" in project_id:
            logger.warning(f"Invalid project ID attempt: {project_id}")
            return "Error: Invalid project ID."
            
        file_path = os.path.join(Config.PROJECTS_DIR, f"{project_id}.md")
        
        if not os.path.exists(file_path):
            return f"Error: Project '{project_id}' not found. Use list_projects() to see available IDs."
        
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
            
    except Exception as e:
        logger.error(f"Error retrieving project {project_id}: {e}")
        return f"Error retrieving project {project_id}: {str(e)}"

def search_projects(query: str) -> str:
    """
    Searches for projects using RAG (Vector Search).
    """
    try:
        if not os.path.exists(Config.CHROMA_DB_DIR):
            return "Error: ChromaDB index not found. Please run 'create_rag.ipynb' to generate the index."
            
        # Initialize Embeddings
        embeddings = HuggingFaceEmbeddings(model_name=Config.EMBEDDING_MODEL_NAME)
        
        # Load Vector Store
        vectorstore = Chroma(persist_directory=Config.CHROMA_DB_DIR, embedding_function=embeddings)
        
        # Perform Search
        results = vectorstore.similarity_search(query, k=3)
        
        if not results:
            return f"No projects found matching '{query}'."
            
        formatted_results = []
        for doc in results:
            source = doc.metadata.get("source", "Unknown Source")
            content = doc.page_content.strip()
            formatted_results.append(f"Source: {source}\nContent: {content}\n---")
            
        return "\n".join(formatted_results)
        
    except Exception as e:
        logger.error(f"Error searching projects: {e}")
        return f"Error searching projects: {str(e)}"

def send_cv_email(email_address: str) -> str:
    """
    Sends Marcello's CV to the specified email address.
    """
    try:
        # Basic validation
        if "@" not in email_address or "." not in email_address:
             return "Error: Invalid email address format. Please provide a valid email."
             
        response = requests.post(
            MAILGUN_URL,
            auth=("api", MAILGUN_API_KEY),
            data={
                "from": MAILGUN_FROM,
                "to": email_address,
                "subject": "Hello from Marcello Martini",
                "template": "send cv",
                "h:X-Mailgun-Variables": '{"test": "test"}' 
            },
            timeout=10
        )
        
        response.raise_for_status()
        return f"CV successfully sent to {email_address}!"
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Mailgun API Error: {e}")
        return f"Error sending email: Failed to connect to mail service." 
    except Exception as e:
        logger.error(f"Unexpected error in send_cv_email: {e}")
        return f"Error sending email: {str(e)}"

# Export the list of tools for the agent
tools = [get_profile_section, list_projects, get_project_details, search_projects, send_cv_email]
