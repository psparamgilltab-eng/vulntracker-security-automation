# VulnTracker Security Automation

VulnTracker is a Python FastAPI service for managing vulnerability scan results. This project adds secure report sharing and includes security scans, remediation documentation, a Docker image, and Terraform configuration for Kubernetes deployment.

## Features

- Create, view, search, update, and delete scan records.
- Restrict scan access to the authenticated owner.
- Share an individual scan through a unique link.
- Set an optional password for shared reports.
- Expire shared links after 24 hours.
- Run automated tests for the API and notification service.
- Store security scan reports and document outstanding risks.

## Technologies

- Python 3.11 and FastAPI
- Node.js and Express
- Docker
- Terraform and Kubernetes
- Bandit, pip-audit, npm audit, and Trivy

## Requirements

Install Python 3.11, Node.js 20 or later, npm, and Docker. Terraform and a configured Kubernetes cluster are needed only for deployment.

## Run the Python API

From the repository root, create and activate a virtual environment:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Run the API from the `app` directory:

```powershell
Set-Location app
python -m uvicorn main:app --reload
```

The API is available at http://localhost:8000.

Interactive API documentation is available at http://localhost:8000/docs.

## Run the notification service

Open a separate terminal from the repository root:

```powershell
Set-Location notify
npm install
npm start
```

The notification service listens on port 3001.

## Run the tests

Run the Python tests from the repository root:

```powershell
python -m pytest tests -v
```

Run the notification service tests:

```powershell
Set-Location notify
npm test
```

During local verification, all 17 Python tests and all 8 notification-service tests passed.

## Build and run with Docker

Build the API image from the repository root:

```powershell
docker build -t vulntracker:local .
```

Generate a temporary strong secret for local testing:

```powershell
$secret = python -c "import secrets; print(secrets.token_urlsafe(48))"
```

Create persistent storage and start the container:

```powershell
docker volume create vulntracker-data

docker run -d --name vulntracker `
  -p 8000:8000 `
  -v vulntracker-data:/data `
  -e SECRET_KEY="$secret" `
  vulntracker:local
```

Check the health endpoint:

```powershell
Invoke-WebRequest http://localhost:8000/health -UseBasicParsing
```

View container logs:

```powershell
docker logs vulntracker
```

Remove the test container when finished:

```powershell
docker rm -f vulntracker
```

Never commit real secrets to source control. For production, use an appropriate secrets manager.

## Kubernetes deployment with Terraform

The `terraform/` directory contains Kubernetes resources for the API, including a namespace, service account, persistent storage, a ClusterIP service, network restrictions, resource limits, security contexts, health probes, and an External Secrets Operator resource.

Prerequisites:

- Terraform and a configured Kubernetes cluster
- A working Kubernetes context and kubeconfig
- External Secrets Operator and a configured `ClusterSecretStore`
- The required external secret and storage support

Format and validate the configuration:

```powershell
terraform -chdir=terraform fmt
terraform -chdir=terraform validate
```

Review the proposed changes before deployment:

```powershell
terraform -chdir=terraform plan
```

Apply only after verifying the target cluster, secret configuration, ingress restrictions, and storage settings:

```powershell
terraform -chdir=terraform apply
```

The configuration uses one replica because the application currently uses SQLite. A production deployment requiring multiple replicas should migrate to a shared database such as PostgreSQL and include backup and recovery controls.

Terraform validation has passed, but a live Kubernetes deployment has not been verified.

## Security assessment

The `reports/` directory contains the scan outputs:

| Scan category | Tool | Report |
|---|---|---|
| SAST | Bandit | `reports/sast.bandit.json` |
| Python dependencies | pip-audit | `reports/sca.pip-audit.json` |
| Node.js dependencies | npm audit | `reports/sca.npm-audit.json` |
| Container image | Trivy | `reports/container.trivy.json` |
| Container SBOM | Trivy | `reports/container-sbom.json` |
| Infrastructure as Code | Trivy | `reports/iac.trivy.json` |

The security documentation is available here:

- `docs/findings.md` — prioritized findings and their business impact.
- `docs/remediation-plan.md` — completed fixes, remaining risks, and recommended controls.
- `docs/executive-summary.md` — overall security posture and recommended next steps.

Scan results should be reviewed against the final code and image before production use.

## CI

The GitHub Actions workflow runs the project's automated checks.

[View the CI workflow](https://github.com/psparamgilltab-eng/vulntracker-security-automation/actions)

