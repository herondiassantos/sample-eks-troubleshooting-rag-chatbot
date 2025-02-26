import faiss
import os

def load_index(path):
    if os.path.exists(path):
        return faiss.read_index(path)
    else:
        return None

def save_index(index, path):
    faiss.write_index(index, path)

def index_data(embeddings, index_path):
    if os.path.exists(index_path):
        index = faiss.read_index(index_path)
    else:
        # Create a new index if it doesn't exist
        index = faiss.IndexFlatL2(embeddings.shape[1])
    
    # Add embeddings to the index
    index.add(embeddings)
    
    # Save the index to disk
    save_index(index, index_path)
    
    return index
