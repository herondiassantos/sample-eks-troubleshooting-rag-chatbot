from datetime import datetime
import pytz
from opensearchpy import OpenSearch, RequestsHttpConnection
from requests_aws4auth import AWS4Auth
import boto3
import logging
import os

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Define UTC timezone
utc = pytz.utc
opensearch_endpoint = os.environ.get('OPENSEARCH_ENDPOINT')

# Get credentials
credentials = boto3.Session().get_credentials()
region = 'us-east-1'

# Create AWS4Auth instance
auth = AWS4Auth(
    credentials.access_key,
    credentials.secret_key,
    region,
    'aoss',
    session_token=credentials.token  # Include this if you're using temporary credentials
)

# Configure OpenSearch client
client = OpenSearch(
    hosts=[{'host': opensearch_endpoint, 'port': 443}],
    http_auth=auth,
    use_ssl=True,
    verify_certs=True,
    connection_class=RequestsHttpConnection
)


def retrieve_documents(query_embedding, index_name, top_k=5):
    # Perform the search using the query embedding
    query_body = {
        "query": {"knn": {"embedding": {"vector": query_embedding, "k": top_k}}},
        "_source": False,
        "fields": ["id", "log"],
    }

    results = client.search(
        body=query_body,
        index=index_name
    )

    if results["hits"]["total"]["value"] > 0:
        docs = [doc for hit in results["hits"]["hits"] for doc in hit["fields"]["log"]]
        return docs
    else:
        logger.error("No match for the prompt found in the vector database")


def construct_prompt(query, retrieved_docs, max_docs=5):
    # Get the current time in UTC
    current_utc_time = datetime.now(utc).isoformat()

    # Limit the number of documents in the context to max_docs
    context_docs = retrieved_docs[:max_docs]

    if not context_docs:
        context = "No relevant logs found."
    else:
        context = "\n\n".join(context_docs)

    # Create a prompt to generate a kubectl command to get more details if needed 
    kubectl_prompt = "When needed Generate a kubectl command to get more details about the relevant logs, use a key 'KUBECTL_COMMAND: command' if true for to parse, make sure that you have real pod names not templates"
    # Construct the final prompt
    prompt = f"Instructions: {kubectl_prompt} \n\nUser Query: {query} \n\nContext:\n{context}\n\nResponse:"
    # prompt = f"Instructions: {kubectl_prompt} \n\nUser Query: {query} \n\nCheck if the log time is within last {time_threshold_minutes} minutes \n\nCurrent UTC Time: {current_utc_time}\n\nContext:\n{context}\n\nResponse:"
    return prompt
