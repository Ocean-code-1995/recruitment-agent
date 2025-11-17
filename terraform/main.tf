# Create or adopt the project WITHOUT billing
resource "google_project" "project" {
  project_id = var.project_id
  name       = var.project_name

  # If you're under an Organization/Folder and want to place it there,
  # we can add folder_id/org_id later. For hackathon, keep it simple.
  deletion_policy = "ABANDON"
}

# Enable Gmail API (no billing required)
resource "google_project_service" "gmail" {
  project            = google_project.project.project_id
  service            = "gmail.googleapis.com"
  disable_on_destroy = false

  timeouts {
    create = "30m"
    update = "30m"
    delete = "30m"
  }

  depends_on = [
    google_project.project
  ]
}

# Enable the Google Calendar API
resource "google_project_service" "calendar_api" {
  project = google_project.project.project_id
  service = "calendar.googleapis.com"
  disable_on_destroy = false
}


# Grants your user account the minimal roles needed to manage API services and 
# avoid “permission denied” errors when enabling APIs.
resource "google_project_iam_member" "user_editor" {
  project = google_project.project.project_id
  role    = "roles/editor"
  member  = "user:${var.user_email}"
}

resource "google_project_iam_member" "user_serviceusage_admin" {
  project = google_project.project.project_id
  role    = "roles/serviceusage.serviceUsageAdmin"
  member  = "user:${var.user_email}"
}

# Give yourself full Owner access for full API + IAM control
resource "google_project_iam_member" "user_owner" {
  project = google_project.project.project_id
  role    = "roles/owner"
  member  = "user:${var.user_email}"
}
