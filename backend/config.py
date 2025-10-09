import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Flask
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    DEBUG = os.getenv('FLASK_ENV') == 'development'
    
    # ✅ NEW: JWT Configuration
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', os.getenv('SECRET_KEY', 'jwt-secret-key'))
    JWT_ACCESS_TOKEN_EXPIRES = 3600  # 1 hour in seconds
    JWT_REFRESH_TOKEN_EXPIRES = 2592000  # 30 days in seconds
    
    # MySQL Configuration
    MYSQL_HOST = os.getenv('MYSQL_HOST', 'localhost')
    MYSQL_USER = os.getenv('MYSQL_USER', 'mining_user')
    MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD', 'mining_password_456')
    MYSQL_DB = os.getenv('MYSQL_DATABASE', 'mining_data')
    MYSQL_PORT = int(os.getenv('MYSQL_PORT', '3307'))
    
    # ChromaDB Local Storage
    CHROMA_PERSIST_DIR = os.getenv('CHROMA_PERSIST_DIR', './chroma_data')
    
    # Ollama Configuration (Free Local LLM)
    OLLAMA_HOST = os.getenv('OLLAMA_HOST', 'localhost')
    OLLAMA_PORT = os.getenv('OLLAMA_PORT', '11434')
    OLLAMA_MODEL = os.getenv('OLLAMA_MODEL', 'mistral')
    
    # API Keys
    MISTRAL_API_KEY = os.getenv('MISTRAL_API_KEY', '')
    HUGGINGFACE_API_KEY = os.getenv('HUGGINGFACE_API_KEY', '')
    
    # Model Settings
    EMBEDDING_MODEL = 'sentence-transformers/all-MiniLM-L6-v2'
    CHUNK_SIZE = 1000
    CHUNK_OVERLAP = 200
    
    # RAG Settings
    TOP_K_RESULTS = 5
    MAX_RESPONSE