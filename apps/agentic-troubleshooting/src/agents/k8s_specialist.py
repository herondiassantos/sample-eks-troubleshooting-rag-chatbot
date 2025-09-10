"""K8s specialist agent with embedded EKS MCP server."""

from strands import Agent
from mcp import stdio_client, StdioServerParameters
from strands.tools.mcp import MCPClient
import logging
import os
import boto3
from src.tools.k8s_tools import describe_pod, get_pods
from src.config.settings import Config
from src.prompts import K8S_SPECIALIST_SYSTEM_PROMPT

logger = logging.getLogger(__name__)


class K8sSpecialist:
    """K8s troubleshooting specialist with embedded EKS MCP server."""
    
    def __init__(self):
        """Initialize the K8s specialist with EKS MCP integration."""
        # Start with local K8s tools
        tools = [describe_pod, get_pods]
        
        # Add EKS MCP server if enabled
        if Config.ENABLE_EKS_MCP:
            try:
                # Get AWS credentials from the current session (Pod Identity)
                session = boto3.Session()
                credentials = session.get_credentials()
                
                # Create EKS MCP client with explicit credentials
                env_vars = {
                    "AWS_REGION": Config.AWS_REGION,
                    "FASTMCP_LOG_LEVEL": "ERROR"
                }
                
                # Pass explicit AWS credentials if available
                if credentials:
                    env_vars["AWS_ACCESS_KEY_ID"] = credentials.access_key
                    env_vars["AWS_SECRET_ACCESS_KEY"] = credentials.secret_key
                    if credentials.token:
                        env_vars["AWS_SESSION_TOKEN"] = credentials.token
                    logger.info("Using Pod Identity credentials for EKS MCP server")
                else:
                    # Fallback to environment credentials
                    for key in ["AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "AWS_SESSION_TOKEN", "AWS_PROFILE"]:
                        if key in os.environ:
                            env_vars[key] = os.environ[key]
                    logger.info("Using environment credentials for EKS MCP server")
                
                # Use kubeconfig created by init container
                env_vars["KUBECONFIG"] = "/shared/kubeconfig"
                
                # Build args based on configuration
                args = ["awslabs.eks-mcp-server@latest", "--allow-sensitive-data-access"]
                if Config.EKS_MCP_ALLOW_WRITE:
                    args.append("--allow-write")
                
                self.eks_mcp_client = MCPClient(lambda: stdio_client(
                    StdioServerParameters(
                        command="uvx",
                        args=args,
                        env=env_vars
                    )
                ))
                
                # Get EKS MCP tools and add to tools list
                with self.eks_mcp_client:
                    eks_tools = self.eks_mcp_client.list_tools_sync()
                    tools.extend(eks_tools)
                    logger.info(f"Added {len(eks_tools)} EKS MCP tools")
                    
            except Exception as e:
                logger.warning(f"Failed to initialize EKS MCP: {e}")
                self.eks_mcp_client = None
        else:
            self.eks_mcp_client = None
        
        cluster_info = f"Cluster: {getattr(Config, 'CLUSTER_NAME', 'unknown')} in region {Config.AWS_REGION}\n"
        
        self.system_prompt = f"{cluster_info}{K8S_SPECIALIST_SYSTEM_PROMPT}"
        
        self.agent = Agent(
            system_prompt=self.system_prompt,
            model=Config.BEDROCK_MODEL_ID,
            tools=tools
        )
    
    def troubleshoot(self, issue: str) -> str:
        """Troubleshoot a K8s issue with EKS cluster context."""
        try:
            if self.eks_mcp_client:
                with self.eks_mcp_client:
                    return str(self.agent(issue)).strip()
            else:
                return str(self.agent(issue)).strip()
        except Exception as e:
            logger.error(f"Error troubleshooting: {e}")
            return "Error during troubleshooting. Please try again."