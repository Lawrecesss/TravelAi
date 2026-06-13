import os
from pinecone import Pinecone, ServerlessSpec
from langchain_text_splitters import RecursiveCharacterTextSplitter
from tools.sample_docs import DOCS

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

    vectors_to_upsert = []
    records = [
        {
            "id": doc["id"],
            "text": doc["text"], 
            "metadata": {k: v for k, v in doc.items() if k not in ["id", "text"]},
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
            
            vectors_to_upsert.append({
            "id":     f"{doc['id']}_chunk_{idx}",
            "values": embedding_res.data[0].values,
            "metadata": doc["metadata"] | {"chunk": chunk}
        })

    # Upsert to Vector Store
    index.upsert(vectors=vectors_to_upsert)
    print(f"Successfully ingested chunks into Pinecone index '{index_name}'.")

# if __name__ == "__main__":
#     run_ingestion()