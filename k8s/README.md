# Kubernetes Manifests

Deploy the JUMO Data Platform to any Kubernetes cluster (Docker Desktop, minikube, GKE, EKS, AKS).

> **Note**: Requires `nginx-ingress` controller installed in the cluster.

## Prerequisites

```bash
# Install nginx ingress controller
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.10.0/deploy/static/provider/cloud/deploy.yaml

# Verify
kubectl get pods -n ingress-nginx
```

## Apply manifests

```bash
# 1. Namespace + shared config
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/configmap.yaml

# 2. Secrets — EDIT FIRST: replace base64 placeholders with real values
#    echo -n 'your-stripe-key' | base64
kubectl apply -f k8s/secrets.yaml

# 3. Infrastructure (databases, Redis, Kafka)
kubectl apply -f k8s/infra/

# 4. Application services
kubectl apply -f k8s/users/
kubectl apply -f k8s/admin/
kubectl apply -f k8s/ambassador/
kubectl apply -f k8s/checkout/
kubectl apply -f k8s/analytics/
kubectl apply -f k8s/email/
kubectl apply -f k8s/react-frontend/

# 5. Ingress routing
kubectl apply -f k8s/ingress.yaml
```

## Verify rollouts

```bash
kubectl rollout status deployment/users       -n jumo-platform
kubectl rollout status deployment/admin       -n jumo-platform
kubectl rollout status deployment/ambassador  -n jumo-platform
kubectl rollout status deployment/checkout    -n jumo-platform
kubectl rollout status deployment/analytics   -n jumo-platform

# Check all pods
kubectl get pods -n jumo-platform
```

## Run Spark batch job manually

```bash
kubectl apply -f k8s/spark-job.yaml
kubectl logs -f job/spark-aggregate-orders -n jumo-platform
```

## Access services

```bash
# Port-forward for local testing
kubectl port-forward svc/react-frontend 3000:3000 -n jumo-platform
kubectl port-forward svc/admin          8002:8002 -n jumo-platform
```
