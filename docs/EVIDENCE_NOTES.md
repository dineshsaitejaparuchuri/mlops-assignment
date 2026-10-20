# Verification evidence and remaining actions

The browser screenshots were captured from the local services; terminal images were rendered from saved command output in a neutral terminal frame, so the Windows test environment is not presented as macOS. Terminal images mask only the machine-specific workspace path; the saved command output remains unchanged. The local captures and CI artifacts are dated October 20, 2026; captured timestamps were not edited. Local Kubernetes evidence shows port-forward access. The local Ingress received no address, so local Ingress routing is not claimed.

| Evidence | What it shows | Status |
|---|---|---|
| `terminal_pytest.png`, `docs/run_outputs/pytest_verbose.txt`, `docs/run_outputs/pytest_junit.xml`, `docs/run_outputs/coverage.xml` | Local unit tests and coverage | Refreshed during final verification: 23 tests passed. |
| `terminal_flake8.png`, `docs/run_outputs/flake8_run.txt` | Local lint | Refreshed during final verification; no lint findings. |
| `docker_build_run.png`, `docs/run_outputs/docker_build.txt`, `docs/run_outputs/docker_run.txt` | Docker build/run and API smoke test | Refreshed against image version 1.0.0; container runs as non-root and reports healthy. |
| `k8s_pods_services.png`, `k8s_smoke_test.png`, `docs/run_outputs/k8s_*.txt` | Local Kubernetes resources and API checks | Refreshed; API and monitoring pods are running and port-forward smoke checks pass. Local Ingress routing remains unverified. |
| `grafana_dashboard.png`, `prometheus_targets.png` | Monitoring dashboard and Prometheus scrape targets | Captured from local services; API targets are up. |
| `ci_ingress_verification.png`, `docs/run_outputs/ci_ingress_*.txt` | Hosted Ingress address and `/health`, `/predict`, `/metrics` smoke test | The PNG is a locally rendered view of the downloaded workflow artifact, not a browser screenshot. The raw artifact logs and successful Actions run #10 are linked here: https://github.com/dineshsaitejaparuchuri/mlops-assignment/actions/runs/39402219483. |
| `github_actions_run.jpg` | Hosted Actions run summary | Actual browser capture of run #10 showing success, both successful jobs, and two uploaded artifacts. The browser is signed out, so job-level step output is evidenced by the linked workflow artifact logs, not this screenshot. |
| GitHub Actions run #10 | CI lint, tests, training, Docker, and disposable kind Ingress checks | All jobs passed in the run; artifacts were uploaded. |

## Remaining actions

- Submit the repository and report through the course portal; that external account is not available in this workspace.
- The project has no persistent public API endpoint. The hosted Ingress check runs in an ephemeral CI cluster.
