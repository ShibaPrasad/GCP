a full set of templates to deploy your Flask + LLaMA-2 API using Cloud Run, Cloud Build, and Cloud Scheduler, with optional support for React frontend .env config.
# ----------------------------------------------------------------------------
1. Dockerfile for Flask + LLaMA2 (CPU)
Place this in the root of your backend project:
# Dockerfile
FROM python:3.10-slim

ENV PYTHONUNBUFFERED=True

WORKDIR /app
COPY . /app

# Install system packages
RUN apt-get update && apt-get install -y \
    git gcc g++ libglib2.0-0 libsm6 libxext6 libxrender-dev curl && \
    rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip install --no-cache-dir torch==2.1.0 torchvision==0.16.0 torchaudio==2.1.0 \
    transformers flask flask-restx flask-cors flask-sqlalchemy pandas scikit-learn matplotlib seaborn

EXPOSE 5089

CMD ["python", "app.py"]

# ----------------------------------------------------------------------------
2. cloudbuild.yaml for Cloud Build & Cloud Run Deploy
Place in your backend root (same level as Dockerfile):
# cloudbuild.yaml
steps:
  - name: 'gcr.io/cloud-builders/docker'
    args: ['build', '-t', 'gcr.io/$PROJECT_ID/llama-cls-api', '.']

  - name: 'gcr.io/cloud-builders/docker'
    args: ['push', 'gcr.io/$PROJECT_ID/llama-cls-api']

  - name: 'gcr.io/google.com/cloudsdktool/cloud-sdk'
    entrypoint: gcloud
    args:
      - run
      - deploy
      - llama-cls-api
      - --image=gcr.io/$PROJECT_ID/llama-cls-api
      - --platform=managed
      - --region=us-central1
      - --allow-unauthenticated
      - --port=5089
# ----------------------------------------------------------------------------
3. React Frontend .env Template
Place this in the root of your React frontend:

# .env
REACT_APP_API_URL=https://<your-cloud-run-url>
Update your axios base URL in React code:

const backendUrl = process.env.REACT_APP_API_URL;

# ----------------------------------------------------------------------------
4. Create a Cloud Scheduler Job (Daily Metrics Export)
Replace placeholders before running in the terminal:
      Create a "llama_metrics_job.sh" and include the below line of code and save it. Make it executable "chmod +x scheduler/llama_metrics_job.sh"
      gcloud scheduler jobs create http llama-daily-metrics --schedule="0 7 * * *" --http-method=GET --uri="https://<your-cloud-run-url>/llama/metrics" --time-zone="America/Chicago" --oidc-service-account-email=<SERVICE_ACCOUNT_EMAIL>

To get the service account email:    gcloud iam service-accounts list

Grant Cloud Run access:              gcloud run services add-iam-policy-binding llama-cls-api --member="serviceAccount:<SERVICE_ACCOUNT_EMAIL>" --role="roles/run.invoker" --region=us-central1
# ----------------------------------------------------------------------------
  
5. Build & Deploy via Cloud Build:   gcloud builds submit --config cloudbuild.yaml

# ----------------------------------------------------------------------------
Folders/Files:

    - app.py	                          Your full Flask API (already shared)
    - Dockerfile	                      Container setup for Flask + transformers + dependencies
    -cloudbuild.yaml	                  CI/CD steps: build, push, deploy to Cloud Run
    -.gcloudignore	                      (Optional) Ignore logs, .git, etc. when using gcloud builds submit
    -scheduler/llama_metrics_job.sh	      Shell script to set up Cloud Scheduler job via CLI
    -scripts/test_local.sh	              Useful for testing curl endpoints locally
    -models/	                          Optional: Store HF model/tokenizer if you want local access
    -db/clinical_notes.db	              Optional: SQLite DB if running locally
    -README.md	                          Document all GCP steps, local dev, endpoints, build instructions

# ----------------------------------------------------------------------------