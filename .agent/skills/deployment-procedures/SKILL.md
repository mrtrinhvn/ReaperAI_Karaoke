---
name: deployment-procedures
description: Production deployment decision rules. Platform selection, rollback strategy, verification windows.
priority: P2
---

## When to Activate

- Deploying to production or staging
- Planning deployment strategy

# Deployment Rules

> AI model đã biết CI/CD, Docker, PM2, K8s.
> File này chỉ chứa DECISION RULES và CHECKLISTS.

---

## Platform Selection

| Deploying what? | Use |
|---|---|
| Static site / JAMstack | Vercel, Netlify, Cloudflare Pages |
| Simple web app (managed) | Railway, Render, Fly.io |
| Simple web app (control) | VPS + PM2/Docker |
| Microservices | Container orchestration (K8s / Docker Compose) |
| Serverless | Edge functions, Lambda |

## Pre-Deploy Checklist (BẮT BUỘC)

```
[ ] Tests passing
[ ] Production build successful, no warnings
[ ] Env vars verified (all set, secrets current)
[ ] Database migrations ready (if any)
[ ] Rollback plan ready
[ ] Team notified
```

## 5-Phase Workflow

```
PREPARE → BACKUP → DEPLOY → VERIFY → CONFIRM/ROLLBACK
```

- **Prepare**: CẤM deploy untested code
- **Backup**: CẤM deploy without backup. Save current state first
- **Deploy**: Watch it happen. CẤM walk away
- **Verify**: Health check, error logs, key user flows, response times
- **Confirm/Rollback**: Rollback trigger PHẢI ready trước khi deploy

## Verification Windows

| Time | Action |
|---|---|
| 0-5 min | Active monitoring |
| 15 min | Confirm stable |
| 1 hour | Final verification |
| Next day | Review metrics |

## Rollback Rules

| Symptom | Action |
|---|---|
| Service down / Critical errors | **Rollback immediately** |
| Performance >50% degraded | Consider rollback |
| Minor issues | Fix forward if quick |

**Principles:** Speed > perfection. One rollback, not multiple changes. Communicate. Post-mortem after stable.

## Zero-Downtime Strategy Selection

| Scenario | Strategy |
|---|---|
| Standard release | Rolling (replace one by one) |
| High-risk change | Blue-green (easy rollback) |
| Need validation | Canary (gradual traffic shift) |

## Anti-Patterns

- ❌ Deploy Friday. ❌ Rush. ❌ Skip staging. ❌ Skip backup
- ❌ Multiple changes at once. ❌ Walk away after deploy
- ✅ Small frequent deploys. ✅ Feature flags for risk. ✅ Automate. ✅ Test rollback before needing it
