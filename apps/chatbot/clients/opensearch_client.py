from opensearchpy import OpenSearch, RequestsHttpConnection
from requests_aws4auth import AWS4Auth
import boto3, os
from utils.logger import logger


class OpenSearchClient:
    def __init__(self):
        self.region = os.environ.get('AWS_DEFAULT_REGION')
        self.opensearch_endpoint = os.environ.get('OPENSEARCH_ENDPOINT')
        self.client = None
        self.credentials = None
        self.last_refresh = None
        self.initialize_client()

    def initialize_client(self):
        self.credentials = boto3.Session().get_credentials()
        logger.debug("Refreshing OpenSearch credentials")
        auth = AWS4Auth(
            self.credentials.access_key,
            self.credentials.secret_key,
            self.region,
            'aoss',
            session_token=self.credentials.token
        )

        self.client = OpenSearch(
            hosts=[{'host': self.opensearch_endpoint, 'port': 443}],
            http_auth=auth,
            use_ssl=True,
            verify_certs=True,
            connection_class=RequestsHttpConnection
        )

    def check_and_refresh_credentials(self):
        """Check if credentials need to be refreshed and refresh if necessary"""
        if self.credentials.refresh_needed():
            self.initialize_client()

    def retrieve_documents(self, query_embedding, index_name, top_k=5, min_score=0.4):
        """Retrieve documents with automatic credential refresh"""
        self.check_and_refresh_credentials()

        query_body = {
            "query": {
                "bool": {
                    "must": [
                        {
                            "knn": {
                                "embedding": {
                                    "vector": query_embedding,
                                    "k": top_k
                                }
                            }
                        }
                    ]
                }
            },
            "_source": False,
            "fields": ["id", "log"],
            "size": top_k,
            "min_score": min_score
        }

        try:
            results = self.client.search(
                body=query_body,
                index=index_name
            )

            if results["hits"]["total"]["value"] > 0:
                context = [hit["fields"]["log"][0] for hit in results["hits"]["hits"]]
                context_log = "\n".join(context)
                logger.debug(f"Context found in OpenSearch: \n{context_log}")
                return context
            else:
                logger.error("No match for the prompt found in the vector database")
                return None

        except Exception as e:
            logger.error(f"Error during OpenSearch query: {str(e)}")
            if "AuthenticationException" in str(e):
                self.initialize_client()
                results = self.client.search(
                    body=query_body,
                    index=index_name
                )
                if results["hits"]["total"]["value"] > 0:
                    return [hit["fields"]["log"][0] for hit in results["hits"]["hits"]]
            return None


