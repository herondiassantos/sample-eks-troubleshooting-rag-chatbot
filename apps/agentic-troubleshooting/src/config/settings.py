"""Configuration settings for the Strands Slack Agent."""

import os


class Config:
    """Configuration class for the Strands Slack Agent."""
    
    @classmethod
    def validate(cls) -> None:
        """Validate required configuration values."""
        slack_bot_token = os.getenv('SLACK_BOT_TOKEN', '')
        slack_app_token = os.getenv('SLACK_APP_TOKEN', '')
        slack_signing_secret = os.getenv('SLACK_SIGNING_SECRET', '')
        
        required_fields = [
            ('SLACK_BOT_TOKEN', slack_bot_token),
            ('SLACK_APP_TOKEN', slack_app_token),
            ('SLACK_SIGNING_SECRET', slack_signing_secret),
        ]
        
        missing_fields = [field for field, value in required_fields if not value]
        
        if missing_fields:
            raise ValueError(
                f"Missing required configuration fields: {', '.join(missing_fields)}. "
                "Please set these environment variables."
            )
    
    # Dynamic properties that read from environment at access time
    @property
    def CLUSTER_NAME(self) -> str:
        return os.getenv('CLUSTER_NAME', 'eks-cluster')
    
    @property
    def SLACK_BOT_TOKEN(self) -> str:
        return os.getenv('SLACK_BOT_TOKEN', '')
    
    @property
    def SLACK_APP_TOKEN(self) -> str:
        return os.getenv('SLACK_APP_TOKEN', '')
    
    @property
    def SLACK_SIGNING_SECRET(self) -> str:
        return os.getenv('SLACK_SIGNING_SECRET', '')
    
    @property
    def AWS_REGION(self) -> str:
        return os.getenv('AWS_REGION', 'us-east-1')
    
    @property
    def BEDROCK_MODEL_ID(self) -> str:
        return os.getenv('BEDROCK_MODEL_ID', 'anthropic.claude-3-sonnet-20240229-v1:0')
    
    @property
    def AGENT_NAME(self) -> str:
        return os.getenv('AGENT_NAME', 'strands-slack-agent')
    
    @property
    def AGENT_DESCRIPTION(self) -> str:
        return os.getenv(
            'AGENT_DESCRIPTION', 
            'An intelligent agent that analyzes Slack conversations and responds when appropriate'
        )
    
    @property
    def LOG_LEVEL(self) -> str:
        return os.getenv('LOG_LEVEL', 'DEBUG')
    
    @property
    def LOG_FORMAT(self) -> str:
        return os.getenv('LOG_FORMAT', 'json')
    
    @property
    def RESPONSE_THRESHOLD(self) -> float:
        return float(os.getenv('RESPONSE_THRESHOLD', '0.7'))
    
    @property
    def MAX_CONTEXT_MESSAGES(self) -> int:
        return int(os.getenv('MAX_CONTEXT_MESSAGES', '10'))
    
    @property
    def RESPONSE_DELAY_SECONDS(self) -> int:
        return int(os.getenv('RESPONSE_DELAY_SECONDS', '2'))
    
    @property
    def ENABLE_THREAD_CONTEXT(self) -> bool:
        return os.getenv('ENABLE_THREAD_CONTEXT', 'true').lower() == 'true'
    
    @property
    def ENABLE_CHANNEL_MONITORING(self) -> bool:
        return os.getenv('ENABLE_CHANNEL_MONITORING', 'true').lower() == 'true'
    
    @property
    def ENABLE_DM_RESPONSES(self) -> bool:
        return os.getenv('ENABLE_DM_RESPONSES', 'true').lower() == 'true'
    
    @property
    def ENABLE_MENTION_RESPONSES(self) -> bool:
        return os.getenv('ENABLE_MENTION_RESPONSES', 'true').lower() == 'true'
    
    @property
    def ENABLE_EKS_MCP(self) -> bool:
        return os.getenv('ENABLE_EKS_MCP', 'false').lower() == 'true'
    
    @property
    def EKS_MCP_ALLOW_WRITE(self) -> bool:
        return os.getenv('EKS_MCP_ALLOW_WRITE', 'false').lower() == 'true'
    
    @property
    def VECTOR_BUCKET(self) -> str:
        return os.getenv('VECTOR_BUCKET', 'test-vector-s3-bucket-321')
    
    @property
    def INDEX_NAME(self) -> str:
        return os.getenv('INDEX_NAME', 'k8s-troubleshooting')


# Create a singleton instance for use throughout the app
Config = Config()