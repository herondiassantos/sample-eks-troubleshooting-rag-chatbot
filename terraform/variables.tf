variable "name" {
  default = "eks-llm-troubleshooting"
}

variable "slack_webhook_url" {
  description = "Slack webhook URL for Prometheus AlertManager notifications (used by both deployments)"
  type        = string
  default     = ""
}

variable "slack_channel_name" {
  description = "Slack channel name for Prometheus AlertManager notifications (used by both deployments)"
  type        = string
  default     = ""
}

variable "opensearch_collection_name" {
  description = "Name for the OpenSearch Serverless collection"
  type        = string
  default     = "vector-col"
}

variable "deployment_type" {
  description = "Type of deployment: 'rag' for RAG-based chatbot or 'agentic' for agentic troubleshooting"
  type        = string
  default     = "rag"
  validation {
    condition     = contains(["rag", "agentic"], var.deployment_type)
    error_message = "Deployment type must be either 'rag' or 'agentic'."
  }
}

# Agentic deployment specific variables
variable "agentic_image_repository" {
  description = "ECR repository for the agentic troubleshooting agent image"
  type        = string
  default     = ""
}

variable "agentic_image_tag" {
  description = "Tag for the agentic troubleshooting agent image"
  type        = string
  default     = "latest"
}

variable "slack_bot_token" {
  description = "Slack bot token for agentic deployment"
  type        = string
  default     = ""
  sensitive   = true
}

variable "slack_app_token" {
  description = "Slack app token for agentic deployment"
  type        = string
  default     = ""
  sensitive   = true
}

variable "slack_signing_secret" {
  description = "Slack signing secret for agentic deployment"
  type        = string
  default     = ""
  sensitive   = true
}

variable "bedrock_model_id" {
  description = "Bedrock model ID for agentic deployment"
  type        = string
  default     = "us.anthropic.claude-3-7-sonnet-20250219-v1:0"
}

variable "vector_bucket_name" {
  description = "S3 bucket name for vector storage (must be created manually before deployment)"
  type        = string
  default     = ""
}

variable "vector_index_name" {
  description = "S3 Vectors index name for troubleshooting knowledge"
  type        = string
  default     = "k8s-troubleshooting"
}