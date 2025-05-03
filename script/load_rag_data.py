import argparse
import pickle
from pathlib import Path
import faiss
import numpy as np

from langchain_community.document_loaders import TextLoader, DirectoryLoader # Or other loaders like CSVLoader, PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer

from app.core.config import settings # Use settings for consistency

def ingest_data(source_dir: str, chunk_size: int = 1000, chunk_overlap: int = 150):
    """Loads data, splits, embeds, and saves to FAISS and metadata file."""

    source_path = Path(source_dir)
    if not source_path.exists():
        print(f"Error: Source directory or file '{source_dir}' not found.")
        return

    vector_store_path = Path(settings.vector_store_path)
    index_file = vector_store_path / settings.faiss_index_file
    metadata_file = vector_store_path / settings.faiss_metadata_file

    try:
        # 1. Load documents
        print(f"Loading documents from: {source_path}")
        if source_path.is_dir():
            # Example: Load all .txt files from the directory
            loader = DirectoryLoader(str(source_path), glob="**/*.txt", loader_cls=TextLoader, show_progress=True)
        elif source_path.is_file():
             # Example: Load a single .txt file
             loader = TextLoader(str(source_path))
        else:
            print(f"Error: Source path '{source_dir}' is neither a file nor a directory.")
            return

        documents = loader.load()
        if not documents:
            print("No documents loaded. Exiting.")
            return
        print(f"Loaded {len(documents)} documents.")

        # 2. Split documents into chunks
        print(f"Splitting documents into chunks (size={chunk_size}, overlap={chunk_overlap})...")
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
        )
        chunks = text_splitter.split_documents(documents)
        if not chunks:
            print("No chunks created after splitting. Exiting.")
            return
        print(f"Split into {len(chunks)} chunks.")

        # Extract just the text content for embedding and metadata
        chunk_texts = [chunk.page_content for chunk in chunks]

        # 3. Load embedding model
        print(f"Loading embedding model: {settings.embedding_model_name}")
        model = SentenceTransformer(settings.embedding_model_name)
        print("Embedding model loaded.")

        # 4. Embed chunks
        print("Embedding text chunks...")
        embeddings = model.encode(chunk_texts, show_progress_bar=True)
        print(f"Created {len(embeddings)} embeddings of dimension {embeddings.shape[1]}.")

        # Ensure embeddings are float32 for FAISS
        embeddings = np.array(embeddings).astype('float32')

        # 5. Create FAISS index
        dimension = embeddings.shape[1]
        # Using IndexFlatL2 - simple L2 distance search. Consider other index types for large datasets (e.g., IndexIVFFlat).
        index = faiss.IndexFlatL2(dimension)
        index.add(embeddings)
        print(f"Created FAISS index with {index.ntotal} vectors.")

        # 6. Save FAISS index and metadata
        print(f"Saving FAISS index to: {index_file}")
        faiss.write_index(index, str(index_file))

        print(f"Saving metadata (text chunks) to: {metadata_file}")
        with open(metadata_file, "wb") as f:
            pickle.dump(chunk_texts, f)

        print("Ingestion complete.")

    except Exception as e:
        print(f"An error occurred during ingestion: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Load data into FAISS vector store for RAG.")
    parser.add_argument("source_directory", type=str, help="Path to the directory or file containing documents to ingest.")
    parser.add_argument("--chunk_size", type=int, default=1000, help="Chunk size for splitting documents.")
    parser.add_argument("--chunk_overlap", type=int, default=150, help="Chunk overlap for splitting documents.")
    args = parser.parse_args()

    ingest_data(args.source_directory, args.chunk_size, args.chunk_overlap)