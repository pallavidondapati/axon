import os
from dotenv import load_dotenv
load_dotenv()
GROQ_API_KEY=os.getenv("GROQ_API_KEY")
LLM_MODEL = "llama-3.3-70b-versatile"
APP_NAME = "AgentX"
APP_VERSION = "1.0.0"
DB_PATH = "db/agentx.db"
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"