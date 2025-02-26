import boto3
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
import json

model = SentenceTransformer('all-MiniLM-L6-v2')

def download_data_from_s3(bucket_name, prefix):
    s3_client = boto3.client('s3')
    objects = s3_client.list_objects_v2(Bucket=bucket_name, Prefix=prefix)
    
    data = []
    for obj in objects.get('Contents', []):
        file_content = s3_client.get_object(Bucket=bucket_name, Key=obj['Key'])
        file_data = file_content['Body'].read().decode('utf-8')
        data.append(file_data)
    
    return data

def index_data(data):
    # Create embeddings for your data
    embeddings = model.encode(data, convert_to_tensor=False)
    
    # Convert to numpy array
    embeddings = np.array(embeddings).astype('float32')

    # Initialize FAISS index
    index = faiss.IndexFlatL2(embeddings.shape[1])
    index.add(embeddings)
    
    return index, embeddings


def retrieve_documents(query, index, data, top_k=5):
    query_embedding = model.encode([query], convert_to_tensor=False)
    query_embedding = np.array(query_embedding).astype('float32')
    
    distances, indices = index.search(query_embedding, top_k)
    
    retrieved_docs = [data[i] for i in indices[0]]
    return retrieved_docs


def construct_prompt(query, retrieved_docs):
    context = "\n\n".join(retrieved_docs)
    prompt = f"User Query: {query}\n\nContext:\n{context}\n\nResponse:"
    return prompt

# Example usage
bucket_name = 'test-llm-troubleshoot-rag'
prefix = '2024/'

data = download_data_from_s3(bucket_name, prefix)
# index, embeddings = index_data(data)

# Example search
# query = "What is the problem of frontend?"
# retrieved_docs = retrieve_documents(query, index, data)
# prompt = construct_prompt(query, retrieved_docs)

# response = generate_response_bedrock(prompt)
# print(response)