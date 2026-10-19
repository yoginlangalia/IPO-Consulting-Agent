import os
from dotenv import load_dotenv

load_dotenv()

# Database
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./ipo_agent.db")

# Gemini API
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# File uploads
UPLOAD_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Max file size (50MB)
MAX_FILE_SIZE = 50 * 1024 * 1024

# Allowed file extensions
ALLOWED_EXTENSIONS = {".pdf", ".xlsx", ".xls", ".csv"}
