#!/usr/bin/env bash
set -euo pipefail

# Interactive gcloud + ADC setup for Gmail MCP.

# --- sanity: require gcloud ---
if ! command -v gcloud >/dev/null 2>&1; then
  echo "Error: gcloud CLI not found. Install Google Cloud SDK and retry."
  exit 1
fi

read -r -p "Your Google account email: " ACCOUNT_EMAIL
read -r -p "Target GCP Project ID (e.g., gradio-hackathon-25): " PROJECT_ID

# --- minimal validation ---
# Project ID: 6–30 chars, starts with letter, lowercase letters/digits/hyphens.
if [[ ! "$PROJECT_ID" =~ ^[a-z][a-z0-9-]{5,29}$ ]]; then
  echo "Error: PROJECT_ID must start with a letter, be 6-30 chars, and use only lowercase letters, digits, and hyphens."
  exit 1
fi
# Basic email sanity check
if [[ ! "$ACCOUNT_EMAIL" =~ ^[^@]+@[^@]+\.[^@]+$ ]]; then
  echo "Error: That doesn't look like a valid email."
  exit 1
fi

echo ""
echo "---------------- Confirmation ----------------"
echo "  Account Email : ${ACCOUNT_EMAIL}"
echo "  Project ID    : ${PROJECT_ID}"
echo "------------------------------------------------"
read -r -p "Proceed to authenticate and set config? [y/N]: " CONFIRM
CONFIRM=${CONFIRM:-N}
if [[ ! "$CONFIRM" =~ ^[Yy]$ ]]; then
  echo "Aborted."
  exit 0
fi

# Auth for gcloud and ADC (opens browser windows)
echo "🔑 Logging into GCP..."
gcloud auth login "${ACCOUNT_EMAIL}" --update-adc
echo "🔐 Setting up Application Default Credentials (ADC)..."
gcloud auth application-default login

# Set defaults (safe even if project doesn't exist yet)
echo "📂 Setting gcloud config for account and project..."
gcloud config set core/account "${ACCOUNT_EMAIL}"
echo "📦 Setting project: $PROJECT_ID"
gcloud config set project "${PROJECT_ID}"

echo "✅ gcloud & ADC configured for ${ACCOUNT_EMAIL} / project ${PROJECT_ID}"

