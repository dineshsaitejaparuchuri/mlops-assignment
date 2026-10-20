# Verification evidence and remaining actions

The screenshots and logs in this repository document captured runs. Existing local terminal images were rendered from their saved command output; browser images were captured from local services. The new Ingress image is rendered locally from the actual hosted workflow artifact. The older local Kubernetes screenshot shows port-forward access from before cloud-provider-kind was added; it is not Ingress-routing evidence.

`docs/run_outputs/deploy_local.txt` and `docs/run_outputs/k8s_pods.txt` preserve that historical local run, including the old ingress-nginx note. Current instructions are in `scripts/deploy_local.sh` and `README.md`; the routed Ingress check passed in hosted run #4.

| Evidence | What it shows | Status |
|---|---|---|
| `terminal_pytest.png`, `docs/run_outputs/pytest_verbose.txt` | 18 unit tests | Captured successful local run; hosted Actions run [#4](https://github.com/dineshsaitejaparuchuri/mlops-assignment/actions/runs/39387758630) also passed. |
| `terminal_flake8.png`, `docs/run_outputs/flake8_run.txt` | Flake8 lint run | Captured successful local run; hosted Actions run [#4](https://github.com/dineshsaitejaparuchuri/mlops-assignment/actions/runs/39387758630) also passed lint. |
| `docker_build_run.png`, `docs/run_outputs/docker_build.txt`, `docker_run.txt` | Docker build/run and API smoke test | Captured successful local run; hosted Actions run [#4](https://github.com/dineshsaitejaparuchuri/mlops-assignment/actions/runs/39387758630) also built and smoke-tested the container. |
| `k8s_pods_services.png`, `k8s_smoke_test.png`, `docs/run_outputs/k8s_*.txt` | Local kind deployment and API checks through port-forward | Captured successful local run. Hosted Actions run [#4](https://github.com/dineshsaitejaparuchuri/mlops-assignment/actions/runs/39387758630) verified the Ingress route in a disposable kind cluster. |
| `grafana_dashboard.png`, `prometheus_targets.png` | Monitoring dashboard and Prometheus scrape targets | Captured local browser screenshots. |
| `ci_run.png`, `docs/run_outputs/act_ci_full.txt` | Local run of `.github/workflows/ci.yml` using `act` | Captured successful local run. Hosted Actions run [#4](https://github.com/dineshsaitejaparuchuri/mlops-assignment/actions/runs/39387758630) passed the application pipeline and Ingress check. |
| `ci_ingress_verification.png`, `docs/run_outputs/ci_run4_ingress_*.txt` | Ingress status and `/health`, `/predict`, `/metrics` smoke test | Rendered locally from the actual uploaded artifact for hosted Actions run [#4](https://github.com/dineshsaitejaparuchuri/mlops-assignment/actions/runs/39387758630). |

## Remaining actions

- The updated code, report and documentation are pushed to GitHub; run [#4](https://github.com/dineshsaitejaparuchuri/mlops-assignment/actions/runs/39387758630) passed all steps.
- The report was rebuilt with the repository URL and student details set and verified at 10 pages.
- Submit the repository and report through the course portal. That account and submission step are outside this workspace.
- The project has no persistent public API endpoint. The Ingress check ran in an ephemeral CI cluster; it validates routing but does not create a long-lived deployment.
- The video is intentionally excluded at the student's request.
