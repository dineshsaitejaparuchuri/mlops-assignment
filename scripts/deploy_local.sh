#!/usr/bin/env bash
set -euo pipefail

IMAGE="heart-disease-api:1.0.0"
CLUSTER="heart-mlops"
cd "$(dirname "$0")/.."

docker build -t "$IMAGE" .

if command -v kind >/dev/null 2>&1; then
  kind get clusters | grep -qx "$CLUSTER" || kind create cluster --name "$CLUSTER"
  kind load docker-image "$IMAGE" --name "$CLUSTER"
elif command -v minikube >/dev/null 2>&1; then
  minikube status >/dev/null 2>&1 || minikube start
  minikube image load "$IMAGE"
else
  echo "install kind or minikube first" >&2
  exit 1
fi

kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/deployment.yaml -f k8s/service.yaml -f k8s/service-nodeport.yaml -f k8s/ingress.yaml
grafana_password="${GRAFANA_ADMIN_PASSWORD:-$(openssl rand -base64 24)}"
kubectl -n heart-mlops create secret generic grafana-admin \
  --from-literal=username=admin --from-literal=password="$grafana_password" \
  --dry-run=client -o yaml | kubectl apply -f -
kubectl apply -f k8s/monitoring/
kubectl -n heart-mlops rollout status deployment/heart-api --timeout=180s
kubectl -n heart-mlops rollout status deployment/prometheus --timeout=180s
kubectl -n heart-mlops rollout status deployment/grafana --timeout=180s

cat <<MSG
Deployed. Port-forward in separate terminals:
  kubectl -n heart-mlops port-forward svc/heart-api 8000:80
  kubectl -n heart-mlops port-forward svc/prometheus 9090:9090
  kubectl -n heart-mlops port-forward svc/grafana 3000:3000
Then: scripts/smoke_test.sh http://localhost:8000
Grafana: http://localhost:3000 (username: admin; password printed below); Prometheus: http://localhost:9090.
Grafana password: $grafana_password
The Ingress object is applied. To route locally with kind + cloud-provider-kind,
add the reported ingress address to the hosts file as "<address> heart.local",
then run: curl -H 'Host: heart.local' http://<address>/health
MSG
