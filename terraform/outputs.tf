
output "namespace" {
  description = "Namespace where VulnTracker is deployed."
  value       = kubernetes_namespace_v1.vulntracker.metadata[0].name
}

output "service_name" {
  description = "Internal Kubernetes service name."
  value       = kubernetes_service_v1.vulntracker.metadata[0].name
}
