output "webserver_ip" {
  description = "Static IP address for the load balancer. Point your DNS A record here."
  value       = google_compute_global_address.webserver_ip.address
}

output "ssl_certificate_name" {
  description = "Name of the managed SSL certificate. Use with gcloud to check provisioning status."
  value       = google_compute_managed_ssl_certificate.ingress_certificate.name
}
