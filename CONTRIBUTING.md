# Contributing

## Adding a new microservice

1. Create `go_microservices/<service>/` following the pattern of `users/` or `admin/`
2. Add `go.mod` with `module <service>` and `go 1.24`
3. Create `src/{controllers,database,middlewares,models,routes}/`
4. Write `Dockerfile` using `golang:1.24-alpine`
5. Add service to `go_microservices/docker-compose.yaml` with a `mem_limit`
6. Add CI workflow `.github/workflows/ci-<service>.yml`
7. Add K8s manifests under `k8s/<service>/`
8. Update `README.md` service map

## Code conventions

- All Go services use **Fiber v2** and **GORM**
- All credentials come from **environment variables** — never hardcode
- All containers have a `mem_limit` — respect the 4 GB budget
- JWT secret is shared across services via `JWT_SECRET` env var
- Services sharing the ambassador MySQL DB must join `ambassador_network`

## Running tests

```bash
# Go services — no test framework set up yet; use go vet as a minimum
docker compose exec <service> go vet ./...

# Spark unit tests (in-memory, no Docker needed)
pip install pyspark==3.5.* pytest
pytest spark/tests/ -v
```
