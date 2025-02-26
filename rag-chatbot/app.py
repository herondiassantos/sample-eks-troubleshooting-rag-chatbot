import gradio as gr
import threading
import asyncio
import logging
import os
from indexer import load_index, index_data, save_index
from s3_utils import download_all_logs_to_single_file
from embedder import encode_data, encode_query
from retriever import retrieve_documents, construct_prompt
# from bedrock_client import invoke_claude
from kubernetes_resource import generate_response_with_kubectl
from data_loader import load_data_from_chunks, filter_data
from datetime import timedelta

# Constants
INDEX_PATH = 'faiss_index.index'
CHUNKS_DIR = 'data_chunks/'
DOWNLOAD_DATA = os.getenv("DOWNLOAD_DATA", 'True')
bucket_name = os.getenv("BUCKET_NAME", 'eks-llm-troubleshooting-logs-rag-eks')
prefix = os.getenv("PREFIX")
top_k = 3

# Set up logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Lock for thread-safe data access
data_lock = threading.Lock()

logger.info("Loading index from disk...")
index = load_index(INDEX_PATH)

# If not index or data, download it
if DOWNLOAD_DATA:
    if not os.path.exists(CHUNKS_DIR):
        logger.warning(f"Chunks directory {
                       CHUNKS_DIR} not found, downloading from S3...")
        download_all_logs_to_single_file(
            bucket_name, prefix, CHUNKS_DIR, logger)

data = load_data_from_chunks(CHUNKS_DIR, logger)

exclusion_keywords = []
limit_per_keyword = {}
filtered_data = filter_data(data, exclusion_keywords=exclusion_keywords,
                            limit_per_keyword=limit_per_keyword, logger=logger)

if not filtered_data:
    logger.error(
        "No data found after filtering. Please check the S3 bucket and data files.")
    raise ValueError("No data loaded from chunks after filtering.")

if not index or not filtered_data or DOWNLOAD_DATA:
    logger.warning("Index or data not found, processing chunks...")
    embeddings = encode_data(filtered_data)
    if embeddings is None or len(embeddings) == 0:
        logger.error(
            "Failed to encode data. The data might be empty or invalid.")
        raise ValueError("Failed to encode data.")

    index = index_data(embeddings, INDEX_PATH)
    save_index(index, INDEX_PATH)
    logger.info("Index created and data saved locally.")
else:
    logger.info("Index and data loaded from disk.")

# Create the chatbot interface that will be called.


def chatbot_interface(user_input, time_threshold_minutes):
    logger.info(f"Received user query: {user_input} with time threshold: {
                time_threshold_minutes} minutes")
    with data_lock:
        query_embedding = encode_query(user_input)
        retrieved_docs = retrieve_documents(
            query_embedding, index, filtered_data, top_k=top_k)
        prompt = construct_prompt(
            user_input, retrieved_docs, time_threshold_minutes=time_threshold_minutes)
        print(prompt)
    response = generate_response_with_kubectl(prompt)
    # response = invoke_claude(prompt)
    logger.info(f"Generated response: {response}")
    return response


def create_interface():
    with gr.Blocks(css=".container { max-width: 700px; margin: auto; padding-top: 20px; }") as demo:
        gr.Markdown(
            """
            <div style="text-align: center;">
                <h1>FAISS-Based Document Retrieval Chatbot</h1>
                <p>Type your query below and interact with the chatbot.</p>
                <p><strong>Set the time threshold (in minutes) to filter recent logs.</strong></p>
                <p><strong>Click "Update Index" to refresh the index in the background.</strong></p>
            </div>
            """
        )

        with gr.Row():
            with gr.Column(scale=2):
                user_input = gr.Textbox(label="Your Query")
                time_threshold_input = gr.Slider(
                    minimum=1, maximum=60, step=1, value=5, label="Time Threshold (minutes)")
            with gr.Column(scale=1):
                submit_btn = gr.Button("Submit")

        chatbot_output = gr.Markdown(label="Chatbot Response")

        submit_btn.click(fn=chatbot_interface, inputs=[
                         user_input, time_threshold_input], outputs=chatbot_output)

    return demo


if __name__ == "__main__":
    logger.info("Starting Gradio interface...")
    interface = create_interface()
    interface.launch()
    logger.info("Gradio interface launched successfully.")
    