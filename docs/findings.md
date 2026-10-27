# VulnTracker Security Findings

## Scope and assessment approach

This assessment covers the Python FastAPI API, the shared-report feature, pinned Python dependencies, the container image, the Node.js dependency report, and Kubernetes deployment configuration. Findings combine automated scan results with manual code review.

Severity reflects potential impact on this application, not just a scanner's default classification. Scanner results should be regenerated after significant code, dependency, or image changes.

## Prioritised findings

| ID | Finding | Source / scan type | Severity and rationale | Business impact | Origin | Status |
|---|---|---|---|---|---|---|
| F-01 | SQL injection risk in scan search | Manual review / SAST | High before remediation: interpolating user input into SQL could allow query manipulation. | An attacker could expose or alter scan records belonging to other users. | Starter code | Remediated using parameterized SQL and owner filtering. |
| F-02 | Scan access not consistently scoped to the authenticated owner | Manual review | High before remediation: missing ownership checks can expose other users' scan records. | Confidential vulnerability information could be disclosed or modified. | Starter code | Owner checks added to scan operations and sharing. |
| F-03 | JWT validation and signing-secret handling needed strengthening | Manual review | High before remediation: weak or improperly validated tokens can undermine authentication. | Unauthorized access to scan data and administrative functionality. | Starter code | JWT validation strengthened; signing secret is configured through the environment or generated randomly at startup. |
| F-04 | Shared-report links require robust token, expiry, and password checks | Manual review and API tests | High if implemented incorrectly: public links can bypass normal authentication by design. | External parties could access sensitive scan results without authorization. | New feature | Cryptographically random tokens, 24-hour expiry, optional hashed password, and tests for invalid and expired links implemented. |
| F-05 | Password-protected share password is supplied in a query parameter | Manual review | Medium residual risk: URLs may be recorded in browser history, proxy logs, or access logs. | A leaked URL or log entry could expose a protected vulnerability report. | New feature | Retained to satisfy the API requirement; use HTTPS, redact query strings from logs, and consider a POST-based password exchange for production. |
| F-06 | Node.js dependency vulnerabilities reported | `npm audit` / SCA | High priority for triage because the original report identified 11 vulnerabilities: 3 low, 2 moderate, 5 high, and 1 critical. Confirm current affected packages and fixed versions before assigning final severity. | A vulnerable notification service could be compromised or used to disrupt notification delivery. | Starter code | Requires verification against the current dependency lockfile and a refreshed audit. |
| F-07 | Python dependency vulnerability report needs to match the final installed versions | `pip-audit` / SCA | Prior report found no known vulnerabilities in the pinned Python requirements. Container scanning also showed package-version discrepancies requiring validation. | Unpatched dependencies could expose the API to known vulnerabilities. | Starter code / deployment | Refresh `pip-audit` and verify installed package versions in the final image. |
| F-08 | Container scan reports operating-system and Python package findings | Trivy / container scan | Prior image report included OS-package findings and Python package findings. Prioritize confirmed critical/high issues, check fixed versions, and rebuild before release. | Exploitation of vulnerable libraries or OS packages could affect confidentiality, integrity, or service availability. | Deployment | Image rebuilt with pinned Python dependencies and OS package upgrades. Residual findings require review against the final image and authoritative advisories. |
| F-09 | Container scanner reported inconsistent package inventories | Trivy / container scan, manual triage | Investigation required: the report included older SBOM-derived package records alongside newer runtime package records. Do not treat all duplicate records as confirmed vulnerabilities without validation. | Incorrect triage can hide genuine vulnerabilities or waste remediation effort. | Deployment | Verify against the final image's installed package versions and current vulnerability advisories. |
| F-10 | Kubernetes deployment originally configured multiple replicas with SQLite on one persistent volume | Manual infrastructure review | High for a multi-replica deployment: SQLite and a shared ReadWriteOnce volume are unsuitable for this design. | Concurrent access, database locking, storage limitations, or service disruption. | Deployment | Replica count reduced to one. Migrate to managed PostgreSQL before scaling production replicas. |
| F-11 | IaC scan reported no failed misconfiguration checks in the captured result | Trivy / IaC scan | No confirmed failed checks in the saved report; this is not proof that the deployment is secure in every environment. | Undetected configuration weaknesses could expose the service or its data. | Deployment | Review alongside manual controls and validate again against the target cluster. |
| F-12 | Bandit reported a possible hardcoded password at the OAuth bearer-token declaration | Bandit / SAST | Low; likely a false positive because `bearer` describes the authentication scheme, not a password or secret. | Misclassification can distract from genuine hardcoded credentials. | Starter code | Retain the correct authentication scheme and document the finding as a false positive after code review. |

## Implemented security controls

- Parameterized SQL and scan-owner authorization.
- JWT signature and expiration validation.
- Random share tokens with a 24-hour expiration.
- Optional password protection using password hashes.
- Tests for valid, invalid, expired, and password-protected share links.
- Non-root Docker execution, health check, and no embedded credentials in the Dockerfile.
- Kubernetes resource requests and limits, restricted service exposure, security contexts, and external-secret integration.

## Limitations

The results reflect the reports captured during this assessment. They are not a guarantee that the application is vulnerability-free. Refresh all scans after dependency or image changes, validate the final CI results, and verify any remaining critical/high findings against current advisories before production use.