# Agentic deployment resources - only created when deployment_type = "agentic"

# IAM policy for EKS MCP server
resource "aws_iam_policy" "eks_mcp_policy" {
  count = var.deployment_type == "agentic" ? 1 : 0
  
  name        = "${local.name}-eks-mcp-policy"
  description = "IAM policy for EKS MCP server access"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "eks:DescribeCluster",
          "eks:ListClusters",
          "eks:DescribeNodegroup",
          "eks:ListNodegroups",
          "eks:DescribeAddon",
          "eks:ListAddons"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents",
          "logs:DescribeLogGroups",
          "logs:DescribeLogStreams",
          "logs:GetLogEvents",
          "logs:StartQuery",
          "logs:StopQuery",
          "logs:GetQueryResults"
        ]
        Resource = [
          "arn:aws:logs:*:${data.aws_caller_identity.current.account_id}:*",
          "arn:aws:logs:*:${data.aws_caller_identity.current.account_id}:log-group:/aws/containerinsights/${local.name}/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "cloudwatch:GetMetricStatistics",
          "cloudwatch:GetMetricData",
          "cloudwatch:ListMetrics"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "bedrock:InvokeModel",
          "bedrock:InvokeModelWithResponseStream"
        ]
        Resource = [
          "arn:aws:bedrock:*::foundation-model/*",
          "arn:aws:bedrock:*:${data.aws_caller_identity.current.account_id}:inference-profile/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "s3vectors:PutVectors",
          "s3vectors:QueryVectors",
          "s3vectors:GetVectors",
          "s3vectors:DeleteVectors"
        ]
        Resource = var.deployment_type == "agentic" && var.vector_bucket_name != "" ? [
          "arn:aws:s3vectors:*:${data.aws_caller_identity.current.account_id}:bucket/${var.vector_bucket_name}/*",
          "arn:aws:s3vectors:*:${data.aws_caller_identity.current.account_id}:bucket/${var.vector_bucket_name}/index/${var.vector_index_name}"
        ] : []
      }
    ]
  })

  tags = local.tags
}

# Pod Identity Association for the agentic troubleshooting agent
resource "aws_eks_pod_identity_association" "agentic_agent" {
  count = var.deployment_type == "agentic" ? 1 : 0

  cluster_name    = module.eks.cluster_name
  namespace       = "default"
  service_account = "k8s-troubleshooting-agent"
  role_arn        = aws_iam_role.agentic_agent_role[0].arn

  tags = local.tags
}

# IAM role for the agentic troubleshooting agent
resource "aws_iam_role" "agentic_agent_role" {
  count = var.deployment_type == "agentic" ? 1 : 0

  name = "${local.name}-agentic-agent-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "pods.eks.amazonaws.com"
        }
        Action = [
          "sts:AssumeRole",
          "sts:TagSession"
        ]
      }
    ]
  })

  tags = local.tags
}

# Attach the EKS MCP policy to the role
resource "aws_iam_role_policy_attachment" "agentic_agent_eks_mcp" {
  count = var.deployment_type == "agentic" ? 1 : 0

  role       = aws_iam_role.agentic_agent_role[0].name
  policy_arn = aws_iam_policy.eks_mcp_policy[0].arn
}

# Access entry for the agentic agent role
resource "aws_eks_access_entry" "agentic_agent" {
  count = var.deployment_type == "agentic" ? 1 : 0

  cluster_name      = module.eks.cluster_name
  principal_arn     = aws_iam_role.agentic_agent_role[0].arn
  kubernetes_groups = []
  type              = "STANDARD"

  tags = local.tags
}

# Access policy association for full admin access
resource "aws_eks_access_policy_association" "agentic_agent_admin" {
  count = var.deployment_type == "agentic" ? 1 : 0

  cluster_name  = module.eks.cluster_name
  principal_arn = aws_iam_role.agentic_agent_role[0].arn
  policy_arn    = "arn:aws:eks::aws:cluster-access-policy/AmazonEKSClusterAdminPolicy"

  access_scope {
    type = "cluster"
  }

  depends_on = [aws_eks_access_entry.agentic_agent]
}

# Kubernetes secret for Slack credentials
resource "kubernetes_secret" "slack_credentials" {
  count = var.deployment_type == "agentic" ? 1 : 0

  metadata {
    name      = "slack-credentials"
    namespace = "default"
  }

  data = {
    bot-token      = var.slack_bot_token
    app-token      = var.slack_app_token
    signing-secret = var.slack_signing_secret
  }

  type = "Opaque"
}

# Helm release for the agentic troubleshooting agent
resource "helm_release" "agentic_agent" {
  count = var.deployment_type == "agentic" && var.agentic_image_repository != "" ? 1 : 0

  name             = "k8s-troubleshooting-agent"
  chart            = "${path.module}/../apps/agentic-troubleshooting/helm/k8s-troubleshooting-agent"
  namespace        = "default"
  create_namespace = false
  wait             = true
  timeout          = 300

  values = [
    yamlencode({
      image = {
        repository = var.agentic_image_repository
        tag        = var.agentic_image_tag
        pullPolicy = "Always"
      }
      
      serviceAccount = {
        create = true
        name   = "k8s-troubleshooting-agent"
      }
      
      config = {
        clusterName     = module.eks.cluster_name
        awsRegion      = local.region
        bedrockModelId = var.bedrock_model_id
        logLevel       = "INFO"
        
        # Vector Storage Configuration
        vectorBucket = var.vector_bucket_name
        indexName    = var.vector_index_name
        
        eksMcp = {
          enabled    = true
          allowWrite = true
        }
        
        slack = {
          botToken      = var.slack_bot_token
          appToken      = var.slack_app_token
          signingSecret = var.slack_signing_secret
        }
      }
      
      secrets = {
        slack = {
          botToken      = var.slack_bot_token
          appToken      = var.slack_app_token
          signingSecret = var.slack_signing_secret
        }
      }
      
      resources = {
        limits = {
          cpu    = "500m"
          memory = "512Mi"
        }
        requests = {
          cpu    = "100m"
          memory = "256Mi"
        }
      }
      
      rbac = {
        create = true
        rules = [
          {
            apiGroups = [""]
            resources = ["pods", "services", "events"]
            verbs     = ["get", "list", "watch"]
          },
          {
            apiGroups = ["apps"]
            resources = ["deployments", "replicasets"]
            verbs     = ["get", "list", "watch"]
          },
          {
            apiGroups = [""]
            resources = ["pods/log"]
            verbs     = ["get"]
          }
        ]
      }
    })
  ]

  depends_on = [
    aws_eks_pod_identity_association.agentic_agent,
    kubernetes_secret.slack_credentials
  ]
}