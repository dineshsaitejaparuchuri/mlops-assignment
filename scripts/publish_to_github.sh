#!/usr/bin/env bash
set -euo pipefail

for cmd in git gh python; do
  command -v "$cmd" >/dev/null 2>&1 || {
    echo "Required command '$cmd' is missing. Install it and retry." >&2
    exit 1
  }
done
gh auth status >/dev/null

read -r -p "Repository name [heart-mlops-assignment-1]: " repo_name
repo_name="${repo_name:-heart-mlops-assignment-1}"
[[ "$repo_name" =~ ^[A-Za-z0-9_.-]+$ ]] || { echo "Invalid repository name." >&2; exit 2; }
read -r -p "Visibility: private or public? [private]: " visibility
visibility="${visibility:-private}"
case "$visibility" in private|public) ;; *) echo "Enter private or public." >&2; exit 2 ;; esac
read -r -p "Student name (required): " student_name
[[ -n "$student_name" ]] || { echo "Student name cannot be blank." >&2; exit 2; }
read -r -p "Student roll number (required): " roll_number
[[ -n "$roll_number" ]] || { echo "Roll number cannot be blank." >&2; exit 2; }

owner="$(gh api user --jq '.login')"
repo_url="https://github.com/${owner}/${repo_name}"
export HEART_MLOPS_REPO_URL="$repo_url"
export HEART_MLOPS_STUDENT_NAME="$student_name"
export HEART_MLOPS_ROLL_NUMBER="$roll_number"

python -c 'import reportlab, matplotlib, pandas, sklearn, joblib, PIL' || {
  echo "Report dependencies missing; activate the venv and run pip install -r requirements-notebooks.txt." >&2
  exit 1
}
python scripts/build_report.py

if [ ! -d .git ]; then git init -b main; fi
branch="$(git branch --show-current)"
if [ "$branch" != "main" ]; then git branch -M main; fi
git add -A
if ! git rev-parse --verify HEAD >/dev/null 2>&1; then
  git config user.name >/dev/null || { echo "Set git user.name first." >&2; exit 1; }
  git config user.email >/dev/null || { echo "Set git user.email first." >&2; exit 1; }
  git commit -m "Initial MLOps assignment submission"
elif ! git diff --cached --quiet; then
  git commit -m "Prepare MLOps assignment submission"
fi
gh repo create "$repo_name" --source . --remote origin --push "--${visibility}"
echo "Repository created and pushed: $repo_url"
echo "Next: open the Actions tab and resolve any failing ci workflow before submission."
