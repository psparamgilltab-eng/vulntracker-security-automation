# VulnTracker Remediation Plan

## Purpose

This plan records security improvements implemented during the assignment, remaining risks, estimated remediation effort, and compensating controls. Effort estimates are indicative and assume an engineer familiar with the application.

## Completed remediations

| Priority | Issue | Remediation implemented | Validation |
|---|---|---|---|
| High | SQL injection risk | Replaced unsafe query construction with parameterized SQL. Search results are scoped to the authenticated owner. | Python API tests and code review. |
| High | Inconsistent scan authorization | Added ownership checks to scan access and sharing operations. | API tests include attempts to share another user's scan. |
| High | JWT validation | Strengthened token decoding, algorithm validation, expiry handling, and required claims. | Authentication tests. |
| High | Shared-report access control | Added cryptographically random tokens, a 24-hour expiry, optional hashed password protection, and rejection of invalid or expired links. | Share-feature tests. |
| High | Container execution privileges | Configured a dedicated non-root user, health check, and a minimal Python base image. | Docker image build and HTTP health check returned 200 OK. |
| Medium | Kubernetes workload hardening | Added resource limits, security contexts, a ClusterIP service, ingress restrictions, and external-secret integration. | `terraform validate` succeeded; IaC scan saved in `reports/iac.trivy.json`. |
| Medium | SQLite multi-replica design | Reduced deployment replicas to one to avoid unsafe concurrent use of the SQLite database on a single persistent volume. | Terraform configuration review and validation. |

## Residual risks and planned actions

| Priority | Residual risk | Why not fully remediated | Estimated effort | Compensating controls / next steps |
|---|---|---|---|---|
| Critical/High, subject to verification | Node.js dependency vulnerabilities | The captured npm audit reported 11 vulnerabilities. Current affected dependencies and available fixes must be confirmed before declaring the issue resolved. | 2–8 hours, depending on breaking changes | Refresh `npm audit`, update affected packages, run notification-service tests, and rebuild the service. |
| High, subject to verification | Container OS and package findings | The image scan reported multiple findings, and its package inventory contained records requiring reconciliation with installed versions. | 2–8 hours for triage and patching; longer if application compatibility changes are needed | Confirm affected packages and fixed versions, rebuild the image, rescan it, and retain the final JSON report. |
| Medium | Password supplied through a URL query parameter | The assignment specifies this interface, but query strings can be logged or retained by clients and intermediaries. | 2–4 hours to design and test an alternative flow | Use HTTPS, redact query strings from logs, apply short retention to access logs, and consider a POST-based password exchange. |
| High before production scaling | SQLite storage and single-replica deployment | The prototype currently uses SQLite and a persistent volume. This does not provide a robust, highly available multi-replica database design. | 1–3 days for a basic managed PostgreSQL migration; longer for production migration and testing | Keep one replica, back up the database, test recovery, and migrate to managed PostgreSQL before scaling. |
| Medium | Secret-store and cluster configuration dependencies | Terraform references an external secret store and an existing Kubernetes environment; validation alone does not prove these services are configured securely or operationally. | 4–8 hours for environment integration and verification | Restrict secret-store IAM access, verify secret rotation, test deployment in a non-production cluster, and audit network policies. |
| Medium | Share-link lifecycle and operational monitoring | The implementation validates token expiry and password protection, but production operations still need monitoring, abuse detection, and a defined revocation process. | 4–8 hours | Monitor failed password attempts, redact share tokens from logs, alert on suspicious access, and test revocation and expiry behavior. |

## Release gates

Before production release:

1. Run the complete Python and Node.js test suites.
2. Refresh SAST, Python SCA, Node.js SCA, container, and IaC scans against the final code and image.
3. Investigate all confirmed critical/high findings and document any accepted risks with an owner and deadline.
4. Verify secret retrieval and rotation in the target environment.
5. Test authorization, password protection, expiration, revocation, backup, and recovery.
6. Confirm that no credentials, local environment files, or temporary image archives are committed.
7. Require green CI and peer review before deployment.

## Risk acceptance

Any remaining critical or high finding must be explicitly reviewed and accepted by the responsible security or engineering owner. A clean scan or a successful Terraform validation does not, by itself, establish production readiness.