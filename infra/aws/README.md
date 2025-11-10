# COLINK · AWS Infra

This folder holds Infrastructure-as-Code for AWS using Terraform (modules + envs).
- **modules/**: composable building blocks (network, compute, database, observability, security)
- **env/**: per-environment stacks (dev/staging/prod)
- **accounts/**: account-specific config (provider aliases, state backends, tfvars)
- **policies/**: IAM policies as JSON (least-privilege)
- **scripts/**: helper PowerShell/Python for bootstrap & guardrails

> CI/CD uses GitHub OIDC → AWS (no long-lived keys). Local auth via `AWS_PROFILE`.
