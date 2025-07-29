# Base image: CUDA 12.6.2 with UBI8 for GPU support
FROM nvcr.io/nvidia/cuda:12.6.2-base-ubi8

# Set the working directory inside the container
WORKDIR /app

# Update base and install Python 3.11 + build tools
RUN dnf update -y && \
    dnf install -y \
        python3.11 \
        python3.11-pip \
        python3.11-devel \
        gcc \
        gcc-c++ \
        git && \
    dnf clean all && \
    rm -rf /var/cache/dnf

# Set Python 3.11 as the default version
RUN alternatives --install /usr/bin/python python /usr/bin/python3.11 1 && \
    alternatives --install /usr/bin/pip pip /usr/bin/pip3.11 1

# Copy Python dependencies and install them
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy your FastAPI app code
COPY app/ ./app/

# Ensure models directory exists
RUN mkdir -p /app/models/Meta-Llama-3-8B/

# Copy LLaMA 3 model files
COPY ./models/Meta-Llama-3-8B/config.json ./models/Meta-Llama-3-8B/
COPY ./models/Meta-Llama-3-8B/tokenizer.model ./models/Meta-Llama-3-8B/
COPY ./models/Meta-Llama-3-8B/model-00001-of-00004.safetensors ./models/Meta-Llama-3-8B/
COPY ./models/Meta-Llama-3-8B/model-00002-of-00004.safetensors ./models/Meta-Llama-3-8B/
# Add other model shards as needed...

# Expose FastAPI default port
EXPOSE 8080

# Podman-compatible entrypoint to run FastAPI via Uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]


