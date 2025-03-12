output "configure_kubectl" {
  description = "Configure kubectl: make sure you're logged in with the correct AWS profile and run the following command to update your kubeconfig"
  value       = "aws eks --region ${local.region} update-kubeconfig --name ${module.eks.cluster_name}"
}

output "opensearch_serverless_collection_endpoint" {
  description = "Endpoint of the OpenSearch Serverless collection"
  value       = module.ingestion_pipeline.collection_endpoint
}
