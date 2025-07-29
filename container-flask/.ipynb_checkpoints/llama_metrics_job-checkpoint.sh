#!/bin/bash

gcloud scheduler jobs create http llama-daily-metrics \
  --schedule="0 7 * * *" \
  --http-method=GET \
  --uri="https://<your-cloud-run-url>/llama/metrics" \
  --time-zone="America/Chicago" \
  --oidc-service-account-email=<SERVICE_ACCOUNT_EMAIL>

# chmod +x scheduler/llama_metrics_job.sh
