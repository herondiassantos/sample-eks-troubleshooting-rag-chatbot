resource "helm_release" "deepseek_gpu" {
  name             = "deepseek-gpu"
  chart            = "./manifests/vllm-chart"
  create_namespace = true
  wait             = false
  replace          = true
  namespace        = "deepseek"

  values = [
    <<-EOT
    nodeSelector:
      owner: "data-engineer"
    tolerations:
      - key: "nvidia.com/gpu"
        operator: "Exists"
        effect: "NoSchedule"
    resources:
      limits:
        cpu: "32"
        memory: 100G
        nvidia.com/gpu: "1"
      requests:
        cpu: "16"
        memory: 30G
        nvidia.com/gpu: "1"
    command: "vllm serve deepseek-ai/DeepSeek-R1-Distill-Llama-8B --max-model-len 4096"
    EOT
  ]
  depends_on = [module.eks, kubernetes_manifest.gpu_nodepool, helm_release.karpenter]
}

resource "helm_release" "nvidia_device_plugin" {
  name             = "nvidia-device-plugin"
  repository       = "https://nvidia.github.io/k8s-device-plugin"
  chart            = "nvidia-device-plugin"
  version          = "0.17.0"
  namespace        = "nvidia-device-plugin"
  create_namespace = true
  wait             = true

  depends_on = [module.eks, helm_release.karpenter]
}