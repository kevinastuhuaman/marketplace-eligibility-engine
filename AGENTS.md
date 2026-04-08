# AGENTS.md

Repo-specific rules for `walmart-transactability`.

## Workflow

- Always work from a Conductor workspace/worktree branch.
- Never push directly to `main`.
- Open a pull request for every change, including hotfixes, unless Kevin explicitly approves bypassing the PR flow.
- Deploy only from merged `main`.

## Validation

- Frontend/UI changes:
  - `cd frontend && npm run build`
  - `cd frontend && npx playwright test e2e/product-detail-layout.spec.ts`
- Live-site verification after deploy:
  - `cd frontend && PLAYWRIGHT_BASE_URL=https://walmart.kevinastuhuaman.com npm run test:e2e`
- Rule-engine/backend changes:
  - `pytest tests/test_evaluator.py -v`
- Full-stack scenario validation when the Docker stack is available:
  - `pytest tests/test_scenarios.py -v`

## Production

- Production URL: `https://walmart.kevinastuhuaman.com`
- Production deploy target is the Lightsail host running the Docker Compose stack.
- For deploys, rebuild and recreate only the services that changed.

## Safety

- Do not bypass branch protection or merge requirements unless Kevin explicitly asks for an emergency override.
- Do not treat the absence of GitHub enforcement as permission to skip the PR workflow.
