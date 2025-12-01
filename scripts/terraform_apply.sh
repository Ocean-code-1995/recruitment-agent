#!/usr/bin/env bash
set -euo pipefail

# Interactive Terraform apply for Gmail MCP (no-billing setup).
# - Prompts for project_id, project_name, user_email
# - Falls back to terraform/terraform.tfvars if inputs are blank
# - Auto-imports an existing GCP project to avoid 409 alreadyExists
# - Applies the stack

# --- resolve paths ---
script_dir="$(cd -- "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"
TF_DIR="${TF_DIR:-${script_dir}/../terraform}"
TFVARS_PATH="${TFVARS_PATH:-${TF_DIR}/terraform.tfvars}"

# --- helpers ---
read_tfvar() {
  # Extract a simple "key = \"value\"" from terraform.tfvars (no HCL expressions)
  local key="$1"
  local file="$2"
  [[ -f "$file" ]] || { echo ""; return 0; }
  sed -nE "s/^[[:space:]]*${key}[[:space:]]*=[[:space:]]*\"([^\"]+)\"[[:space:]]*$/\1/p" "$file" | head -n1
}

# load defaults from tfvars (if present)
DEFAULT_PROJECT_ID="$(read_tfvar project_id "$TFVARS_PATH")"
DEFAULT_PROJECT_NAME="$(read_tfvar project_name "$TFVARS_PATH")"
DEFAULT_USER_EMAIL="$(read_tfvar user_email "$TFVARS_PATH")"

# prompt with defaults
read -r -p "GCP Project ID [${DEFAULT_PROJECT_ID:-none}]: " PROJECT_ID
read -r -p "Project Name [${DEFAULT_PROJECT_NAME:-none}]: " PROJECT_NAME
read -r -p "Your Google Account Email [${DEFAULT_USER_EMAIL:-none}]: " USER_EMAIL

# use defaults if blank
PROJECT_ID="${PROJECT_ID:-$DEFAULT_PROJECT_ID}"
PROJECT_NAME="${PROJECT_NAME:-$DEFAULT_PROJECT_NAME}"
USER_EMAIL="${USER_EMAIL:-$DEFAULT_USER_EMAIL}"

# validate presence
if [[ -z "${PROJECT_ID}" || -z "${PROJECT_NAME}" || -z "${USER_EMAIL}" ]]; then
  echo "Error: project_id, project_name, and user_email are required (either input or terraform.tfvars defaults)."
  exit 1
fi

# minimal validation
if [[ ! "$PROJECT_ID" =~ ^[a-z][a-z0-9-]{5,29}$ ]]; then
  echo "Error: PROJECT_ID must start with a letter, be 6-30 chars, and use only lowercase letters, digits, and hyphens."
  exit 1
fi
if [[ ! "$USER_EMAIL" =~ ^[^@]+@[^@]+\.[^@]+$ ]]; then
  echo "Error: USER_EMAIL doesn't look like a valid email."
  exit 1
fi

# verify TF dir & files
if [[ ! -d "$TF_DIR" ]]; then
  echo "Error: Terraform directory not found: $TF_DIR"
  exit 1
fi
if ! ls "$TF_DIR"/*.tf >/dev/null 2>&1; then
  echo "Error: No .tf files found in $TF_DIR"
  exit 1
fi

# summary
echo ""
echo "──────────────── Terraform Apply ────────────────"
echo "  Terraform dir : ${TF_DIR}"
echo "  tfvars path   : ${TFVARS_PATH}"
echo "  Project ID    : ${PROJECT_ID}"
echo "  Project Name  : ${PROJECT_NAME}"
echo "  User Email    : ${USER_EMAIL}"
echo "─────────────────────────────────────────────────"
read -r -p "Proceed with terraform apply? [y/N]: " CONFIRM
CONFIRM=${CONFIRM:-N}
if [[ ! "$CONFIRM" =~ ^[Yy]$ ]]; then
  echo "Aborted."
  exit 0
fi

cd "$TF_DIR"

echo "Initializing Terraform…"
terraform init -input=false

# If project already exists, import into state to avoid 409 alreadyExists
if command -v gcloud >/dev/null 2>&1; then
  if gcloud projects describe "$PROJECT_ID" >/dev/null 2>&1; then
    echo "Project '${PROJECT_ID}' exists. Importing into Terraform state (idempotent)…"
    terraform import -input=false google_project.project "$PROJECT_ID" || true
  else
    echo "Project '${PROJECT_ID}' does not exist yet. Terraform will create it."
  fi
else
  echo "Warning: gcloud not found; skipping existence check. If the project exists, apply may fail with 409."
fi

echo "Applying Terraform…"
terraform apply -auto-approve \
  -var="project_id=${PROJECT_ID}" \
  -var="project_name=${PROJECT_NAME}" \
  -var="user_email=${USER_EMAIL}"

echo "✅ Successfully applied Terraform changes."
echo "📝 Remaining manual setup steps for Gmail and Calendar MCP servers:"
echo "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~"
echo "   → Open OAuth consent screen:      https://console.cloud.google.com/apis/credentials/consent?project=${PROJECT_ID}"
echo "   → Create Desktop OAuth client(s): https://console.cloud.google.com/apis/credentials?project=${PROJECT_ID}"
echo "      - ~/.gmail-mcp/credentials.json"
echo "      - ~/.calendar-mcp/credentials.json"

