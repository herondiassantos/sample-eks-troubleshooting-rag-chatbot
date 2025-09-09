"""Simple Kubernetes tools for troubleshooting."""

import logging
from typing import Optional
from kubernetes import client, config
from strands import tool

logger = logging.getLogger(__name__)

# Try to load Kubernetes configuration
try:
    config.load_incluster_config()  # Try in-cluster first
except:
    try:
        config.load_kube_config()  # Fall back to kubeconfig file
    except Exception as e:
        logger.warning(f"Could not load Kubernetes config: {e}")


@tool
def describe_pod(namespace: str, pod_name: str) -> str:
    """Describe a Kubernetes pod (similar to kubectl describe pod).
    
    Args:
        namespace: The Kubernetes namespace
        pod_name: The name of the pod
    
    Returns:
        Pod description or error message
    """
    try:
        v1 = client.CoreV1Api()
        pod = v1.read_namespaced_pod(name=pod_name, namespace=namespace)
        
        # Format basic pod info
        output = f"Name: {pod.metadata.name}\n"
        output += f"Namespace: {pod.metadata.namespace}\n"
        output += f"Node: {pod.spec.node_name}\n"
        output += f"Status: {pod.status.phase}\n"
        output += f"IP: {pod.status.pod_ip}\n\n"
        
        # Container statuses
        output += "Containers:\n"
        if pod.status.container_statuses:
            for cs in pod.status.container_statuses:
                output += f"  {cs.name}:\n"
                output += f"    Ready: {cs.ready}\n"
                output += f"    Restarts: {cs.restart_count}\n"
                if cs.state.running:
                    output += f"    State: Running\n"
                elif cs.state.waiting:
                    output += f"    State: Waiting ({cs.state.waiting.reason})\n"
                elif cs.state.terminated:
                    output += f"    State: Terminated ({cs.state.terminated.reason})\n"
        
        # Events
        events = v1.list_namespaced_event(
            namespace=namespace,
            field_selector=f"involvedObject.name={pod_name}"
        )
        if events.items:
            output += "\nRecent Events:\n"
            for event in events.items[-5:]:  # Last 5 events
                output += f"  {event.type}: {event.reason} - {event.message}\n"
        
        return output
    except Exception as e:
        return f"Error describing pod: {str(e)}"


@tool
def get_pods(namespace: Optional[str] = None) -> str:
    """Get list of pods (similar to kubectl get pods).
    
    Args:
        namespace: Optional namespace. If not provided, gets pods from all namespaces
    
    Returns:
        List of pods or error message
    """
    try:
        v1 = client.CoreV1Api()
        
        if namespace:
            pods = v1.list_namespaced_pod(namespace=namespace)
            output = f"Pods in namespace {namespace}:\n"
        else:
            pods = v1.list_pod_for_all_namespaces()
            output = "Pods in all namespaces:\n"
        
        output += f"{'NAMESPACE':<15} {'NAME':<40} {'READY':<7} {'STATUS':<20} {'RESTARTS':<10}\n"
        output += "-" * 95 + "\n"
        
        for pod in pods.items:
            ready_containers = 0
            total_containers = 0
            restarts = 0
            
            if pod.status.container_statuses:
                total_containers = len(pod.status.container_statuses)
                for cs in pod.status.container_statuses:
                    if cs.ready:
                        ready_containers += 1
                    restarts += cs.restart_count
            
            ready_str = f"{ready_containers}/{total_containers}"
            
            output += f"{pod.metadata.namespace:<15} {pod.metadata.name:<40} {ready_str:<7} {pod.status.phase:<20} {restarts:<10}\n"
        
        return output
    except Exception as e:
        return f"Error getting pods: {str(e)}"
