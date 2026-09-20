#!/usr/bin/env bash
#
# Creates the API key Watch Worth It needs, in your own Google Cloud account.
#
#   ./setup-api-key.sh                     # new project, both APIs, one key
#   ./setup-api-key.sh --project my-proj   # reuse a project you already have
#   ./setup-api-key.sh --yes               # skip the confirmation prompt
#
# Everything it creates is free: projects cost nothing, and neither the Fact
# Check Tools API nor the YouTube Data API requires a billing account.

set -euo pipefail

PROJECT_ID=""
KEY_NAME="Watch Worth It"
ASSUME_YES=0
SERVICES=(factchecktools.googleapis.com youtube.googleapis.com)

while [[ $# -gt 0 ]]; do
  case "$1" in
    --project) PROJECT_ID="${2:-}"; shift 2 ;;
    --name) KEY_NAME="${2:-}"; shift 2 ;;
    --yes|-y) ASSUME_YES=1; shift ;;
    -h|--help) awk 'NR>1 && /^#/ { sub(/^# ?/, ""); print; next } NR>1 { exit }' "$0"; exit 0 ;;
    *) echo "unknown option: $1" >&2; exit 2 ;;
  esac
done

say() { printf '\n\033[1m%s\033[0m\n' "$*"; }
note() { printf '  %s\n' "$*"; }
die() { printf '\n\033[31m%s\033[0m\n' "$*" >&2; exit 1; }

# ---------------------------------------------------------------- gcloud ----

if ! command -v gcloud >/dev/null 2>&1; then
  die "The gcloud CLI is not installed.

Install it, then run this again:
  macOS      brew install --cask google-cloud-sdk
  Linux      https://cloud.google.com/sdk/docs/install
  Windows    https://cloud.google.com/sdk/docs/install (or use WSL)

Or do it by hand in the browser - see README.md, 'Getting the API key'."
fi

ACCOUNT="$(gcloud auth list --filter=status:ACTIVE --format='value(account)' 2>/dev/null | head -1)"
if [[ -z "$ACCOUNT" ]]; then
  say "Signing in to Google (a browser window will open)"
  gcloud auth login
  ACCOUNT="$(gcloud auth list --filter=status:ACTIVE --format='value(account)' | head -1)"
  [[ -n "$ACCOUNT" ]] || die "Sign-in did not complete."
fi

# Some gcloud versions still keep api-keys under the beta track.
KEYS_CMD=(gcloud services api-keys)
if ! gcloud services api-keys --help >/dev/null 2>&1; then
  KEYS_CMD=(gcloud beta services api-keys)
  "${KEYS_CMD[@]}" --help >/dev/null 2>&1 || die "This gcloud has no 'services api-keys' command. Run: gcloud components update"
fi

# --------------------------------------------------------------- confirm ----

NEW_PROJECT=0
if [[ -z "$PROJECT_ID" ]]; then
  NEW_PROJECT=1
  PROJECT_ID="watch-worth-it-$(date +%s | tail -c 7)$(printf '%03d' $((RANDOM % 1000)))"
fi

say "About to do this as $ACCOUNT"
if [[ $NEW_PROJECT -eq 1 ]]; then
  note "create a new Cloud project            $PROJECT_ID"
else
  note "use your existing project             $PROJECT_ID"
fi
note "enable Fact Check Tools API           factchecktools.googleapis.com"
note "enable YouTube Data API v3            youtube.googleapis.com"
note "create one API key restricted to those two APIs, named \"$KEY_NAME\""
note ""
note "No billing account is involved. Nothing here costs money."

if [[ $ASSUME_YES -eq 0 ]]; then
  printf '\nGo ahead? [y/N] '
  read -r reply
  [[ "$reply" =~ ^[Yy]$ ]] || die "Stopped. Nothing was created."
fi

# --------------------------------------------------------------- project ----

if [[ $NEW_PROJECT -eq 1 ]]; then
  say "Creating project $PROJECT_ID"
  gcloud projects create "$PROJECT_ID" --name="Watch Worth It" --quiet || die \
"Could not create the project.

If your Google account belongs to an organization that blocks project creation,
make one in the console or ask an admin, then re-run with:
  ./setup-api-key.sh --project THEIR-PROJECT-ID"
else
  gcloud projects describe "$PROJECT_ID" --format='value(projectId)' >/dev/null 2>&1 \
    || die "No project called '$PROJECT_ID' is visible to $ACCOUNT."
fi

say "Enabling the APIs (this takes a moment)"
gcloud services enable "${SERVICES[@]}" --project="$PROJECT_ID" || die \
"Could not enable the APIs on $PROJECT_ID. Check that the account has permission."
note "done"

# ------------------------------------------------------------------- key ----

say "Creating the API key"
KEY_RESOURCE="$("${KEYS_CMD[@]}" create \
  --display-name="$KEY_NAME" \
  --api-target=service=factchecktools.googleapis.com \
  --api-target=service=youtube.googleapis.com \
  --project="$PROJECT_ID" \
  --format='value(response.name)' 2>/dev/null || true)"

if [[ -z "$KEY_RESOURCE" ]]; then
  # Older gcloud prints the operation rather than the key; find it by name.
  KEY_RESOURCE="$("${KEYS_CMD[@]}" list --project="$PROJECT_ID" \
    --filter="displayName=\"$KEY_NAME\"" --format='value(name)' | head -1)"
fi
[[ -n "$KEY_RESOURCE" ]] || die "The key was not created. Check the console: https://console.cloud.google.com/apis/credentials?project=$PROJECT_ID"

API_KEY="$("${KEYS_CMD[@]}" get-key-string "$KEY_RESOURCE" --format='value(keyString)')"
[[ -n "$API_KEY" ]] || die "Created the key but could not read it back. It is in the console: https://console.cloud.google.com/apis/credentials?project=$PROJECT_ID"

# ---------------------------------------------------------------- verify ----

say "Checking the key against the live API"
VERIFIED=0
for attempt in 1 2 3 4 5; do
  BODY="$(curl -sS --max-time 20 \
    "https://factchecktools.googleapis.com/v1alpha1/claims:search?query=moon%20landing&languageCode=en&key=$API_KEY" 2>/dev/null || true)"
  if [[ "$BODY" == *'"claims"'* || "$BODY" == "{}" ]]; then
    VERIFIED=1
    break
  fi
  note "not ready yet (attempt $attempt of 5) - new keys take a minute to propagate"
  sleep 6
done

echo
if [[ $VERIFIED -eq 1 ]]; then
  printf '\033[32m%s\033[0m\n' "The key works."
else
  printf '\033[33m%s\033[0m\n' "The key was created but has not answered yet."
  note "This is usually propagation. Wait a minute and press Test in the extension's options."
  note "Last response: $(printf '%s' "$BODY" | head -c 300)"
fi

cat <<EOF

  Your API key:

      $API_KEY

  Paste it into the extension's options page - both fields, since this one key
  covers the Fact Check Tools API and the YouTube Data API - and press Test.

  Project:  https://console.cloud.google.com/apis/credentials?project=$PROJECT_ID
EOF
