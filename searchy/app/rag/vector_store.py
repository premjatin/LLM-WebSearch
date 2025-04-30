import faiss
import pickle
from pathlib import Path
from sentence_transformers import SentenceTransformer
from app.core.config import settings
import numpy as np
from typing import List, Tuple, Optional

class FAISSVectorStore:
    def __init__(self):
        self.store_path = Path(settings.vector_store_path)
        self.index_file = self.store_path / settings.faiss_index_file
        self.metadata_file = self.store_path / settings.faiss_metadata_file
        self.embedding_model = None
        self.index = None
        self.metadata = [] # List to store the actual text chunks corresponding to index positions

        self._load_model()
        self._load_store()

    def _load_model(self):
        """Loads the sentence transformer model."""
        try:
            print(f"Loading embedding model: {settings.embedding_model_name}")
            self.embedding_model = SentenceTransformer(settings.embedding_model_name)
            print("Embedding model loaded.")
        except Exception as e:
            print(f"Error loading embedding model: {e}")
            # Handle error appropriately, maybe raise or exit
            raise RuntimeError(f"Failed to load embedding model: {settings.embedding_model_name}") from e

    def _load_store(self):
        """Loads the FAISS index and metadata if they exist."""
        if self.index_file.exists() and self.metadata_file.exists():
            try:
                print(f"Loading FAISS index from: {self.index_file}")
                self.index = faiss.read_index(str(self.index_file))
                print(f"Loading metadata from: {self.metadata_file}")
                with open(self.metadata_file, "rb") as f:
                    self.metadata = pickle.load(f)
                print(f"FAISS index and metadata loaded. Index size: {self.index.ntotal if self.index else 0}, Metadata size: {len(self.metadata)}")
            except Exception as e:
                print(f"Error loading FAISS index or metadata: {e}. Store will be empty.")
                self.index = None
                self.metadata = []
        else:
            print("FAISS index or metadata file not found. Store is empty.")
            self.index = None
            self.metadata = []

    def is_ready(self) -> bool:
        """Checks if the vector store is loaded and ready."""
        return self.index is not None and self.embedding_model is not None and len(self.metadata) > 0

    def search(self, query: str, k: int = 3) -> List[Tuple[float, str]]:
        """Performs a similarity search."""
        if not self.is_ready():
            print("Vector store not ready for search.")
            return []

        try:
            query_embedding = self.embedding_model.encode([query])[0]
            # FAISS expects a 2D array for search
            query_embedding_np = np.array([query_embedding]).astype('float32')

            # Perform the search
            distances, indices = self.index.search(query_embedding_np, k)

            results = []
            if indices.size > 0:
                for i, idx in enumerate(indices[0]):
                    if 0 <= idx < len(self.metadata): # Ensure index is valid
                        score = distances[0][i] # FAISS returns L2 distance, lower is better
                        text_chunk = self.metadata[idx]
                        results.append((float(score), text_chunk))
                    else:
                         print(f"Warning: FAISS returned invalid index {idx}")

            # Sort by score (ascending for L2 distance)
            results.sort(key=lambda x: x[0])
            return results

        except Exception as e:
            print(f"Error during FAISS search: {e}")
            return []

# Single instance for the application
vector_store = FAISSVectorStore()