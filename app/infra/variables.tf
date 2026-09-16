variable "project_id" {
  type    = string
  default = "promptish-prod"
}

variable "region" {
  type    = string
  default = "us-central1"
}

variable "service_name" {
  type    = string
  default = "primary-care-atlas"
}

variable "repository" {
  type    = string
  default = "primary-care-atlas"
}

variable "image_tag" {
  type    = string
  default = "latest"
}

variable "allow_unauthenticated" {
  description = "Make the Cloud Run service publicly invokable (a public data explorer)."
  type        = bool
  default     = true
}
