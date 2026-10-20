# Verification evidence and remaining actions

The screenshots and logs in this repository document captured local runs. Terminal images were rendered from the corresponding saved command output; browser images were captured from the local services. They remain evidence of those runs and are not presented as new captures from the current machine.

| Evidence | What it shows | Status |
|---|---|---|
| `terminal_pytest.png`, `docs/run_outputs/pytest_verbose.txt` | 18 unit tests | Captured successful local run; hosted Actions run [#4](https://github.com/dineshsaitejaparuchuri/mlops-assignment/actions/runs/39387758630) also passed. |
| `terminal_flake8.png`, `docs/run_outputs/flake8_run.txt` | Flake8 lint run | Captured successful local run; hosted Actions run [#4](https://github.com/dineshsaitejaparuchuri/mlops-assignment/actions/runs/39387758630) also passed lint. |
| `docker_build_run.png`, `docs/run_outputs/docker_build.txt`, `docker_run.txt` | Docker build/run and API smoke test | Captured successful local run; hosted Actions run [#4](https://github.com/dineshsaitejaparuchuri/mlops-assignment/actions/runs/39387758630) also built and smoke-tested the container. |
| `k8s_pods_services.png`, `k8s_smoke_test.png`, `docs/run_outputs/k8s_*.txt` | Local kind deployment and API checks through port-forward | Captured successful local run. Hosted Actions run [#4](https://github.com/dineshsaitejaparuchuri/mlops-assignment/actions/runs/39387758630) verified the Ingress route in a disposable kind cluster. |
| `grafana_dashboard.png`, `prometheus_targets.png` | Monitoring dashboard and Prometheus scrape targets | Captured local browser screenshots. |
| `ci_run.png`, `docs/run_outputs/act_ci_full.txt` | Local run of `.github/workflows/ci.yml` using `act` | Captured successful local run. Hosted Actions run [#4](https://github.com/dineshsaitejaparuchuri/mlops-assignment/actions/runs/39387758630) passed the application pipeline and Ingress check. |

## Remaining actions

- The updated code, report and documentation are pushed to GitHub; run [#4](https://github.com/dineshsaitejaparuchuri/mlops-assignment/actions/runs/39387758630) passed all steps.
- The report was rebuilt with the repository URL and student details set and verified at 10 pages.
- Submit the repository and report through the course portal. That account and submission step are outside this workspace.
- The project has no persistent public API endpoint. The Ingress check ran in an ephemeral CI cluster; it validates routing but does not create a long-lived deployment.
- The video is intentionally excluded at the student's request.
