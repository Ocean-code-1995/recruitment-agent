variable "project_id" {
  type        = string
  description = "Project ID to create or reuse"
  default     = "gradio-hackathon-25"
}

variable "project_name" {
  type        = string
  description = "Human-friendly project name"
  default     = "Gradio Agent MCP Hackathon 25"
}

variable "region" {
  type        = string
  default     = "europe-west3"
  description = "Default region"
}

variable "user_email" {
  type        = string
  description = "Your Google account email to grant project roles to"
  default     = "hr.cjordan.agent.hack.winter25@gmail.com"
}
