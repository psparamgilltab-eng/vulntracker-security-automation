
variable "kubeconfig_path" {
  description = "Path to the kubeconfig for the existing Kubernetes cluster."
  type        = string
  default     = "~/.kube/config"
}

variable "namespace" {
  description = "Namespace for VulnTracker."
  type        = string
  default     = "vulntracker"
}

variable "container_image" {
  description = "Published VulnTracker container image."
  type        = string
}

variable "storage_class_name" {
  description = "Storage class available in the Kubernetes cluster."
  type        = string
}

variable "secret_store_name" {
  description = "Existing External Secrets Operator ClusterSecretStore."
  type        = string
}

variable "aws_secret_name" {
  description = "AWS Secrets Manager secret containing SECRET_KEY."
  type        = string
}

variable "allowed_ingress_cidr" {
  description = "Trusted source CIDR allowed to reach VulnTracker pods."
  type        = string
}
