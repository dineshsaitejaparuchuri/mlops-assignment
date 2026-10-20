#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

CLUSTER_NAME="heart-ci"
NODE_IMAGE="kindest/node:v1.36.4@sha256:099e049362a1526b2db71494e1947aae99bd16290d7c895f2b7ea312e3cbfaed"
PROVIDER_LOG="$ROOT/ci-output/cloud-provider-kind.log"
mkdir -p "$ROOT/ci-output"
provider_pid=""

cleanup() {
  result=$?
  trap - EXIT
  if [ "$result" -ne 0 ]; then
    kubectl get pods,svc,ingress -A -o wide || true
    kubectl describe ingress heart-api -n heart-mlops || true
    tail -n 100 "$PROVIDER_LOG" || true
  fi
  if [ -n "$provider_pid" ]; then
    sudo kill "$provider_pid" >/dev/null 2>&1 || true
    wait "$provider_pid" >/dev/null 2>&1 || true
  fi
  kind delete cluster --name "$CLUSTER_NAME" >/dev/null 2>&1 || true
  exit "$result"
}
trap cleanup EXIT

kind create cluster --name "$CLUSTER_NAME" --image "$NODE_IMAGE" --wait 5m
kind load docker-image heart-disease-api:latest --name "$CLUSTER_NAME"
kubectl label node "${CLUSTER_NAME}-control-plane" \
  node.kubernetes.io/exclude-from-external-load-balancers- --overwrite

export KUBECONFIG="${KUBECONFIG:-$HOME/.kube/config}"
sudo env KUBECONFIG="$KUBECONFIG" cloud-provider-kind >"$PROVIDER_LOG" 2>&1 &
provider_pid=$!

kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/deployment.yaml -f k8s/service.yaml -f k8s/ingress.yaml
kubectl -n heart-mlops rollout status deployment/heart-api --timeout=180s

ingress_ip=""
for _ in $(seq 1 90); do
  ingress_ip="$(kubectl get ingress heart-api -n heart-mlops \
    -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null || true)"
  if [ -n "$ingress_ip" ] && \
    curl --connect-timeout 2 -fsS -H 'Host: heart.local' \
      "http://${ingress_ip}/health" >/dev/null 2>&1; then
    break
  fi
  sleep 2
done

if [ -z "$ingress_ip" ]; then
  echo "Ingress did not receive an external IP" >&2
  exit 1
fi

SMOKE_TEST_HOST=heart.local bash scripts/smoke_test.sh "http://${ingress_ip}" \
  2>&1 | tee "$ROOT/ci-output/ingress-smoke.txt"
kubectl get ingress heart-api -n heart-mlops -o wide \
  | tee "$ROOT/ci-output/ingress-status.txt"
kubectl get pods,svc -n heart-mlops -o wide \
  | tee "$ROOT/ci-output/kubernetes-resources.txt"
