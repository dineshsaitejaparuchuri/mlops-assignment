# Verification evidence and remaining external checks

The screenshots and text logs in this repository document earlier local runs. Terminal images are rendered from the corresponding saved command output; browser images were captured from the local services. They are evidence of those local runs, not claims that the same steps were rerun in this packaging environment.

| Evidence | What it shows | Status |
|---|---|---|
| `terminal_pytest.png`, `docs/run_outputs/pytest_verbose.txt` | 18 unit tests | Captured successful run; the tests also passed again during this review. |
| `terminal_flake8.png`, `docs/run_outputs/flake8_run.txt` | Flake8 lint run | Captured successful run. Flake8 was not installed in the packaging environment, and network access was unavailable to install it again. |
| `docker_build_run.png`, `docs/run_outputs/docker_build.txt`, `docker_run.txt` | Docker build/run and API smoke test | Captured local run; Docker is not installed in the packaging environment for a fresh rerun. |
| `k8s_pods_services.png`, `k8s_smoke_test.png`, `docs/run_outputs/k8s_*.txt` | Local kind cluster and API smoke test via port-forward | Captured successful local run. Kubernetes tools are not installed in the packaging environment for a fresh rerun. |
| `grafana_dashboard.png`, `prometheus_targets.png` | Monitoring dashboard and Prometheus scrape targets | Captured local browser screenshots. |
| `ci_run.png`, `docs/run_outputs/act_ci_full.txt` | Local run of `.github/workflows/ci.yml` using `act` | Captured successful local run; this is not a GitHub-hosted Actions result. |

## Still required outside this package

- **GitHub repository and hosted CI:** the source package has not been pushed. The GitHub tools available in this session did not expose a repository-creation action, and no repositories were returned by the connector. Use `scripts/publish_to_github.ps1` on Windows after installing Git/GitHub CLI and authenticating with `gh auth login`; it asks for repository visibility before creating the remote and pushing. Then open the GitHub Actions tab and confirm the hosted `ci` workflow succeeds.
- **Ingress route:** `k8s/ingress.yaml` is present and was previously server-side dry-run validated, but an ingress-nginx controller was not installed in the captured run. The screenshots therefore prove API access by port-forward, not public/Ingress routing. Install and test the ingress controller on the target local Kubernetes cluster before claiming that route is verified.
- **Student details:** add the required student name and roll number to the report.
- **Repository URL:** after the push, rebuild the PDF with `HEART_MLOPS_REPO_URL` set to the actual GitHub URL so the submitted report has a working code link.
- **Video:** intentionally not included, as requested. Use `docs/demo_video_script.md` as an outline if a recording is required later.
