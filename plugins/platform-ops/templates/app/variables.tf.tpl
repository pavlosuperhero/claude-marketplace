variable "region" {
  type    = string
  default = "{{AWS_REGION}}"
}

variable "desired_count" {
  type    = number
  default = 1
}
