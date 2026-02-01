import os
import yaml
from typing import Literal
from dotenv import load_dotenv

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

tools = [get_profile_section]
