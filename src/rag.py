import chromadb
from sentence_transformers import SentenceTransformer

CHROMA_DIR = "data/chroma"
COLLECTION_NAME = "used_cars"

client = chromadb.PersistentClient(path=CHROMA_DIR)
col = client.get_or_create_collection(name=COLLECTION_NAME)
emb_model = SentenceTransformer("all-MiniLM-L6-v2")

def retrieve(query: str, k: int = 5, where: dict | None = None):
    q_emb = emb_model.encode([query]).tolist()
    res = col.query(query_embeddings=q_emb, n_results=k, where=where)
    return res