from strands import Agent, tool
from src.agents.memory_agent import MemoryAgent
from src.agents.k8s_specialist import K8sSpecialist
from src.config.settings import Config
from src.prompts import ORCHESTRATOR_SYSTEM_PROMPT, CLASSIFICATION_PROMPT, K8S_KEYWORDS
import logging
import boto3
import json

logger = logging.getLogger(__name__)

class OrchestratorAgent:
    """Direct K8s troubleshooting orchestrator."""
    
    def __init__(self):
        self.memory_agent = MemoryAgent()
        self.k8s_specialist = K8sSpecialist()
        
        # Initialize Bedrock client for Nova Micro classification
        try:
            self.bedrock_client = boto3.client('bedrock-runtime', region_name=Config.AWS_REGION)
        except Exception as e:
            logger.warning(f"Failed to initialize Bedrock client, falling back to keywords: {e}")
            self.bedrock_client = None
        
        self.agent = Agent(
            name="K8s Orchestrator",
            system_prompt=ORCHESTRATOR_SYSTEM_PROMPT,
            model=Config.BEDROCK_MODEL_ID,
            tools=[self.memory_operations, self.troubleshoot_k8s]
        )
        
    def should_respond(self, message: str, is_mention: bool = False, is_thread: bool = False) -> bool:
        """Check if should respond to message using SLM or keyword fallback."""
        if is_mention:
            return True
        
        # If this is a thread reply, assume it's relevant (saves inference costs)
        if is_thread:
            return True
        
        # Try Nova Micro classification first
        if self.bedrock_client:
            return self._classify_with_nova(message)
        
        # Fallback to keyword matching
        return any(keyword in message.lower() for keyword in K8S_KEYWORDS)
    
    def _classify_with_nova(self, message: str) -> bool:
        """Use Amazon Nova Micro to classify if message is K8s/troubleshooting related."""
        try:
            prompt = CLASSIFICATION_PROMPT.format(message=message)
            
            body = {
                "messages": [
                    {
                        "role": "user",
                        "content": [{"text": prompt}]
                    }
                ],
                "inferenceConfig": {
                    "maxTokens": 10,
                    "temperature": 0.1
                }
            }
            
            response = self.bedrock_client.invoke_model(
                modelId="amazon.nova-micro-v1:0",
                body=json.dumps(body)
            )
            
            result = json.loads(response['body'].read())
            logger.info(f"Message classification should respond:{result}")
            
            answer = result['output']['message']['content'][0]['text'].strip().upper()
            
            return answer == "YES"
            
        except Exception as e:
            logger.error(f"Nova classification failed: {e}")
            # Fallback to keyword matching
            return any(keyword in message.lower() for keyword in K8S_KEYWORDS)

    def respond(self, message: str, thread_id: str, context: str = None) -> str:
        """Main entry point for responses."""
        try:
            response = str(self.agent(message)).strip()
            return response if response else "I'm here to help with Kubernetes troubleshooting. How can I assist you?"
        except Exception as e:
            logger.error(f"Orchestrator error: {e}")
            return "Error processing request. Please try again."



    @tool
    def memory_operations(self, request: str) -> str:
        """Handle memory operations - store or retrieve K8s troubleshooting information."""
        try:
            result = self.memory_agent.agent(request)
            return str(result)
        except Exception as e:
            logger.error(f"Memory operation failed: {e}")
            return f"Memory error: {e}"

    @tool
    def troubleshoot_k8s(self, query: str) -> str:
        """Perform K8s troubleshooting."""
        try:
            return self.k8s_specialist.troubleshoot(query)
        except Exception as e:
            return f"Troubleshooting error: {e}"