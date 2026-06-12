import os
from dotenv import load_dotenv
from pinecone import Pinecone, ServerlessSpec
from langchain_text_splitters import RecursiveCharacterTextSplitter
from tools.sample_docs import DOCS

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", "env.secret"))

def run_ingestion():
    pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
    index_name = os.getenv("PINECONE_INDEX_NAME")

    # Create Pinecone index if it doesn't exist
    if index_name not in pc.list_indexes().names():
        print(f"Creating index: {index_name}...")
        pc.create_index(
            name=index_name,
            dimension=1024,
            metric="cosine",
            spec=ServerlessSpec(cloud="aws", region="us-east-1")
        )

    index = pc.Index(index_name)
    
    # Character Text Splitter configuration (1000 limit, 200 overlap)
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000, 
        chunk_overlap=200
    )

    vectors_by_namespace: dict[str, list] = {}
    records = [
        {
            "id": doc["id"],
            "inputs": {"text": doc["text"]},
            "metadata": {k: v for k, v in doc.items() if k != "id"},
        }
        for doc in DOCS
    ]
    for doc in records:
        chunks = text_splitter.split_text(doc["text"])
        for idx, chunk in enumerate(chunks):
            # Generate Embeddings natively inside Pinecone utilizing input_type="passage"
            embedding_res = pc.inference.embed(
                model="llama-text-embed-v2",
                inputs=[chunk],
                parameters={"input_type": "passage", "truncate": "END"}
            )
            
            vectors_by_namespace.setdefault(doc["metadata"].get("destination"), []).append({
            "id":     f"{doc['id']}_chunk_{idx}",
            "values": embedding_res.data[0].values,
            "metadata": {
                "text":     chunk,
                "destination":     doc["metadata"].get("destination"),
                "source": doc["metadata"].get("source"),
                "category": doc["metadata"].get("category"),
            }
        })

    # Upsert to Vector Store
    for namespace, vectors in vectors_by_namespace.items():
        index.upsert(vectors=vectors, namespace=namespace)
    print(f"Successfully ingested chunks into Pinecone index '{index_name}'.")

# if __name__ == "__main__":
#     run_ingestion()