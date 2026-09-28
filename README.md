# FastAPI RAG API Container

A lightweight, production-ready Retrieval-Augmented Generation (RAG) API built with **FastAPI**, **ChromaDB**, **Sentence-Transformers**, and **Google GenAI**. Designed to run efficiently inside Docker using CPU-optimized dependencies.

---

## 📁 Project Structure

```text
.
├── .dockerignore         # Specifies files ignored by Docker build
├── .env                  # Environment variables (API keys, config)
├── .gitignore            # Git exclusion rules
├── Dockerfile            # Container configuration and build steps
├── docs/                 # Document store for RAG indexing
└── app/
    ├── app.py            # Supplementary scripts/utilities
    ├── rag_api.py        # Core FastAPI application & RAG logic
    └── requirements.txt  # Python package requirements
```

---

## 🚀 Prerequisites

Ensure you have the following installed on your machine or environment:
* [Docker Desktop](https://www.docker.com/products/docker-desktop/) or Docker Engine
* [Python 3.11+](https://www.python.org/) (for local development without Docker)
* A valid Google Gemini API Key

---

## ⚙️ Environment Setup

Create a `.env` file in the root directory of the project:

```bash
GOOGLE_API_KEY=your_google_gemini_api_key_here
PORT=8000
```

> **Security Note:** Never commit your `.env` file to version control.

---

## 🐳 Running with Docker

### 1. Build the Docker Image

Run the build command from the root directory:

```bash
docker build -t my-rag-api .
```

### 2. Launch the Container

Run the container in detached mode, exposing port `8000`, passing your `.env` file, and mounting the `docs/` directory:

```bash
docker run -d \
  --name my-rag-api \
  -p 8000:8000 \
  --env-file .env \
  -v "$(pwd)/docs:/workspace/app/docs" \
  my-rag-api
```

### 3. Check Logs

Monitor the container logs in real time:

```bash
docker logs -f my-rag-api
```

---

## 🧪 Testing the API

### Interactive API Documentation (Swagger UI)

Once the container is running, access the interactive Swagger UI at:
👉 **[http://localhost:8000/docs](http://localhost:8000/docs)**

### Health Check Request

```bash
curl -X GET http://localhost:8000/health
```

### Sending a RAG Query Request

```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "What information is available in the uploaded documents?"
  }'
```

---

## 🛠 Useful Container Maintenance Commands

* **Stop the running container:**
  ```bash
  docker stop my-rag-api
  ```
* **Remove the container:**
  ```bash
  docker rm -f my-rag-api
  ```
* **Clean up unused Docker storage & cache:**
  ```bash
  docker system prune -a --volumes -f
  ```