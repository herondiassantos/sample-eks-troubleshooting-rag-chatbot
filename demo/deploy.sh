#!/bin/bash

echo "🚀 Deploying Multi-Tier Demo Application with Issues..."
echo "=================================================="

# Deploy the broken application
kubectl apply -f demo/multi-tier-app.yaml

echo ""
echo "✅ Application deployed to demo-app namespace"
echo ""
echo "⏳ Waiting for pods to start (and fail)..."
sleep 10

echo ""
echo "📊 Current Pod Status:"
kubectl get pods -n demo-app

echo ""
echo "🔍 Expected Issues:"
echo "- monitoring-agent: ImagePullBackOff (nonexistent image)"
echo "- backend-api: CrashLoopBackOff (wrong Redis service name)"
echo "- backend-api: OOMKilled (insufficient memory)"
echo "- frontend-web: Running but can't reach backend (wrong port)"

echo ""
echo "🤖 Ready for agent troubleshooting!"
echo "Start by asking: 'Check the status of pods in the demo-app namespace'"