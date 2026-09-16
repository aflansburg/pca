## Purpose

Minimal Terraform to deploy the Primary Care Atlas to **Google Cloud Run** in region `us-central1`. Can easily be reswizzled to deploy to AWS.

The FastAPI process serves the built Vue SPA, the API, and the committed `data/db/atlas.duckdb` on `$PORT` from a single service. The image is built from the repo-root `Dockerfile` and artifact pushed to Google Artifact Registry.

Applied locally, there is no CD job (see the top-level README). State lives local, ideally this would be in a GCS bucket.

## What Terraform manages

- `google_artifact_registry_repository`: the Docker repo for the image.
- `google_cloud_run_v2_service`: the service (1 CPU, 1Gi, scale 0→2).
- `google_cloud_run_v2_service_iam_member`: public access (`allUsers` → `roles/run.invoker`),
  toggled by `allow_unauthenticated` (default `true`).

The container image is built and pushed out of band with `gcloud` (Cloud Build), but in the future would be handled by a CI/CD pipeline.

## Deploy (local apply - can be scripted in the future)

Prereqs: `gcloud auth login` (account with access to a GCP project) and `terraform >= 1.9`.

```sh
cd app/infra
terraform init

# 1: Use targeted apply to create the Artifact Registry repo first
terraform apply -target=google_artifact_registry_repository.repo

# 2: Build + push the image (run from the REPO ROOT, not app/infra).
cd ../..
gcloud builds submit --project <PROJECT_ID> \
  --tag us-central1-docker.pkg.dev/<PROJECT_ID>/primary-care-atlas/primary-care-atlas:latest .

# 3: Deploy Cloud Run service.
cd app/infra
terraform apply

# output the service url
terraform output service_url
```

## Redeploy

Bump `image_tag` and `terraform apply` to keep TF state as source of truth.

## Variables

`project_id`, `region`, `service_name`, `repository`, `image_tag`, `allow_unauthenticated` — see
`variables.tf`. Set `-var 'allow_unauthenticated=false'` to make the service private.

## Teardown

```sh
terraform destroy
```
