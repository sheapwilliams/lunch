terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 6.12"
    }
  }
}

provider "google" {
  project = var.project
  region  = var.region

  default_labels = {
    owner = "admin-cppnow2025"
  }
}
