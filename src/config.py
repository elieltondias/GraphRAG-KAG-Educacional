import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

@dataclass(frozen=True)
class Settings:
    host: str = os.getenv('FALKORDB_HOST', 'localhost')
    port: int = int(os.getenv('FALKORDB_PORT', '6379'))
    password: str = os.getenv('FALKORDB_PASSWORD', '')
    graph: str = os.getenv('GRAPH_NAME', 'ensino_2024_amostra')
    embedding: str = os.getenv('EMBEDDING_MODE', 'semantic')
    model: str = 'sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2'
    llm_url: str = os.getenv('LLM_BASE_URL', '')
    llm_model: str = os.getenv('LLM_MODEL', '')
    llm_key: str = os.getenv('LLM_API_KEY', '')
