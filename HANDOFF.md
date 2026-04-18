# Handoff

Short repo-tracked handoff for the Walmart / Marketplace Eligibility Engine workspace.

## Status Snapshot

As of Apr 17, 2026 PST:

- Workspace was synced to `origin/main` before archive.
- Production URL: `https://walmart.kevinastuhuaman.com`
- Deploy target: AWS Lightsail Docker Compose stack
- Repo workflow is PR-first:
  - work from a Conductor workspace/worktree branch
  - never push directly to `main`
  - deploy only from merged `main`

## What This Phase Added

- React frontend is the live experience for the Walmart demo.
- Mobile product-detail layout regression was fixed.
- Playwright coverage exists for:
  - live smoke flows
  - mobile product-detail layout regression
- Repo governance was hardened:
  - repo-local workflow rules in `AGENTS.md`
  - GitHub CI in `.github/workflows/ci.yml`
  - branch-protected PR workflow is the intended path going forward

## Start Here Next Time

- Product and architecture overview: `README.md`
- Architectural and operational rationale: `DESIGN_DECISIONS.md`
- Repo workflow and validation rules: `AGENTS.md`
- CI gates: `.github/workflows/ci.yml`
- Frontend live smoke tests: `frontend/e2e/live-smoke.spec.ts`
- Mobile regression test: `frontend/e2e/product-detail-layout.spec.ts`

## Validation Commands

```bash
cd frontend && npm run build
cd frontend && npx playwright test e2e/product-detail-layout.spec.ts
cd frontend && PLAYWRIGHT_BASE_URL=https://walmart.kevinastuhuaman.com npm run test:e2e
pytest tests/test_evaluator.py -v
pytest tests/test_scenarios.py -v
```

## Deployment Notes

- Production deploys should rebuild and recreate only the services that changed.
- The production stack runs on Lightsail, not Vercel or Render.
- For frontend/UI work, browser-level validation is the source of truth. Use Playwright or equivalent browser automation, not curl-only smoke checks.

## Archive Note

The repo now contains the durable code, tests, workflow rules, and this handoff summary. Some session artifacts still live only in `.context/`, so keep the archived workspace if you want the full review trail.
