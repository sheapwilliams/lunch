locals {
  quad_zero_cidr_range             = "0.0.0.0/0"
  private_google_access_cidr_range = "199.36.153.8/30"
  restricted_api_access_cidr_range = "199.36.153.4/30"
  health_check_cidr_range          = "35.191.0.0/16"
  health_check2_cidr_range         = "130.211.0.0/22"
  iap_tunnel_range                 = "35.235.240.0/20"

  private_google_access_dns_zones = {
    pkg-dev = {
      dns = "pkg.dev."
      ips = ["199.36.153.4", "199.36.153.5", "199.36.153.6", "199.36.153.7"]
    }
    gcr-io = {
      dns = "gcr.io."
      ips = ["199.36.153.4", "199.36.153.5", "199.36.153.6", "199.36.153.7"]
    }
    googleapis-com = {
      dns = "googleapis.com."
      ips = ["199.36.153.8", "199.36.153.9", "199.36.153.10", "199.36.153.11"]
    }
  }
}

resource "google_compute_network" "vpc" {
  name                                      = var.env
  project                                   = var.project
  auto_create_subnetworks                   = false
  routing_mode                              = "GLOBAL"
  delete_default_routes_on_create           = true
  network_firewall_policy_enforcement_order = "BEFORE_CLASSIC_FIREWALL"
}

resource "google_compute_subnetwork" "subnet" {
  name                     = "${var.env}-subnet"
  project                  = var.project
  network                  = google_compute_network.vpc.id
  ip_cidr_range            = "10.10.10.0/24"
  region                   = var.region
  private_ip_google_access = true
}

resource "google_compute_firewall" "allow_private_google_access_egress" {
  name        = "${var.env}-allow-private-google-access-egress"
  project     = var.project
  network     = google_compute_network.vpc.id
  direction   = "EGRESS"
  description = "Allow egress to private Google APIs"
  priority    = 4000

  destination_ranges = [
    local.private_google_access_cidr_range,
  ]

  allow {
    protocol = "tcp"
    ports    = ["443"]
  }
}

resource "google_compute_firewall" "allow_health_check_ingress" {
  name        = "${var.env}-allow-health-check-ingress"
  project     = var.project
  network     = google_compute_network.vpc.id
  description = "Allow health check ingress"
  direction   = "INGRESS"
  priority    = 10000

  source_ranges = [
    local.health_check_cidr_range,
    local.health_check2_cidr_range,
  ]

  allow {
    protocol = "tcp"
    ports    = ["8000"]
  }
}

resource "google_compute_firewall" "allow_ssh_https_ingress" {
  name        = "${var.env}-allow-ssh-https-ingress"
  project     = var.project
  network     = google_compute_network.vpc.id
  direction   = "INGRESS"
  description = "Allow SSH and HTTPS ingress from anywhere"
  priority    = 4000

  source_ranges = [
    "0.0.0.0/0",
  ]

  allow {
    protocol = "tcp"
    ports    = ["22", "443"]
  }
}

resource "google_compute_firewall" "allow_egress" {
  name        = "${var.env}-allow-egress"
  project     = var.project
  network     = google_compute_network.vpc.id
  direction   = "EGRESS"
  description = "Allow egress to all"
  priority    = 4000

  source_ranges = [
    google_compute_subnetwork.subnet.ip_cidr_range,
  ]

  allow {
    protocol = "icmp"
  }

  allow {
    protocol = "tcp"
    ports    = ["0-65535"]
  }

  allow {
    protocol = "udp"
    ports    = ["0-65535"]
  }
}

resource "google_compute_route" "quad_zero" {
  name             = "${var.env}-quad-zero"
  project          = var.project
  network          = google_compute_network.vpc.id
  description      = "Route to allow all traffic to public internet"
  dest_range       = local.quad_zero_cidr_range
  next_hop_gateway = "default-internet-gateway"
  priority         = 6000
}

resource "google_dns_managed_zone" "private_google_access" {
  for_each = { for k, v in local.private_google_access_dns_zones : k => v }

  name       = each.key
  project    = var.project
  dns_name   = each.value.dns
  visibility = "private"

  private_visibility_config {
    networks {
      network_url = google_compute_network.vpc.id
    }
  }
}

resource "google_dns_record_set" "cnames" {
  for_each = { for k, v in google_dns_managed_zone.private_google_access : k => v }

  name         = "*.${each.value.dns_name}"
  project      = var.project
  managed_zone = each.value.name
  type         = "CNAME"
  ttl          = 300
  rrdatas      = [each.value.dns_name]
}

resource "google_dns_record_set" "a" {
  for_each = { for k, v in google_dns_managed_zone.private_google_access : k => v }

  name         = each.value.dns_name
  project      = var.project
  managed_zone = each.value.name
  type         = "A"
  ttl          = 300
  rrdatas      = local.private_google_access_dns_zones[each.key].ips
}
  
resource "google_compute_router" "router" {
  name    = "${var.env}-router"
  project = var.project
  region  = var.region
  network = google_compute_network.vpc.id

  bgp {
    asn = 64514
  }
}

resource "google_compute_address" "nat" {
  count   = 2
  name    = "${var.env}-nat-${count.index}"
  project = var.project
  region  = var.region
}

resource "google_compute_router_nat" "nat" {
  name    = "${var.env}-nat"
  project = var.project
  region  = var.region
  router  = google_compute_router.router.name

  nat_ip_allocate_option = "MANUAL_ONLY"
  nat_ips                = google_compute_address.nat.*.self_link

  source_subnetwork_ip_ranges_to_nat = "ALL_SUBNETWORKS_ALL_IP_RANGES"

  log_config {
    enable = true
    filter = "ERRORS_ONLY"
  }
}

resource "google_compute_network_firewall_policy" "fqdn_policy" {
  name        = "${var.env}-fqdn-policy"
  project     = var.project
  description = "Firewall policy for FQDNs"
}

resource "google_compute_network_firewall_policy_rule" "fqdn_rule" {
  firewall_policy = google_compute_network_firewall_policy.fqdn_policy.id
  description     = "Firewall rule for FQDNs"
  priority        = 1000
  project         = var.project
  action          = "allow"
  direction       = "EGRESS"

  target_service_accounts = [google_service_account.lunch.email]

  match {
    dest_fqdns = [
      "packages.cloud.google",
      "releases.hashicorp.com",
      "checkpoint-api.hashicorp.com",
      "get.docker.com",
      "download.docker.com",
      "contracts.canonical.com",
      "security.ubuntu.com",
      "archive.ubuntu.com",
      "esm.ubuntu.com",
    ]

    layer4_configs {
      ip_protocol = "tcp"
    }
  }
}

resource "google_compute_network_firewall_policy_association" "fqdn_policy_association" {
  name              = "${var.env}-fqdn-policy-association"
  project           = var.project
  firewall_policy   = google_compute_network_firewall_policy.fqdn_policy.id
  attachment_target = google_compute_network.vpc.id
}

resource "google_compute_backend_service" "webserver" {
  provider              = google-beta
  name                  = "${var.env}-webserver-backend"
  project               = var.project
  protocol              = "HTTPS"
  timeout_sec           = 30
  health_checks         = [google_compute_health_check.webserver.id]
  load_balancing_scheme = "EXTERNAL_MANAGED"

  backend {
    group          = google_compute_network_endpoint_group.webserver.id
    balancing_mode = "RATE"
    max_rate       = 100
  }
}

