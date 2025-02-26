import json
from datetime import datetime
import pytz
from sentence_transformers import CrossEncoder

# Define UTC timezone
utc = pytz.utc

def retrieve_documents(query_embedding, index, data, top_k=10):
    # Perform the search using the query embedding
    distances, indices = index.search(query_embedding, top_k)
    
    # If no documents are found, return an empty list
    if len(indices[0]) == 0:
        print("No documents found for the given query embedding.")
        return []
    
    # Retrieve the documents from the data using the indices
    retrieved_docs = [data[i] for i in indices[0] if i < len(data)]
    print(f"Retrieved documents: {retrieved_docs[:3]}")  # Display a preview of the retrieved documents
    return retrieved_docs

def rerank_documents(query, retrieved_docs):
    # Load the cross-encoder model
    cross_encoder_model = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')
    
    # Create pairs of (query, document) for re-ranking
    query_doc_pairs = [[query, doc] for doc in retrieved_docs]
    
    # Get cross-encoder scores for each pair
    scores = cross_encoder_model.predict(query_doc_pairs)
    
    # Sort documents by score in descending order
    ranked_docs = [doc for _, doc in sorted(zip(scores, retrieved_docs), reverse=True)]
    
    return ranked_docs

def construct_prompt(query, retrieved_docs, max_docs=10, time_threshold_minutes=None):
    # Get the current time in UTC
    current_utc_time = datetime.now(utc).isoformat()

    # Re-rank the retrieved documents before constructing the prompt
    ranked_docs = rerank_documents(query, retrieved_docs)
    
    # Limit the number of documents in the context to max_docs
    context_docs = ranked_docs[:max_docs]
    
    if not context_docs:
        context = "No relevant logs found."
    else:
        context = "\n\n".join(context_docs)

    # Create a prompt to generate a kubectl command to get more details if needed 
    kubectl_prompt = "When needed Generate a kubectl command to get more details about the relevant logs, use a key 'KUBECTL_COMMAND: command' if true for to parse, make sure that you have real pod names not templates"
    # Construct the final prompt
    prompt = f"Instructions: {kubectl_prompt} \n\nUser Query: {query}\n\nCheck if the log time is within last {time_threshold_minutes} minutes \n\nCurrent UTC Time: {current_utc_time}\n\nContext:\n{context}\n\nResponse:"
    # prompt = f"User Query: {query}\n\nCheck if the log time is within last {time_threshold_minutes} minutes \n\nCurrent UTC Time: {current_utc_time}\n\nContext:\n{context}\n\nResponse:"
    return prompt
