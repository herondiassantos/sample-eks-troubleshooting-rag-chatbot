output "configure_kubectl" {
  description = "Configure kubectl: make sure you're logged in with the correct AWS profile and run the following command to update your kubeconfig"
  value       = "aws eks --region ${local.region} update-kubeconfig --name ${module.eks.cluster_name}"
}

output "deployment_type" {
  description = "The type of deployment that was created"
  value       = var.deployment_type
}

# RAG deployment outputs
output "opensearch_collection_endpoint" {
  description = "OpenSearch Serverless collection endpoint (RAG deployment only)"
  value       = var.deployment_type == "rag" ? module.ingestion_pipeline[0].collection_endpoint : null
}

output "chatbot_ecr_repository" {
  description = "ECR repository for the RAG chatbot (RAG deployment only)"
  value       = var.deployment_type == "rag" ? module.agentic_chatbot[0].chatbot_ecr_repo : null
}

# Agentic deployment outputs
output "agentic_agent_role_arn" {
  description = "IAM role ARN for the agentic troubleshooting agent (Agentic deployment only)"
  value       = var.deployment_type == "agentic" ? aws_iam_role.agentic_agent_role[0].arn : null
}

output "agentic_agent_service_account" {
  description = "Kubernetes service account for the agentic agent (Agentic deployment only)"
  value       = var.deployment_type == "agentic" ? "k8s-troubleshooting-agent" : null
}

# Common outputs
output "cluster_name" {
  description = "EKS cluster name"
  value       = module.eks.cluster_name
}

output "cluster_endpoint" {
  description = "EKS cluster endpoint"
  value       = module.eks.cluster_endpoint
}

output "region" {
  description = "AWS region"
  value       = local.region
}