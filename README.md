# Kernel Panic Dashboard 🚨

A real-time cybersecurity intelligence dashboard running on the terminal. It aggregates security news streams, processes them using a RAG (Retrieval-Augmented Generation) pipeline, and provides an AI-powered chat interface to query the data.

**Stack:** Python, Textual (TUI), Pathway (Stream Processing), Ollama (Local LLM), Docker.

## 📋 Prerequisites

* **OS:** Linux or macOS (Windows users should use WSL2).
* **Python:** 3.10 or higher.
* **Ollama:** Installed and running (`ollama serve`).

---

## 🚀 Quick Start (Automated Scripts)

The easiest way to run the project locally on your machine.

1.  **Clone the repository:**
    ```bash
    git clone [https://github.com/vatsalj17/cyber-news.git](https://github.com/vatsalj17/cyber-news.git)
    cd cyber-news
    ```

2.  **Run the Setup Script:**
    This creates a virtual environment, installs dependencies, and pulls the AI model.
    ```bash
    chmod +x setup.sh
    ./setup.sh
    ```

3.  **Start the Dashboard:**
    ```bash
    chmod +x start.sh
    ./start.sh
    ```
    *Use `Ctrl+C` to exit. The script will automatically clean up background processes.*

---

## 🛠 Manual Installation & Run

If you prefer to configure things yourself step-by-step.

1.  **Prepare the Environment:**
    ```bash
    python3 -m venv .venv
    source .venv/bin/activate
    pip install -r req.txt
    playwright install chromium
    ```

2.  **Ensure AI is Ready:**
    Make sure Ollama is running in a separate terminal and the model is pulled:
    ```bash
    ollama pull phi3
    ```

3.  **Run the Components:**
    You need to run these in separate terminals or background them.

    * **Terminal 1 (Data Producer):**
        ```bash
        python3 producer.py
        ```
    * **Terminal 2 (RAG Pipeline):**
        ```bash
        python3 pipeline.py
        ```
        *Wait until you see "Starting RAG Server on 0.0.0.0:9000"*

    * **Terminal 3 (UI):**
        ```bash
        python3 dashboard.py
        ```

---

## 🐳 Docker Methods

### Option A: Docker Compose (Recommended)
This runs the Dashboard and a dedicated Ollama container together.

1.  **Run the stack:**
    ```bash
    docker-compose up --build
    ```
    *Note: The first run will take time as it downloads the 2GB+ LLM model.*

2.  **Access:**
    Attach to the dashboard container to see the TUI:
    ```bash
    docker attach cyber_news_dashboard
    ```

### Option B: Build & Run Locally
If you want to run the image but use your **host's** existing Ollama instance.

1.  **Build the image:**
    ```bash
    docker build -t cyber-news:local .
    ```

2.  **Run the container:**
    * **Linux:** Use `--network host` to let the container access your local Ollama on port 11434.
        ```bash
        docker run -it --network host cyber-news:local
        ```
    * **Mac/Windows:** Use `host.docker.internal` for networking.
        ```bash
        docker run -it -e OLLAMA_HOST="[http://host.docker.internal:11434](http://host.docker.internal:11434)" -p 9000:9000 cyber-news:local
        ```

### Option C: Remote Docker Image
Pull the pre-built image from Docker Hub (if available).

```bash
docker run -it --network host vatsalj17/cyber-news:latest
