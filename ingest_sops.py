import chromadb
from chromadb.utils import embedding_functions

CHROMA_PATH = "chroma_db"
COLLECTION_NAME = "pharma_sops"

# 2 Minimal SOP documents matching our machine failure modes
SOPS = [
    {
        "id": "SOP-PKG-104",
        "title": "Handling Heat Sealing Temperature Excursions",
        "content": (
            "SOP-PKG-104: If blister packaging sealing temperature drops below 110°C, "
            "trigger Error Code 104 immediately. Halt the line to prevent non-sterile seals. "
            "Inspect thermocouple sensor lead B for drift or disconnect. Verify heater band continuity. "
            "If thermal binding occurs, replace sensor lead B before clearing the fault and restarting."
        ),
        "metadata": {"error_code": 104, "area": "packaging", "criticality": "high"}
    },
    {
        "id": "SOP-PKG-201",
        "title": "Resolution of Blister Feed Guide Jams",
        "content": (
            "SOP-PKG-201: Blister guide rail jams trigger Error Code 201. "
            "Usually caused by pneumatic cylinder pressure dropping below 5.0 bar. "
            "Inspect pneumatic feed line, check guide rail clearance with feeler gauge (standard: 1.2mm), "
            "and replace worn seal rings on the guide cylinder."
        ),
        "metadata": {"error_code": 201, "area": "packaging", "criticality": "medium"}
    }
]

def main():
    print(f"Initializing ChromaDB vector store at './{CHROMA_PATH}'...")
    
    # Use persistent client so embeddings are saved to disk
    client = chromadb.PersistentClient(path=CHROMA_PATH)
    
    # Default lightweight embedding model (all-MiniLM-L6-v2 runs locally on CPU)
    emb_fn = embedding_functions.DefaultEmbeddingFunction()
    
    # Create or get collection
    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        embedding_function=emb_fn
    )

    # Ingest documents
    ids = [sop["id"] for sop in SOPS]
    documents = [sop["content"] for sop in SOPS]
    metadatas = [sop["metadata"] for sop in SOPS]

    collection.upsert(
        ids=ids,
        documents=documents,
        metadatas=metadatas
    )

    print(f"Successfully ingested {len(ids)} SOP documents into collection '{COLLECTION_NAME}'.")

if __name__ == "__main__":
    main()