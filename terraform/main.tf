
terraform {
  required_version = ">= 1.6.0"

  required_providers {
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "2.35.1"
    }
  }
}

provider "kubernetes" {
  config_path = var.kubeconfig_path
}

resource "kubernetes_namespace_v1" "vulntracker" {
  metadata {
    name = var.namespace
  }
}

resource "kubernetes_service_account_v1" "vulntracker" {
  metadata {
    name      = "vulntracker"
    namespace = kubernetes_namespace_v1.vulntracker.metadata[0].name
  }

  automount_service_account_token = false
}

resource "kubernetes_persistent_volume_claim_v1" "data" {
  metadata {
    name      = "vulntracker-data"
    namespace = kubernetes_namespace_v1.vulntracker.metadata[0].name
  }

  spec {
    access_modes       = ["ReadWriteOnce"]
    storage_class_name = var.storage_class_name

    resources {
      requests = {
        storage = "1Gi"
      }
    }
  }
}

resource "kubernetes_manifest" "external_secret" {
  manifest = {
    apiVersion = "external-secrets.io/v1"
    kind       = "ExternalSecret"

    metadata = {
      name      = "vulntracker-secrets"
      namespace = kubernetes_namespace_v1.vulntracker.metadata[0].name
    }

    spec = {
      refreshInterval = "1h"

      secretStoreRef = {
        name = var.secret_store_name
        kind = "ClusterSecretStore"
      }

      target = {
        name           = "vulntracker-secrets"
        creationPolicy = "Owner"
      }

      data = [
        {
          secretKey = "SECRET_KEY"

          remoteRef = {
            key      = var.aws_secret_name
            property = "SECRET_KEY"
          }
        }
      ]
    }
  }

  depends_on = [kubernetes_namespace_v1.vulntracker]
}

resource "kubernetes_deployment_v1" "vulntracker" {
  metadata {
    name      = "vulntracker"
    namespace = kubernetes_namespace_v1.vulntracker.metadata[0].name

    labels = {
      app = "vulntracker"
    }
  }

  spec {
    replicas = 1

    selector {
      match_labels = {
        app = "vulntracker"
      }
    }

    template {
      metadata {
        labels = {
          app = "vulntracker"
        }
      }

      spec {
        service_account_name            = kubernetes_service_account_v1.vulntracker.metadata[0].name
        automount_service_account_token = false

        security_context {
          run_as_non_root = true
          run_as_user     = 10001
          run_as_group    = 10001
          fs_group        = 10001

          seccomp_profile {
            type = "RuntimeDefault"
          }
        }

        container {
          name              = "vulntracker"
          image             = var.container_image
          image_pull_policy = "IfNotPresent"

          port {
            container_port = 8000
          }

          env {
            name  = "DATABASE_URL"
            value = "sqlite:////data/vulntracker.db"
          }

          env {
            name = "SECRET_KEY"

            value_from {
              secret_key_ref {
                name     = "vulntracker-secrets"
                key      = "SECRET_KEY"
                optional = false
              }
            }
          }

          volume_mount {
            name       = "data"
            mount_path = "/data"
          }

          resources {
            requests = {
              cpu    = "100m"
              memory = "128Mi"
            }

            limits = {
              cpu    = "500m"
              memory = "512Mi"
            }
          }

          security_context {
            allow_privilege_escalation = false
            read_only_root_filesystem  = true

            capabilities {
              drop = ["ALL"]
            }
          }

          liveness_probe {
            http_get {
              path = "/health"
              port = 8000
            }

            initial_delay_seconds = 20
            period_seconds        = 30
          }

          readiness_probe {
            http_get {
              path = "/health"
              port = 8000
            }

            initial_delay_seconds = 10
            period_seconds        = 10
          }
        }

        volume {
          name = "data"

          persistent_volume_claim {
            claim_name = kubernetes_persistent_volume_claim_v1.data.metadata[0].name
          }
        }
      }
    }
  }

  depends_on = [kubernetes_manifest.external_secret]
}

resource "kubernetes_service_v1" "vulntracker" {
  metadata {
    name      = "vulntracker"
    namespace = kubernetes_namespace_v1.vulntracker.metadata[0].name
  }

  spec {
    type = "ClusterIP"

    selector = {
      app = "vulntracker"
    }

    port {
      port        = 80
      target_port = 8000
    }
  }
}

resource "kubernetes_network_policy_v1" "restrict_ingress" {
  metadata {
    name      = "vulntracker-ingress"
    namespace = kubernetes_namespace_v1.vulntracker.metadata[0].name
  }

  spec {
    pod_selector {
      match_labels = {
        app = "vulntracker"
      }
    }

    policy_types = ["Ingress"]

    ingress {
      from {
        ip_block {
          cidr = var.allowed_ingress_cidr
        }
      }

      ports {
        port     = 8000
        protocol = "TCP"
      }
    }
  }
}
