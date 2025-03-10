# GPU NodeClass
resource "kubernetes_manifest" "gpu_nodeclass" {
  manifest = {
    apiVersion = "karpenter.k8s.aws/v1"
    kind       = "EC2NodeClass"
    metadata = {
      name = "gpu-nodeclass"
    }
    spec = {
      amiFamily = "AL2"
      amiSelectorTerms = [
        {
          # Use the GPU-optimized AMI
          name   = "amazon-eks-gpu-node-1.31-*"
          owners = ["amazon"]
        }
      ]

      subnetSelectorTerms = [{
        tags = {
          "karpenter.sh/discovery" = local.name
        }
      }]

      securityGroupSelectorTerms = [{
        tags = {
          "karpenter.sh/discovery" = local.name
        }
      }]

      tags = {
        "karpenter.sh/discovery" = local.name
      }

      role = local.name

      blockDeviceMappings = [
        {
          deviceName = "/dev/xvda"
          ebs = {
            volumeSize = "200Gi" # Increased from 100Gi to 200Gi
            volumeType = "gp3"
            encrypted  = true
          }
        }
      ]
    }
  }

  depends_on = [module.eks, module.karpenter, helm_release.karpenter]
}

# GPU NodePool
resource "kubernetes_manifest" "gpu_nodepool" {
  manifest = {
    apiVersion = "karpenter.sh/v1"
    kind       = "NodePool"
    metadata = {
      name = "gpu-nodepool"
    }
    spec = {
      template = {
        metadata = {
          labels = {
            owner                    = "data-engineer"
            "nvidia.com/gpu.present" = "true"
          }
        }
        spec = {
          nodeClassRef = {
            name  = "gpu-nodeclass"
            kind  = "EC2NodeClass"
            group = "karpenter.k8s.aws"
          }

          requirements = [
            {
              key      = "karpenter.k8s.aws/instance-family"
              operator = "In"
              values   = ["g5", "g6"]
            },
            {
              key      = "karpenter.k8s.aws/instance-size"
              operator = "In"
              values   = ["xlarge", "2xlarge", "4xlarge", "8xlarge", "12xlarge", "16xlarge"]
            },
            {
              key      = "karpenter.sh/capacity-type"
              operator = "In"
              values   = ["on-demand", "spot"]
            }
          ]

          taints = [
            {
              key    = "nvidia.com/gpu"
              value  = "true"
              effect = "NoSchedule"
            }
          ]
        }
      }

      disruption = {
        consolidationPolicy = "WhenEmptyOrUnderutilized"
        consolidateAfter    = "30s"
      }

      limits = {
        cpu    = "1000"
        memory = "1000Gi"
      }
    }
  }

  depends_on = [kubernetes_manifest.gpu_nodeclass, helm_release.karpenter]
}


