output "service_url" {
  description = "Public URL of the Cloud Run service."
  value       = google_cloud_run_v2_service.app.uri
}

output "image" {
  description = "Fully-qualified image the service runs."
  value       = local.image
}
