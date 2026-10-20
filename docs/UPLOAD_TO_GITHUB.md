# GitHub repository and course submission

This project already lives at [dineshsaitejaparuchuri/mlops-assignment](https://github.com/dineshsaitejaparuchuri/mlops-assignment). The local checkout is connected to that repository. After editing locally, review and commit the changes, then push `main`. The video is intentionally excluded; record and submit it separately if required by the course.

## Before rebuilding the report

1. Install Git for Windows and [GitHub CLI](https://cli.github.com/).
2. Open PowerShell in the project folder (the one containing `scripts`, `src`, `README.md`, and `requirements.txt`).
3. Authenticate once with `gh auth login` and confirm that it succeeds with `gh auth status`.
4. Configure your Git author name and email if not already configured:
   `git config --global user.name "Your Name"` and `git config --global user.email "you@example.com"`.
5. Activate your project virtual environment and install dependencies, including the report-generation tools:
   `pip install -r requirements-notebooks.txt`.

## Windows PowerShell

**Important:** run the report command from the project root (the folder that contains `scripts`, `src`, `README.md`, and `requirements.txt`). If your prompt says `PS C:\Windows\system32>`, you are in the wrong directory.

For example, in this checkout, run:

```powershell
Set-Location "$HOME\Downloads\heart-mlops-submission\heart-mlops-final"
Get-ChildItem
Test-Path ".\scripts\build_report.py"  # should return True
```

If the folder name differs, update `Set-Location` to the actual project path. To rebuild the report, set the student details and repository URL first:

```powershell
$env:HEART_MLOPS_REPO_URL = "https://github.com/dineshsaitejaparuchuri/mlops-assignment"
$env:HEART_MLOPS_STUDENT_NAME = "Dinesh Sai Teja Paruchuri"
$env:HEART_MLOPS_ROLL_NUMBER = "2025AE05145"
python scripts/build_report.py
```

The repository is public. Review the diff, commit, and push when the local work is ready. Do not create a second repository for this project.

## macOS / Linux

```bash
HEART_MLOPS_REPO_URL=https://github.com/dineshsaitejaparuchuri/mlops-assignment \
HEART_MLOPS_STUDENT_NAME="Dinesh Sai Teja Paruchuri" \
HEART_MLOPS_ROLL_NUMBER=2025AE05145 python scripts/build_report.py
```

## After publication

1. Open the repository and go to the **Actions** tab. Wait for the latest `ci` workflow to complete.
2. If a workflow run fails, inspect the logs and fix the failure. The workflow includes a disposable kind cluster and an end-to-end Ingress route test.
3. Confirm that the repository README and `docs/report/MLOps_Assignment1_Report.pdf` are present and the student details/repository URL on the report cover are correct.
4. The CI Ingress test is temporary and does not create a persistent API endpoint. For local access, use the port-forward or NodePort option documented in the README.
5. Upload the repository/report to the course portal and record and submit the short pipeline video separately; the video is not included here.
