resource "google_compute_instance" "webserver" {
  name         = var.env
  project      = var.project
  zone         = "${var.region}-c"
  description  = "Web server for lunch"
  machine_type = "e2-medium"
#   machine_type = "e2-standard-2"
  labels       = {}

  metadata = {
    google-logging-enabled = true
    enable-oslogin         = true
    user-data              = file("cloud-init.yaml")
  }

  boot_disk {
    initialize_params {
      image = "ubuntu-os-cloud/ubuntu-2404-lts-amd64"
      size  = 20
    }
  }

  network_interface {
    subnetwork         = google_compute_subnetwork.subnet.id
    subnetwork_project = var.project
  }

  service_account {
    email  = google_service_account.lunch.email
    scopes = ["cloud-platform"]
  }
}

resource "google_compute_health_check" "webserver" {
  name                = "${var.env}-health-check"
  project             = var.project
  check_interval_sec  = 5
  timeout_sec         = 5
  healthy_threshold   = 2
  unhealthy_threshold = 2

  http_health_check {
    port         = 8000
    request_path = "/"
  }
}

resource "google_compute_instance_group" "webserver" {
  name        = "${var.env}-webservers"
  description = "Webserver instance group"

  instances = [
    google_compute_instance.webserver.id,
  ]

  named_port {
    name = "http"
    port = "8000"
  }

  zone = "${var.region}-c"
}
