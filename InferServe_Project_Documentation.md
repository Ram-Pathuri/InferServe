# InferServe — Production-Grade ML Model Serving Platform

**Project documentation — living doc, update as you build**
**Owner:** Ram | **Duration:** 3 weeks | **Goal:** Deep FastAPI + Docker + Kubernetes, portfolio-ready for ML Engineer roles

---

## 1. What This Project Is

InferServe is an API that serves a machine learning model (NLP text classification) the way a real company would run it in production — not a notebook, not a single `predict()` script.

**The problem it solves (the story you'll tell in interviews):**
Most ML portfolios stop at "I trained a model and got 92% accuracy." InferServe answers the next question every ML Engineer interview actually asks: *how do you serve this to real users, keep it fast, keep it running, and know when it's silently breaking?*

**What it demonstrates:**
- You can build a production API, not just a script (FastAPI in depth)
- You can package and run software reliably (Docker)
- You can operate that software at scale (Kubernetes)
- You understand the full lifecycle of a model after training — serving, monitoring, drift, retraining (MLOps)

**One-line pitch for your README / resume:**
> "A containerized FastAPI service serving versioned ML models with async batch inference, Redis caching, Prometheus/Grafana monitoring, automated drift detection, and Kubernetes autoscaling — deployed on GKE."

---

## 2. Current Status — What We're Building Right Now

We are in **Week 1: the core FastAPI service.** Nothing is containerized or deployed yet — the priority right now is a correct, well-tested, production-shaped API running locally.

### In progress this week
| Component | Status | Detail |
|---|---|---|
| Project skeleton | 🔲 Not started | Routers, Pydantic v2 schemas, settings via `pydantic-settings` |
| Model loading | 🔲 Not started | Loaded once at app startup via FastAPI `lifespan` events, not per-request |
| Prediction endpoint | 🔲 Not started | `POST /v1/predict` — validates input, returns prediction + confidence |
| Database layer | 🔲 Not started | Async SQLAlchemy + PostgreSQL, logs every prediction (input, output, latency, model version) |
| Auth | 🔲 Not started | JWT for users, API keys for service-to-service calls |
| Error handling | 🔲 Not started | Custom exception handlers, consistent error response schema |
| Tests | 🔲 Not started | pytest + httpx async client, target 80%+ coverage |
| CI | 🔲 Not started | GitHub Actions — lint (ruff) + test on every push |

*(Update this table's status column as you complete each piece — 🔲 → 🟡 in progress → ✅ done.)*

### Why this order matters
Docker and Kubernetes are meaningless without something worth containerizing. Week 1 exists so that by Week 2, you're not debugging your API *and* Docker at the same time — you're containerizing something you already know works.

---

## 3. Architecture (Target — End of Week 3)

```
                        ┌─────────────────────────┐
                        │        Ingress           │
                        │   (routes external       │
                        │    traffic → Service)     │
                        └────────────┬─────────────┘
                                     │
                        ┌────────────▼─────────────┐
                        │      Kubernetes Service    │
                        │   (load balances pods)     │
                        └────────────┬─────────────┘
                                     │
              ┌──────────────────────┼──────────────────────┐
              │                      │                       │
      ┌───────▼──────┐      ┌────────▼──────┐       ┌────────▼──────┐
      │ FastAPI Pod 1 │      │ FastAPI Pod 2  │  ...  │ FastAPI Pod N  │
      │ (autoscaled)  │      │                │       │  (HPA)         │
      └───────┬───────┘      └────────┬───────┘       └────────┬──────┘
              │                       │                        │
      ┌───────┴───────────────────────┴────────────────────────┴───────┐
      │                                                                  │
┌─────▼──────┐   ┌──────────────┐   ┌───────────────┐   ┌───────────────┐
│  PostgreSQL │   │    Redis      │   │ Celery Worker │   │  Prometheus   │
│ (predictions│   │  (cache +     │   │ (async batch  │   │  + Grafana    │
│    log)     │   │  job queue)   │   │  inference)   │   │  (metrics)    │
└─────────────┘   └──────────────┘   └───────────────┘   └───────────────┘
                                                                    │
                                                          ┌─────────▼─────────┐
                                                          │  Evidently AI job   │
                                                          │  (drift detection)  │
                                                          │  → Slack alert      │
                                                          └────────────────────┘
```

You won't build this all at once. It's the target state — Week 1 is the FastAPI box in isolation, running with `uvicorn` on your laptop, no Postgres/Redis containers yet (or a bare-minimum local Postgres if your endpoints need it early).

---

## 4. How We're Implementing Docker (Week 2)

**Goal:** every piece of the architecture above runs as a container, and the whole stack starts with one command.

### Step-by-step plan
1. **Dockerfile for the FastAPI app**
   - Multi-stage build: a `builder` stage installs dependencies, a slim `runtime` stage copies only what's needed — smaller image, faster deploys, and it's the kind of detail interviewers ask about.
   - Run as a non-root user (`USER appuser`) — this is a real production/security expectation, not decoration.
   - `HEALTHCHECK` instruction that hits your `/health` endpoint.
2. **`.dockerignore`** — exclude `.venv`, `__pycache__`, tests, `.git` so images stay small.
3. **`docker-compose.yml`** for local development — wires together:
   - `api` (your FastAPI container)
   - `db` (Postgres)
   - `redis`
   - `worker` (Celery, same image as `api`, different entrypoint command)
   - Named volumes for Postgres data persistence, and a shared `.env` for config.
4. **Verify:** `docker compose up` should bring up the entire stack and `POST /v1/predict` should work end-to-end, including a prediction being written to Postgres.
5. **Push the image** to Docker Hub (or GCP Artifact Registry, since you already have GCP access) — this is what Kubernetes will later pull from.

### What you're learning here (not just doing)
- Why multi-stage builds exist (image size, attack surface)
- The difference between an image and a container
- Why services talk to each other by service name (`db`, not `localhost`) inside Docker's network
- Volumes vs. bind mounts, and why Postgres needs a volume to survive a container restart

---

## 5. How We're Implementing Kubernetes (Week 3)

**Goal:** take the exact same containers from Week 2 and run them the way a production cluster would — self-healing, scalable, configurable without rebuilding images.

### Step-by-step plan
1. **Local cluster first:** `kind` or `minikube` — no cloud cost, fast iteration, safe place to break things.
2. **Core manifests** (`/k8s` folder):
   - `deployment.yaml` — defines the FastAPI pods, image, replica count, resource `requests`/`limits`
   - `service.yaml` — stable internal address + load balancing across pods
   - `configmap.yaml` — non-secret config (log level, model version flag)
   - `secret.yaml` — DB credentials, JWT signing key (never in the image or git)
   - `postgres` and `redis` — either as their own Deployments+Services in the cluster, or (more realistic for production) treated as external managed services later
3. **Health probes:**
   - `readinessProbe` → your `/health` endpoint — controls whether a pod receives traffic
   - `livenessProbe` → restarts a pod if it's stuck/hung
   - This is the single most interview-relevant K8s concept for an API service — know *why* these two are different.
4. **Horizontal Pod Autoscaler (HPA):** scale pod count based on CPU usage under load — this is what you'll demonstrate with your Locust load test from Week 2.
5. **Ingress:** expose the service outside the cluster with a proper hostname/path routing, instead of raw `NodePort`.
6. **Move to the cloud:** once it works on `kind`, push the same manifests to GKE Autopilot (uses your existing GCP familiarity) — same YAML, different cluster, which is itself the point of Kubernetes.

### What you're learning here (not just doing)
- Declarative infrastructure — you describe the desired state, K8s reconciles it
- Why Pods are ephemeral and Deployments/Services exist to abstract that away
- Config/secret separation from code — this connects directly to 12-factor app principles
- Autoscaling as a response to real load data, not a guess

---

## 6. Future Steps — MLOps Layer (Post Week 3 / Stretch Goals)

Once the core service + Docker + K8s are solid, these are the next layers that turn this from "a deployed API" into "an MLOps system" — pick 2-3, don't try all of them:

| Feature | What it adds | Priority |
|---|---|---|
| **Drift detection** (Evidently AI) | Scheduled job compares live prediction inputs against training data distribution; alerts via Slack webhook when drift crosses a threshold | High — cheap to add, strong interview talking point |
| **Model versioning / A/B routing** | Serve v1 and v2 of the model simultaneously, split traffic, compare metrics | High — shows you understand deployment strategy, not just deployment |
| **CI/CD pipeline** | GitHub Actions: on push → lint → test → build image → push to registry → (optionally) auto-deploy to a staging namespace | High — this is what "production-grade" actually means |
| **Prometheus + Grafana dashboard** | Request rate, latency percentiles (p50/p95/p99), error rate, model confidence distribution | High — pairs directly with your Week 2 Locust benchmark |
| **Retraining trigger** | If drift crosses threshold, kick off a retraining job (can be a stub/simulated pipeline — the architecture matters more than a real retrain for portfolio purposes) | Medium |
| **MLflow integration** | Track model versions/experiments formally, since you already know MLflow | Medium — natural fit given your existing experience |
| **Canary deployment** | Route 5% of traffic to a new model version before full rollout | Low — nice-to-have, mention as "next step" even if unbuilt |

---

## 7. System Design — Traffic, Rate Limiting & DDoS Resilience

These aren't equally buildable in a solo 3-week project. Priority order below reflects what's real application work vs. what's genuinely an infrastructure concern you should understand and document rather than fully implement.

### 7.1 Rate Limiting — Highest Priority (build this)
Lives entirely in the app layer, so this is real, demonstrable work.

- **Algorithm:** token bucket — smooths short bursts while still enforcing a hard ceiling, and it's the industry-default answer in interviews. (Sliding window is stricter/more accurate but overkill here.)
- **Storage:** Redis-backed, not in-memory. An in-memory limiter only works per-process — the moment you run more than one pod (which HPA will do under load), each pod counts independently and the limit silently stops working. Redis gives you one shared counter across all pods.
- **Tiers:**
  - Per-IP limit for anonymous/unauthenticated requests (strict)
  - Per-API-key limit for authenticated clients (higher ceiling)
  - Optional: a stricter limit specifically on `/v1/predict` since it's your expensive endpoint, vs. a looser limit on `/health` or `/docs`
- **Implementation:** `slowapi` (FastAPI-native) or a custom dependency using `redis.incr` + `EXPIRE` — build the custom version once so you understand the mechanics, then you can cite either in interviews.
- **Response:** return `429 Too Many Requests` with a `Retry-After` header — small detail, frequently checked.

### 7.2 Handling Large Traffic Volume — Second Priority (mostly already covered)
This isn't a separate feature — it's the payoff of decisions already in this doc, plus a couple of additions:

| Already planned | Role in handling load |
|---|---|
| Redis caching | Avoids recomputing predictions for repeated inputs |
| Async I/O (FastAPI + async SQLAlchemy) | One slow request doesn't block others |
| Celery + Redis queue | Buffers spikes instead of failing requests outright |
| HPA (Kubernetes) | Adds pods automatically as CPU load rises |

**New additions worth documenting:**
- **DB connection pooling** — set explicit `pool_size`/`max_overflow` on your async engine; an unbounded pool is a real production failure mode under load
- **Read replicas** — name this as an honest next step: a single Postgres instance is your actual bottleneck at scale, and you don't need to build a replica to say so correctly in an interview
- **Load test proof** — your Week 2 Locust benchmark *is* your evidence here; the before/after latency numbers under simulated concurrent load are what make this section credible instead of theoretical

### 7.3 DDoS Protection — Understand and Document, Don't Over-Build
Be direct with yourself: a solo project cannot actually stop a DDoS attack. That's solved at the network layer (Cloudflare, GCP Cloud Armor, AWS Shield), not in application code — and claiming otherwise in an interview would be a red flag, not a strength. What's worth doing:

- Your rate limiter (7.1) is your **last line of defense**, not your DDoS defense — say this explicitly in your README so it reads as informed, not naive
- Set request size limits and timeouts at the Ingress/reverse-proxy level in Kubernetes — cheap to configure, real protection against slow/oversized request attacks
- Since you're already deploying on GCP: name **Cloud Armor** sitting in front of your Ingress as where real DDoS/WAF protection belongs. You don't need to fully configure it — correctly identifying the layer solves the problem is the signal
- Frame it in your docs as the **layered defense model**: network layer (Cloud Armor/CDN) → transport (Ingress timeouts/size limits) → application (rate limiting + auth). This shows systems thinking, which is exactly what "system design" questions are testing for

---

## 8. Timeline Summary

| Week | Focus | Deliverable at end of week |
|---|---|---|
| **1** (current) | FastAPI in depth | A working, tested, locally-running API with auth, DB logging, and CI |
| **2** | Docker + async + observability | Full stack running via `docker compose up`; Prometheus metrics live; Locust benchmark with before/after latency numbers |
| **3** | Kubernetes + shipping | Same stack running on `kind`/GKE with HPA, health probes, ingress; polished README with architecture diagram and demo |

---

## 9. Tech Stack Reference

- **API:** FastAPI, Pydantic v2, async SQLAlchemy
- **Data:** PostgreSQL, Redis
- **Async jobs:** Celery
- **Testing:** pytest, httpx, Locust (load testing)
- **Monitoring:** Prometheus, Grafana, Evidently AI
- **Containers:** Docker, Docker Compose
- **Orchestration:** Kubernetes (kind/minikube → GKE Autopilot)
- **CI/CD:** GitHub Actions

---

*Next update: fill in Section 2's status table as Week 1 tasks are completed, and add screenshots/GIFs to Section 3 once the API is running.*
