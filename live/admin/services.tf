
locals {
  services = [
    "dns.googleapis.com",
    "domains.googleapis.com",
    "certificatemanager.googleapis.com",
    "cloudresourcemanager.googleapis.com",
    "compute.googleapis.com",
    "iam.googleapis.com",
    "iamcredentials.googleapis.com",
    "networkservices.googleapis.com",
    "servicemanagement.googleapis.com",
  ]
}

resource "google_project_service" "services" {
  for_each                   = toset(local.services)
  project                    = var.project
  service                    = each.value
  disable_dependent_services = false
  disable_on_destroy         = false
}
