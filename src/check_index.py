import chromadb

CHROMA_DIR = "data/chroma"
COLLECTION_NAME = "used_cars"

client = chromadb.PersistentClient(path=CHROMA_DIR)
col = client.get_or_create_collection(name=COLLECTION_NAME)

print("Collection:", COLLECTION_NAME)
print("Count:", col.count())