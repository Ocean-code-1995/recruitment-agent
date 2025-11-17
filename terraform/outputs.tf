output "project_id" {
  value       = google_project.project.project_id
  description = "Project ID"
}

output "project_number" {
  value       = google_project.project.number
  description = "Project number"
}

output "gmail_api_service" {
  value       = google_project_service.gmail.service
  description = "Gmail API service name (resource exists ⇒ enabled)"
}

output "console_calendar_api_url" {
  value = "https://console.cloud.google.com/apis/library/calendar.googleapis.com?project=${google_project.project.project_id}"
}



# Handy console URLs to complete the unavoidable manual OAuth bits:
output "console_oauth_consent_screen_url" {
  value       = "https://console.cloud.google.com/apis/credentials/consent?project=${google_project.project.project_id}"
  description = "Configure OAuth consent (External + add your email as test user, add gmail.modify scope)."
}

output "console_oauth_credentials_url" {
  value       = "https://console.cloud.google.com/apis/credentials?project=${google_project.project.project_id}"
  description = "Create OAuth 2.0 Client ID (Application type: Desktop app)."
}
