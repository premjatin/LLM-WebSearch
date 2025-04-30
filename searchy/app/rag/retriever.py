from app.rag.vector_store import vector_store
from typing import List

def retrieve_context(query: str, k: int = 3) -> str:
    """
    Retrieves relevant text chunks from the vector store based on the query.
    Returns a single string concatenating the results.
    """
    if not vector_store.is_ready():
        return "Internal knowledge base (RAG) is not available."

    results = vector_store.search(query, k=k)

    if not results:
        return "No relevant information found in the internal knowledge base."

    # Combine the text chunks into a single context string
    # You might want to add separators or metadata here
    context = "\n---\n".join([chunk for score, chunk in results])
    print(f"--- RAG Retrieved Context (Top {len(results)} chunks) ---")
    # print(context) # Optional: print retrieved context for debugging
    return context