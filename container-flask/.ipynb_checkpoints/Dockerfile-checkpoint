# Dockerfile
FROM python:3.10-slim

ENV PYTHONUNBUFFERED=True

WORKDIR /app
COPY . /app

# System dependencies
RUN apt-get update && apt-get install -y \
    git gcc g++ libglib2.0-0 libsm6 libxext6 libxrender-dev curl && \
    rm -rf /var/lib/apt/lists/*

# Install Python packages
RUN pip install --no-cache-dir torch==2.1.0 torchvision==0.16.0 torchaudio==2.1.0 \
    transformers flask flask-restx flask-cors flask-sqlalchemy pandas scikit-learn matplotlib seaborn

EXPOSE 5089

CMD ["python", "app.py"]


