# Kubernetes manifests

Equivalent of the docker-compose stack as Kubernetes resources. Platform-
neutral by default (only `Deployment`, `Service`, `ConfigMap`, `Secret`) so
the same files apply to vanilla Kubernetes, OpenShift, k3s, kind, etc.

## Layout

```text
k8s/
  configmaps.yaml   demo-shared-config + prometheus.yml.tmpl + config.alloy
  secret.yaml       elastic-credentials placeholder
  app.yaml          demo-app Deployment + Service
  prometheus.yaml   Prometheus Deployment + Service
  alloy.yaml        Alloy Deployment + Service
```

The same configuration shape as compose:

- Image versions are pinned in the Deployment manifests.
- Non-secret config (job name, ports, scrape interval, scrape target) lives in `demo-shared-config`.
- Elastic endpoint and API key live in the `elastic-credentials` Secret.
- `prometheus.yml.tmpl` uses `__PLACEHOLDER__` tokens; the pod renders it with `sed` at start. Alloy reads `sys.env(...)` natively.

## Security context

All three pods run **non-root**:

- `prom/prometheus` runs as `nobody` (UID 65534) by default.
- `grafana/alloy` runs as `alloy` by default.
- `demo-app` is built with `USER 1001` in the Dockerfile.

Each pod sets `runAsNonRoot: true`, drops all capabilities, and uses
`seccompProfile: RuntimeDefault`. No `runAsUser` or `fsGroup` is hard-coded,
so OpenShift's `restricted-v2` SCC can assign random UIDs from the project's
allowed range. Writable paths use `emptyDir` volumes.

## Build the demo-app image

The image must be reachable by your cluster. Pick whichever fits your platform:

**OpenShift integrated registry:**

```bash
oc new-build --binary --name=prometheus-demo-app --strategy=docker
oc start-build prometheus-demo-app --from-dir=. --follow
```

Then update `app.yaml`'s `image:` to:

```yaml
image: image-registry.openshift-image-registry.svc:5000/<project>/prometheus-demo-app:latest
```

**External registry (Quay / GHCR / Docker Hub):**

```bash
docker build -t ghcr.io/<you>/prometheus-demo-app:latest .
docker push ghcr.io/<you>/prometheus-demo-app:latest
# update app.yaml image: to match
```

**Local kind / minikube:**

```bash
docker build -t prometheus-demo-app:latest .
kind load docker-image prometheus-demo-app:latest         # kind
minikube image load prometheus-demo-app:latest            # minikube
```

## Apply

```bash
# Create the secret with real values
kubectl create secret generic elastic-credentials \
  --from-literal=ES_ENDPOINT=https://your-cluster.es.io \
  --from-literal=ES_API_KEY=your-api-key

# Apply everything else
kubectl apply -f k8s/configmaps.yaml -f k8s/app.yaml \
              -f k8s/prometheus.yaml -f k8s/alloy.yaml
```

(Substitute `oc` for `kubectl` on OpenShift if you prefer.)

## Access the UIs

The manifests ship only `ClusterIP` Services. Pick the access pattern that
fits your platform:

**Port-forward (works everywhere):**

```bash
kubectl port-forward svc/prometheus 9090:9090
kubectl port-forward svc/alloy 12345:12345
kubectl port-forward svc/demo-app 8000:8000
```

**OpenShift Route (one-liner per service):**

```bash
oc expose svc/prometheus
oc expose svc/alloy
oc get routes
```

Add `--hostname=...` and `oc patch route ...` if you need TLS edge termination.

**Ingress (clusters with an ingress controller):**

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: prometheus
spec:
  rules:
    - host: prometheus.example.com
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: prometheus
                port:
                  number: 9090
```

## Updating Elastic credentials

```bash
kubectl create secret generic elastic-credentials \
  --from-literal=ES_ENDPOINT=https://new-cluster.es.io \
  --from-literal=ES_API_KEY=new-key \
  --dry-run=client -o yaml | kubectl apply -f -
kubectl rollout restart deploy/prometheus deploy/alloy
```
