#!/usr/bin/env bash
# Runs the real .github/workflows/ci.yml locally with `act` (nothing is pushed, no GitHub access).
# The 3 third-party actions are replaced by local stubs in .ci-local/actions and a local runner image
# with Python 3.11 + docker CLI, so act never contacts GitHub.
set -euo pipefail
cd "$(dirname "$0")/.."
docker build -q -t heart-ci-runner:local .ci-local/runner
rm -rf .ci-local/artifacts
act push -W .github/workflows/ci.yml \
  -P ubuntu-latest=heart-ci-runner:local --pull=false \
  --container-architecture linux/arm64 \
  --local-repository actions/checkout@v4=.ci-local/actions/checkout \
  --local-repository actions/setup-python@v5=.ci-local/actions/setup-python \
  --local-repository actions/upload-artifact@v4=.ci-local/actions/upload-artifact \
  --action-offline-mode \
  --bind
