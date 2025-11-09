# Deployment Guide

This guide covers deploying the Ceiling Grid ML Pipeline to production environments.

## Table of Contents
- [Development vs Production](#development-vs-production)
- [Production Deployment Options](#production-deployment-options)
- [Security Hardening](#security-hardening)
- [Scaling Considerations](#scaling-considerations)
- [Monitoring & Observability](#monitoring--observability)
- [Cloud Deployment Examples](#cloud-deployment-examples)

---

## Development vs Production

### Current Setup (Development)
The current `docker-compose.yml` is optimized for **local development and demos**:

```yaml
✅ LocalExecutor (simple, no Redis/Celery)
✅ PostgreSQL 16 Alpine (fast, minimal)
✅ UV for dependency management
✅ Structured logging via PipelineRunner
✅ Health checks on all services
```

**What's missing for production:**
- Secrets management (passwords are hardcoded)
- SSL/TLS encryption
- Persistent storage backups
- Horizontal scaling (CeleryExecutor)
- Load balancing
- Log aggregation (ELK, Datadog, etc.)
- Metrics exporters (Prometheus, StatsD)

---

## Production Deployment Options

### Option 1: Docker Compose (Small Scale)
**Use case:** Small team, low-traffic, single-node deployment

**Changes needed:**
```yaml
# Use external secrets
environment:
  AIRFLOW__CORE__FERNET_KEY: ${FERNET_KEY}  # Generate with cryptography.fernet.Fernet.generate_key()
  POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}    # Strong password from env

# Add SSL/TLS termination via Nginx
services:
  nginx:
    image: nginx:alpine
    ports:
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./certs:/etc/nginx/certs
```

**Persistent volumes:**
```yaml
volumes:
  postgres-db-volume:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: /mnt/data/postgres  # Dedicated disk
```

### Option 2: Kubernetes (Medium-Large Scale)
**Use case:** High availability, auto-scaling, multi-region

**Recommended tools:**
- **Helm Chart:** [apache-airflow/airflow](https://github.com/apache/airflow/tree/main/chart)
- **Executor:** CeleryExecutor or KubernetesExecutor
- **Database:** Managed PostgreSQL (RDS, Cloud SQL, Azure Database)
- **Storage:** Cloud object storage (S3, GCS, Azure Blob)

**Example architecture:**
```
┌─────────────────────────────────────────────────┐
│ Load Balancer (Ingress)                         │
└─────────────────┬───────────────────────────────┘
                  │
        ┌─────────┴──────────┐
        │                    │
┌───────▼────────┐  ┌────────▼────────┐
│ Webserver Pods │  │ Scheduler Pods  │
│ (Replicas: 2+) │  │ (Replicas: 1-2) │
└────────────────┘  └─────────────────┘
        │                    │
        └─────────┬──────────┘
                  │
        ┌─────────▼──────────┐
        │ Managed PostgreSQL │
        └────────────────────┘
```

**Quick start:**
```bash
helm repo add apache-airflow https://airflow.apache.org
helm install airflow apache-airflow/airflow \
  --set executor=CeleryExecutor \
  --set postgresql.enabled=false \
  --set externalDatabase.host=YOUR_RDS_ENDPOINT
```

### Option 3: Managed Services
**Use case:** Zero infrastructure management

**Options:**
- **Google Cloud Composer** (fully managed Airflow on GCP)
- **Amazon MWAA** (Managed Workflows for Apache Airflow on AWS)
- **Astronomer** (Airflow-as-a-service, multi-cloud)

**Migration path:**
1. Package your DAGs and src/ into a Docker image
2. Upload to managed service
3. Configure environment variables
4. Deploy

---

## Security Hardening

### 1. Secrets Management

**Never commit secrets to Git!**

```bash
# Generate strong Fernet key
python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# Store in .env (gitignored)
AIRFLOW__CORE__FERNET_KEY=your_generated_key_here
POSTGRES_PASSWORD=strong_random_password
_AIRFLOW_WWW_USER_PASSWORD=strong_admin_password
```

**Use secret managers in production:**
- **AWS:** AWS Secrets Manager, Parameter Store
- **GCP:** Secret Manager
- **Azure:** Key Vault
- **Kubernetes:** External Secrets Operator

### 2. Network Security

```yaml
# docker-compose.yml - Remove external ports
services:
  postgres:
    # ports:
    #   - "5432:5432"  # ❌ Don't expose to internet!

    # Only accessible within Docker network ✅
    expose:
      - "5432"
```

**Add reverse proxy with SSL:**
```nginx
# nginx.conf
server {
    listen 443 ssl http2;
    server_name airflow.yourcompany.com;

    ssl_certificate /etc/nginx/certs/cert.pem;
    ssl_certificate_key /etc/nginx/certs/key.pem;

    location / {
        proxy_pass http://airflow-webserver:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### 3. RBAC (Role-Based Access Control)

Airflow has built-in RBAC enabled:
```python
# Create users with different roles
airflow users create \
  --username data_scientist \
  --firstname Jane \
  --lastname Doe \
  --role Viewer \
  --email jane@company.com
```

**Built-in roles:**
- `Admin` - Full access
- `Op` - Operator (trigger DAGs, view logs)
- `User` - Limited write access
- `Viewer` - Read-only
- `Public` - No authentication required (disable in production!)

---

## Scaling Considerations

### When to Scale

**Symptoms you need to scale:**
- DAG tasks queuing for >5 minutes
- Scheduler lag (tasks not picked up quickly)
- Webserver slow to load UI
- Database connection pool exhausted

### Horizontal Scaling Options

**1. CeleryExecutor (Distributed Workers)**

```yaml
# docker-compose.yml
services:
  airflow-worker:
    <<: *airflow-common
    command: celery worker
    deploy:
      replicas: 3  # Scale to 3 workers
    depends_on:
      - redis

  redis:
    image: redis:7-alpine
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
```

**Pros:**
- Horizontal scaling (add more workers)
- Task isolation (one task crash doesn't kill others)
- Cloud-native (Kubernetes friendly)

**Cons:**
- More complexity (Redis + Celery)
- More moving parts to monitor

**2. KubernetesExecutor (K8s Pods)**

Each task runs in its own Kubernetes pod:

```python
# DAG with pod resources
task = PythonOperator(
    task_id='heavy_ml_task',
    executor_config={
        "pod_override": k8s.V1Pod(
            spec=k8s.V1PodSpec(
                containers=[
                    k8s.V1Container(
                        name="base",
                        resources=k8s.V1ResourceRequirements(
                            requests={"cpu": "4", "memory": "16Gi"},
                            limits={"cpu": "8", "memory": "32Gi"}
                        )
                    )
                ]
            )
        )
    }
)
```

**Pros:**
- Dynamic scaling (pods created on-demand)
- Resource isolation per task
- No Redis/Celery overhead

**Cons:**
- Requires Kubernetes
- Pod startup latency

### Vertical Scaling (LocalExecutor)

**For small-medium workloads:**
```yaml
services:
  airflow-scheduler:
    deploy:
      resources:
        limits:
          cpus: '4'
          memory: 8G
        reservations:
          cpus: '2'
          memory: 4G
```

---

## Monitoring & Observability

### Built-In: Airflow UI
- DAG run history
- Task logs (structured logs from PipelineRunner!)
- Gantt charts, task duration graphs
- Health status (`/health` endpoint)

### Production Monitoring Stack

**1. Metrics Export (Prometheus)**

```python
# airflow.cfg
[metrics]
statsd_on = True
statsd_host = statsd-exporter
statsd_port = 9125
statsd_prefix = airflow
```

```yaml
# docker-compose.yml
services:
  statsd-exporter:
    image: prom/statsd-exporter
    ports:
      - "9102:9102"

  prometheus:
    image: prom/prometheus
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
```

**2. Log Aggregation (ELK Stack)**

```yaml
services:
  elasticsearch:
    image: elasticsearch:8.11.0

  logstash:
    image: logstash:8.11.0

  kibana:
    image: kibana:8.11.0
    ports:
      - "5601:5601"
```

Ship logs to Elasticsearch:
```python
# airflow.cfg
[logging]
remote_logging = True
remote_base_log_folder = elasticsearch://logs
```

**3. OpenTelemetry (Already Integrated!)**

Your PipelineRunner already uses OpenTelemetry for traces and metrics!

**Send to Jaeger:**
```bash
docker run -d --name jaeger \
  -p 16686:16686 \
  -p 4317:4317 \
  jaegertracing/all-in-one:latest
```

Update your metrics server endpoint:
```python
# In run_with_metrics_server.py
OTEL_EXPORTER_OTLP_ENDPOINT=http://jaeger:4317
```

### Alerting

**Health check monitoring:**
```bash
# Simple uptime check
curl -f http://airflow:8080/health || alert_pagerduty

# Task failure alerts (native Airflow)
default_args = {
    'email': ['team@company.com'],
    'email_on_failure': True,
    'email_on_retry': False,
}
```

**Slack/PagerDuty integration:**
```python
from airflow.providers.slack.operators.slack_webhook import SlackWebhookOperator

def task_failure_alert(context):
    slack = SlackWebhookOperator(
        task_id='slack_alert',
        http_conn_id='slack_webhook',
        message=f"Task {context['task_instance']} failed!"
    )
    slack.execute(context)

# Apply to DAG
default_args = {
    'on_failure_callback': task_failure_alert
}
```

---

## Cloud Deployment Examples

### AWS (ECS Fargate + RDS)

```bash
# 1. Build and push image
docker build -t YOUR_ECR_REPO/airflow:latest .
docker push YOUR_ECR_REPO/airflow:latest

# 2. Create RDS PostgreSQL instance
aws rds create-db-instance \
  --db-instance-identifier airflow-db \
  --db-instance-class db.t3.small \
  --engine postgres \
  --master-username airflow \
  --master-user-password STRONG_PASSWORD

# 3. Deploy to ECS Fargate
aws ecs create-service \
  --cluster airflow-cluster \
  --service-name airflow-webserver \
  --task-definition airflow-webserver:1 \
  --desired-count 2
```

### GCP (Cloud Run + Cloud SQL)

```bash
# 1. Build and push
gcloud builds submit --tag gcr.io/PROJECT_ID/airflow

# 2. Create Cloud SQL instance
gcloud sql instances create airflow-db \
  --database-version=POSTGRES_16 \
  --tier=db-f1-micro \
  --region=us-central1

# 3. Deploy to Cloud Run
gcloud run deploy airflow-webserver \
  --image gcr.io/PROJECT_ID/airflow \
  --add-cloudsql-instances PROJECT_ID:us-central1:airflow-db
```

### Azure (Container Apps + PostgreSQL Flexible Server)

```bash
# 1. Push to ACR
az acr build -t airflow:latest -r YOUR_ACR .

# 2. Create PostgreSQL
az postgres flexible-server create \
  --name airflow-db \
  --resource-group airflow-rg \
  --sku-name Standard_B1ms

# 3. Deploy Container App
az containerapp create \
  --name airflow-webserver \
  --resource-group airflow-rg \
  --image YOUR_ACR.azurecr.io/airflow:latest \
  --target-port 8080
```

---

## Production Checklist

Before going to production, ensure:

### Infrastructure
- [ ] Secrets stored in secret manager (not .env)
- [ ] Database has automated backups
- [ ] SSL/TLS enabled for all external traffic
- [ ] Network security groups configured (allow only necessary ports)
- [ ] Resource limits configured (CPU, memory)
- [ ] Health checks enabled on all services

### Airflow Configuration
- [ ] Strong Fernet key generated
- [ ] Default admin password changed
- [ ] RBAC roles configured for team members
- [ ] Email/Slack alerts configured
- [ ] Task retry policy defined
- [ ] SLA monitoring enabled
- [ ] Log retention policy set (7-30 days)

### Monitoring
- [ ] Metrics exported to monitoring system
- [ ] Logs shipped to aggregation service
- [ ] Alerting configured for critical failures
- [ ] Uptime monitoring enabled
- [ ] Dashboard created for key metrics

### CI/CD
- [ ] DAG tests automated (pytest)
- [ ] Docker image builds on merge to main
- [ ] Deployment automated (GitHub Actions, GitLab CI)
- [ ] Rollback procedure documented

---

## Next Steps

1. **Start small:** Use current docker-compose setup for initial deployment
2. **Add secrets:** Migrate to .env with strong passwords (gitignored)
3. **Enable SSL:** Add Nginx reverse proxy with Let's Encrypt
4. **Scale when needed:** Move to CeleryExecutor or Kubernetes
5. **Monitor everything:** Add Prometheus + Grafana

**Questions?** Check the [Airflow Production Deployment Guide](https://airflow.apache.org/docs/apache-airflow/stable/production-deployment.html)
