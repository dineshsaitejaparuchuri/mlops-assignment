# Publish this project to GitHub

The source package is ready to publish. The publishing script creates a new GitHub repository under the account authenticated with GitHub CLI, rebuilds the report with the selected repository URL and student details, then commits and pushes the complete project. The video is intentionally excluded.

## Before running the script

1. Install Git for Windows and [GitHub CLI](https://cli.github.com/).
2. Open PowerShell in the extracted `heart-mlops` folder.
3. Authenticate once with `gh auth login` and confirm that it succeeds with `gh auth status`.
4. Configure your Git author name and email if not already configured:
   `git config --global user.name "Your Name"` and `git config --global user.email "you@example.com"`.
5. Activate your project virtual environment and install dependencies, including the report-generation tools:
   `pip install -r requirements-notebooks.txt`.

## Windows PowerShell

**Important:** `gh auth login` can be run from any folder, but the publishing script must be run from the extracted project root (the folder that contains `scripts`, `src`, `README.md`, and `requirements.txt`). If your prompt says `PS C:\Windows\system32>`, you are in the wrong directory.

For example, if you extracted the downloaded ZIP to your Downloads folder as `heart-mlops-final`, run:

```powershell
Set-Location "$HOME\Downloads\heart-mlops-final"
Get-ChildItem
Test-Path ".\scripts\publish_to_github.ps1"  # should return True
```

If the folder name differs, update `Set-Location` to the actual extracted path. Then run:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\scripts\publish_to_github.ps1
```

The script asks for the repository name (default: `heart-mlops-assignment-1`), visibility (private by default), your student name and roll number. It then builds the report with the actual GitHub URL before making the first commit, creates the repository, and pushes the `main` branch. Keep the repository private unless you are comfortable making the code public; if it is private, give your instructor access before submitting the URL.

## macOS / Linux

```bash
bash scripts/publish_to_github.sh
```

## After publication

1. Open the repository and go to the **Actions** tab. Wait for the `ci` workflow to complete.
2. If a workflow run fails, inspect the logs and fix the failure; a previous local `act` run is not a substitute for the hosted GitHub Actions result.
3. Confirm that the repository README and `docs/report/MLOps_Assignment1_Report.pdf` are present and the student details/repository URL on the report cover are correct.
4. Verify the deployment path accepted by your instructor. The Ingress route requires an installed controller; without it, use the documented port-forward or NodePort option and include fresh evidence if required.
5. Record and submit the short pipeline video separately.
