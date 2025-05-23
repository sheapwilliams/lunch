
resource "google_compute_global_address" "webserver_ip" {
  name         = var.env
  project      = var.project
  address_type = "EXTERNAL"
  description  = "Static IP for webserver"
}

resource "google_compute_backend_service" "webserver" {
  provider              = google-beta
  name                  = "${var.env}-webserver-backend"
  project               = var.project
  protocol              = "HTTP"
  port_name             = "http"
  timeout_sec           = 30
  health_checks         = [google_compute_health_check.webserver.id]
  load_balancing_scheme = "EXTERNAL_MANAGED"

  backend {
    group          = google_compute_instance_group.webserver.id
    balancing_mode = "RATE"
    max_rate       = 100
  }
}


resource "google_compute_url_map" "webserver_url_map" {
  name            = "${var.env}-webserver-url-map"
  project         = var.project
  default_service = google_compute_backend_service.webserver.id
}

resource "google_compute_managed_ssl_certificate" "ingress_certificate" {
  name    = "${var.env}-ingress-certificate"
  project = var.project

  managed {
    domains = ["${var.env}.${data.google_dns_managed_zone.dns_zone.dns_name}"]
  }
}

resource "google_compute_target_https_proxy" "webserver_https_proxy" {
  name    = "${var.env}-webserver-https-proxy"
  project = var.project
  url_map = google_compute_url_map.webserver_url_map.id
  ssl_certificates = [
    google_compute_managed_ssl_certificate.ingress_certificate.id
  ]
}

resource "google_compute_global_forwarding_rule" "webserver_forwarding_rule" {
  name                  = "${var.env}-ssl-forwarding-rule"
  project               = var.project
  ip_protocol           = "TCP"
  port_range            = "443-443"
  load_balancing_scheme = "EXTERNAL_MANAGED"
  target                = google_compute_target_https_proxy.webserver_https_proxy.id
  ip_address            = google_compute_global_address.webserver_ip.id
}

resource "google_dns_record_set" "ingress_record_set" {
  name         = "${var.env}.${data.google_dns_managed_zone.dns_zone.dns_name}"
  project      = var.project
  type         = "A"
  ttl          = 300
  managed_zone = data.google_dns_managed_zone.dns_zone.name
  rrdatas      = [google_compute_global_forwarding_rule.webserver_forwarding_rule.ip_address]
}

resource "google_dns_record_set" "redirect_to_cppnow_org" {
  name         = "${data.google_dns_managed_zone.dns_zone.dns_name}"
  project      = var.project
  type         = "A"
  ttl          = 300
  managed_zone = data.google_dns_managed_zone.dns_zone.name
  rrdatas      = [google_compute_global_forwarding_rule.webserver_forwarding_rule.ip_address]
}

resource "google_dns_record_set" "redirect_schedule_to_cppnow_org" {
  name         = "schedule.${data.google_dns_managed_zone.dns_zone.dns_name}"
  project      = var.project
  type         = "A"
  ttl          = 300
  managed_zone = data.google_dns_managed_zone.dns_zone.name
  rrdatas      = [google_compute_global_forwarding_rule.webserver_forwarding_rule.ip_address]
}
