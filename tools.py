import os
import yaml
from typing import Literal
from dotenv import load_dotenv
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma

# Configuration for RAG
CHROMA_DB_DIR = "./chroma_db"
EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

# Load env vars
load_dotenv()

PERSONAL_DATA_DIR = os.path.join(os.path.dirname(__file__), "personal_data")

def get_profile_section(section_name: Literal["activities", "awards", "certifications", "education", "experience", "volunteer"]) -> str:
    """Retrieves a specific section of the user's profile data (YAML)."""
    try:
        file_path = os.path.join(PERSONAL_DATA_DIR, f"{section_name}.yml")
        if not os.path.exists(file_path):
            return f"Error: Section '{section_name}' not found."
        
        with open(file_path, "r") as f:
            data = yaml.safe_load(f)
        return yaml.dump(data)
    except Exception as e:
        return f"Error retrieving section {section_name}: {str(e)}"

PROJECTS_DIR = os.path.join(PERSONAL_DATA_DIR, "projects")

def list_projects() -> str:
    """Returns a list of available projects with their descriptions."""
    try:
        if not os.path.exists(PROJECTS_DIR):
            return "No projects directory found."
        
        project_list = []
        for filename in os.listdir(PROJECTS_DIR):
            if filename.endswith(".md"):
                project_id = filename.replace(".md", "")
                file_path = os.path.join(PROJECTS_DIR, filename)
                
                try:
                    with open(file_path, "r") as f:
                        content = f.read()
                        
                    # Extract frontmatter
                    if content.startswith("---"):
                        parts = content.split("---", 2)
                        if len(parts) >= 3:
                            frontmatter = yaml.safe_load(parts[1])
                            title = frontmatter.get("title", project_id)
                            description = frontmatter.get("description", "No description available.")
                            project_list.append(f"- {project_id}: {title} - {description}")
                        else:
                            project_list.append(f"- {project_id}: (No metadata)")
                    else:
                        project_list.append(f"- {project_id}")
                except Exception:
                    project_list.append(f"- {project_id}")

        if not project_list:
            return "No projects available."
        
        return "\n".join(project_list)
    except Exception as e:
        return f"Error listing projects: {str(e)}"

def get_project_details(project_id: str) -> str:
    """Retrieves the details of a specific project by its ID (filename without extension)."""
    try:
        # Security: Prevent traversal
        if ".." in project_id or "/" in project_id:
            return "Error: Invalid project ID."
            
        file_path = os.path.join(PROJECTS_DIR, f"{project_id}.md")
        if not os.path.exists(file_path):
            return f"Error: Project '{project_id}' not found. Use list_projects() to see available ID."
        
        with open(file_path, "r") as f:
            return f.read()
    except Exception as e:
        return f"Error retrieving project {project_id}: {str(e)}"

def search_projects(query: str) -> str:
    """Searches for projects using RAG (Vector Search). Returns relevant project chunks."""
    try:
        if not os.path.exists(CHROMA_DB_DIR):
            return "Error: ChromaDB index not found. Please run 'create_rag.ipynb' to generate the index."
            
        # Initialize Embeddings (must match what was used for indexing)
        embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL_NAME)
        
        # Load Vector Store
        vectorstore = Chroma(persist_directory=CHROMA_DB_DIR, embedding_function=embeddings)
        
        # Perform Search
        results = vectorstore.similarity_search(query, k=3)
        
        if not results:
            return f"No projects found matching '{query}'."
            
        formatted_results = []
        for doc in results:
            source = doc.metadata.get("source", "Unknown Source")
            content = doc.page_content
            formatted_results.append(f"Source: {source}\nContent: {content}\n---")
            
        return "\n".join(formatted_results)
        
    except Exception as e:
        return f"Error searching projects: {str(e)}"

tools = [get_profile_section, list_projects, get_project_details, search_projects]
