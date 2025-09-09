from strands import Agent, tool
from src.agents.memory_agent import MemoryAgent
from src.agents.k8s_specialist import K8sSpecialist
from src.config.settings import Config
import logging

logger = logging.getLogger(__name__)

class OrchestratorAgent:
    """Direct K8s troubleshooting orchestrator."""
    
    def __init__(self):
        self.memory_agent = MemoryAgent()
        self.k8s_specialist = K8sSpecialist()
        
        self.agent = Agent(
            name="K8s Orchestrator",
            system_prompt="""You are a direct K8s troubleshooting orchestrator. Be concise and action-oriented:

1. ALWAYS use memory_operations first to check for similar issues before troubleshooting
2. If relevant memories found, return them to the user. If no relevant memory found, use troubleshoot_k8s
3. After solving new issues, use memory_operations to store the solution
4. ALWAYS provide a complete response to the user - never return empty responses
5. If you store a solution, confirm it was stored AND provide the solution details to the user
6. Format responses for Slack (no markdown, use *bold* and `code`)""",
            model=Config.BEDROCK_MODEL_ID,
            tools=[self.memory_operations, self.troubleshoot_k8s]
        )
        
    def should_respond(self, message: str, is_mention: bool = False) -> bool:
        """Check if should respond to message."""
        if is_mention:
            return True
        
        k8s_keywords = ["pod", "crashloopbackoff", "error", "failed", "pending", 
                       "kubernetes", "k8s", "deployment", "service"]
        return any(keyword in message.lower() for keyword in k8s_keywords)

    def respond(self, message: str, thread_id: str, context: str = None) -> str:
        """Main entry point for responses."""
        channel_id = thread_id.split(':')[0] if ':' in thread_id else thread_id
        
        prompt = f"""User Message: "{message}"
Channel: {channel_id}
Thread Context: {context or "No previous context"}

Analyze the FULL context and provide a direct, actionable response. Do not ask follow-up questions unless absolutely critical information is missing."""
        
        try:
            return str(self.agent(prompt))
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
    def troubleshoot_k8s(self, query: str, context: str = None, channel_id: str = None) -> str:
        """Perform K8s troubleshooting."""
        try:
            solution = self.k8s_specialist.troubleshoot(query, context)
            return solution
        except Exception as e:
            return f"Troubleshooting error: {e}"