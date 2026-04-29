resource "google_artifact_registry_repository" "images" {
  project       = var.project
  location      = var.region
  repository_id = var.env
  format        = "DOCKER"
  description   = "Docker images for ${var.env}"
}

resource "google_artifact_registry_repository_iam_member" "webserver_reader" {
  project    = var.project
  location   = var.region
  repository = google_artifact_registry_repository.images.name
  role       = "roles/artifactregistry.reader"
  member     = "serviceAccount:${google_service_account.lunch.email}"
}
