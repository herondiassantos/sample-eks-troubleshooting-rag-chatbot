from sentence_transformers import SentenceTransformer
import numpy as np

model = SentenceTransformer('all-MiniLM-L12-v2')

# Function to encode data
def encode_data(data):
    embeddings = model.encode(data, convert_to_tensor=False)
    return np.array(embeddings).astype('float32')

# Function to encode a single query
def encode_query(query):
    query_embedding = model.encode([query], convert_to_tensor=False)
    return np.array(query_embedding).astype('float32')
