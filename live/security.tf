locals {
  # Stripe webhook source IPs — update when Stripe rotates them.
  # Current list: https://stripe.com/files/ips/ips_webhooks.txt
  stripe_webhook_ips = [
    "3.18.12.63",
    "3.130.192.231",
    "13.235.14.237",
    "13.235.122.149",
    "18.211.135.69",
    "35.154.171.200",
    "52.15.183.38",
    "54.88.130.119",
    "54.88.130.237",
    "54.187.174.169",
    "54.187.205.235",
    "54.187.216.72",
    "35.157.207.129",
    "3.69.109.8",
    "3.120.168.93",
  ]

  # SRC_IPS_V1 supports up to 10 ranges per rule; split the list accordingly.
  stripe_ip_chunks = chunklist(local.stripe_webhook_ips, 10)
}

resource "google_compute_security_policy" "webhook_guard" {
  name    = "${var.env}-webhook-guard"
  project = var.project

  # Allow Stripe IPs unconditionally — these rules fire before the /webhook
  # deny below, so Stripe can always reach the endpoint. SRC_IPS_V1 is the
  # purpose-built IP-matching mode and has no CEL expression limit.
  dynamic "rule" {
    for_each = local.stripe_ip_chunks
    content {
      priority    = 1000 + rule.key
      action      = "allow"
      description = "Allow Stripe webhook IPs (group ${rule.key + 1})"

      match {
        versioned_expr = "SRC_IPS_V1"
        config {
          src_ip_ranges = rule.value
        }
      }
    }
  }

  # Block all other traffic to /webhook.
  rule {
    priority    = 2000
    action      = "deny(403)"
    description = "Block non-Stripe traffic to /webhook"

    match {
      expr {
        expression = "request.path == '/webhook'"
      }
    }
  }

  # Default: allow everything else.
  rule {
    priority    = 2147483647
    action      = "allow"
    description = "Default allow"

    match {
      versioned_expr = "SRC_IPS_V1"
      config {
        src_ip_ranges = ["*"]
      }
    }
  }
}
