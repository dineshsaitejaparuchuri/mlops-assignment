$ErrorActionPreference = 'Stop'

function Require-Command([string]$Name, [string]$InstallHint) {
    if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
        throw "$Name is required. $InstallHint"
    }
}

Require-Command 'git' 'Install Git for Windows and retry.'
Require-Command 'gh' "Install GitHub CLI (gh), run 'gh auth login', and retry."
# Prefer the Windows Python launcher, because 'python' can resolve to the Microsoft Store shim.
$pythonCmd = Get-Command 'python' -ErrorAction SilentlyContinue
$pyCmd = Get-Command 'py' -ErrorAction SilentlyContinue
if ($pythonCmd) { $pythonExe = $pythonCmd.Source; $pythonArgs = @() }
elseif ($pyCmd) { $pythonExe = $pyCmd.Source; $pythonArgs = @('-3') }
else { throw 'Python is required. Install Python 3.11+ and retry.' }

# This call fails early if the user has not authenticated or if the token is expired.
gh auth status | Out-Null
if ($LASTEXITCODE -ne 0) { throw "GitHub CLI is not authenticated. Run 'gh auth login' and retry." }

$repoName = Read-Host 'Repository name [heart-mlops-assignment-1]'
if ([string]::IsNullOrWhiteSpace($repoName)) { $repoName = 'heart-mlops-assignment-1' }
if ($repoName -notmatch '^[A-Za-z0-9_.-]+$') { throw 'Repository name can contain only letters, digits, dots, hyphens and underscores.' }
$visibility = Read-Host 'Visibility: private or public? [private]'
if ([string]::IsNullOrWhiteSpace($visibility)) { $visibility = 'private' }
$visibility = $visibility.ToLowerInvariant()
if ($visibility -notin @('private', 'public')) { throw 'Enter private or public. No repository was created.' }

$studentName = Read-Host 'Student name (required for the final report)'
if ([string]::IsNullOrWhiteSpace($studentName)) { throw 'Student name cannot be blank; no repository was created.' }
$rollNumber = Read-Host 'Student roll number (required for the final report)'
if ([string]::IsNullOrWhiteSpace($rollNumber)) { throw 'Roll number cannot be blank; no repository was created.' }

$owner = (gh api user --jq '.login').Trim()
if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($owner)) { throw 'Could not determine the authenticated GitHub account.' }
$repoUrl = "https://github.com/$owner/$repoName"

# Build a final report that includes the repository URL and student details before the first commit.
$env:HEART_MLOPS_REPO_URL = $repoUrl
$env:HEART_MLOPS_STUDENT_NAME = $studentName
$env:HEART_MLOPS_ROLL_NUMBER = $rollNumber
& $pythonExe @pythonArgs -c "import reportlab, matplotlib, pandas, sklearn, joblib, PIL" 2>$null
if ($LASTEXITCODE -ne 0) {
    throw 'Report-build dependencies are missing. Activate your project virtual environment and run: python -m pip install -r requirements-notebooks.txt. Then rerun this script.'
}
& $pythonExe @pythonArgs scripts/build_report.py
if ($LASTEXITCODE -ne 0) { throw 'Report rebuild failed; repository was not created. Fix the report-build error and retry.' }

if (-not (Test-Path '.git')) {
    git init -b main
    if ($LASTEXITCODE -ne 0) { throw 'git init failed.' }
}
$currentBranch = (git branch --show-current).Trim()
if ($currentBranch -ne 'main') {
    git branch -M main
    if ($LASTEXITCODE -ne 0) { throw 'Could not set the main branch.' }
}

# Stage project files while respecting .gitignore (caches, local MLflow state, secrets).
git add -A
if ($LASTEXITCODE -ne 0) { throw 'git add failed.' }
$head = git rev-parse --verify HEAD 2>$null
if ($LASTEXITCODE -ne 0) {
    $gitName = git config user.name
    $gitEmail = git config user.email
    if ([string]::IsNullOrWhiteSpace($gitName) -or [string]::IsNullOrWhiteSpace($gitEmail)) {
        throw 'Configure git user.name and user.email (git config --global user.name / user.email), then rerun.'
    }
    git commit -m 'Initial MLOps assignment submission'
} else {
    git diff --cached --quiet
    if ($LASTEXITCODE -ne 0) { git commit -m 'Prepare MLOps assignment submission' }
}
if ($LASTEXITCODE -ne 0) { throw 'git commit failed.' }

$visibilityFlag = if ($visibility -eq 'private') { '--private' } else { '--public' }
gh repo create $repoName --source . --remote origin --push $visibilityFlag
if ($LASTEXITCODE -ne 0) { throw 'GitHub repository creation/push failed. Check whether this repository name already exists.' }

Write-Host ''
Write-Host 'Repository created and pushed:' -ForegroundColor Green
Write-Host $repoUrl
Write-Host 'Next: open the Actions tab, wait for the ci workflow, and resolve any failure before submission.'
