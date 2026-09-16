provider "google" {
  project = var.project_id
  region  = var.region
}

locals {
  image = "${var.region}-docker.pkg.dev/${var.project_id}/${var.repository}/${var.service_name}:${var.image_tag}"
}

# Already enabled on promptish-prod; declared so a fresh project is self-sufficient.
resource "google_project_service" "run" {
  service            = "run.googleapis.com"
  disable_on_destroy = false
}

resource "google_project_service" "artifactregistry" {
  service            = "artifactregistry.googleapis.com"
  disable_on_destroy = false
}

# Docker image registry for this app.
resource "google_artifact_registry_repository" "repo" {
  location      = var.region
  repository_id = var.repository
  format        = "DOCKER"
  description   = "Container images for the Primary Care Atlas app"

  depends_on = [google_project_service.artifactregistry]
}

# One service: the FastAPI container serves the SPA + API + the committed DuckDB.
resource "google_cloud_run_v2_service" "app" {
  name                = var.service_name
  location            = var.region
  ingress             = "INGRESS_TRAFFIC_ALL"
  deletion_protection = false

  template {
    containers {
      image = local.image

      ports {
        container_port = 8080
      }

      resources {
        limits = {
          cpu    = "1"
          memory = "1Gi"
        }
      }
    }

    scaling {
      min_instance_count = 0
      max_instance_count = 2
    }
  }

  depends_on = [
    google_project_service.run,
    google_artifact_registry_repository.repo,
  ]
}

# Public access (optional): allow unauthenticated invocations.
resource "google_cloud_run_v2_service_iam_member" "public" {
  count = var.allow_unauthenticated ? 1 : 0

  project  = var.project_id
  location = var.region
  name     = google_cloud_run_v2_service.app.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}
