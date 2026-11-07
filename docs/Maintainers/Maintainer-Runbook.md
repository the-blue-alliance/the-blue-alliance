## Bumping the GAE/Python Runtime

Bumping the Python version requires that Google App Engine supports the new Python version in the [Python 3 runtime](https://cloud.google.com/appengine/docs/standard/python3/runtime) and that our dependencies support the new Python version. If the new Python version is supported and can be bumped safely, follow these steps:

1. Update the version in `.python-version`
2. Run `./ops/check_python_version.sh --update` to update all dependent files:
   - `pyproject.toml` (`requires-python`)
   - GAE service `.yaml` files (`runtime:` directive)
   - GitHub Actions workflow files (`python-version:`)
3. Verify the changes: `./ops/check_python_version.sh`

## Running One-Off Data Migrations/Cleanups

See the [[Local Shell|Local-Shell]] documentation for running one-off cleanup or migration scripts against the production database. You will need a production service account key to run scripts against the production database. **Be extremely careful before running scripts against the production database.**

## Container Images and Rolling Back a Deploy

### Where images live

| Location | What's in it | Retention |
|---|---|---|
| Artifact Registry `gae-standard` (`us-central1`) | `app/<service>`: one image per App Engine deploy, tagged with the deploy operation ID. `build-cache/<service>`: buildpack cache. | [`ops/artifact-registry-cleanup-policy.json`](../../ops/artifact-registry-cleanup-policy.json): delete after 30 days, but always keep the 10 most recent per package |
| Artifact Registry `gcr.io` (`us`) | Images pulled as `gcr.io/tbatv-prod-hrd/...` (`gcr.io` redirects here). CI pulls `tba-offseason-companion-import:latest` from it. | None |

App Engine starts new instances of the serving version from its `app/<service>` image. Never hand-delete the newest image of an `app/*` package. The cleanup policy's keep-10 rule exists to protect it.

### Rolling back

Every service deploys in place to version `1` (`ops/deploy/deploy_module.sh`), so there is no older version to shift traffic back to. The stored images can't be redeployed either: `gcloud app deploy --image-url` is App Engine flexible only. A rollback is a rebuild from source:

1. **Preferred:** revert the bad commit on `main` and let the push workflow redeploy.
2. **Urgent, with maintainer credentials:** for each affected service, find the most recent good run of the push workflow (`.github/workflows/push.yml`) whose deploy job for that service actually deployed, and re-run that job. Each deploy job skips its steps unless that commit changed the service's files, so re-running a run that skipped it does nothing. GitHub only allows re-runs within 30 days of the original run; past that, use option 1.
3. **Deploying from a local checkout:** only `default`, `tasks_io`, `tasks_cpu` and `tasks_cpu_enqueue` can be deployed with just `./ops/deploy/deploy_module.sh src/<service>.yaml`. The others need the setup their push jobs do first:
   - **`web` and `api`:** both include `src/env_variables.yaml`, whose checked-in `FLASK_SECRET_KEY` is the dev value. Run `FLASK_SECRET_KEY=<prod secret> ./ops/deploy/update_env_variables_yaml.sh` first. Deploying the dev key logs everyone out and lets anyone forge session cookies.
   - **`web`:** also serves `src/build/css` and `src/build/javascript`, which aren't in git. Build them first (`npm run build`), or the deploy ships stale or missing assets.
   - **PWA:** needs `pwa/build` and `pwa/server.js` built with the production `VITE_*` variables, and `NEXUS_API_KEY` added to a copy of `pwa/pwa.yaml` (see the `deploy-pwa` job). `pwa/pwa.yaml` on its own doesn't work.

Python dependencies come from `uv.lock`, so a rebuild of an old commit gets the same packages. The App Engine base runtime image may be newer than it was at the original deploy.
