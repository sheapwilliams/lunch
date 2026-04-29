variable "project" {
  type    = string
  default = "lunch-cppnow"
}

variable "region" {
  type    = string
  default = "us-central1"
}

variable "env" {
  type    = string
  default = "lunch"
}

variable "domain" {
  type        = string
  description = "Fully-qualified domain name for the app. Must match the external DNS A record."
  default     = "lunch.cppnow.org"
}
