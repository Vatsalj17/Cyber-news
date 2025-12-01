# Real-Time Cyber Intelligence Platform

> **Status:** Active | **Architecture:** x86_64 (Linux) | **Engine:** Pathway + Ollama

**Cyber News** is a next-generation security intelligence aggregator that bridges the gap between raw data streams and Generative AI. Unlike traditional static dashboards, this platform utilizes a **streaming data pipeline** to ingest, process, and vectorize cybersecurity news, CVEs, and exploit feeds in real-time.

It leverages **Retrieval-Augmented Generation (RAG)** to allow security analysts to chat with the live data stream, asking questions like *"What are the latest heap exploits in the Linux kernel?"* and receiving answers grounded in data collected seconds ago.

---

## 🚀 Why This Project?

In the fast-paced world of cybersecurity, yesterday's news is irrelevant. Static databases cannot keep up with Zero-Day exploits.

* **⚡ True Real-Time Processing**: Powered by **Pathway**, we don't just batch process data; we treat information as a continuous stream. As soon as a vulnerability is posted on a tracker, it flows through our pipeline.
* **🔒 Local Privacy First**: Uses **Ollama (Phi-3)** running locally. No data leaves your machine. Your intelligence queries remain confidential.
* **🧠 Dynamic Context**: The RAG engine updates its vector store dynamically. You aren't querying a model trained months ago; you are querying a model equipped with the context of *right now*.
* **💻 Triple-Threat Interface**: Whether you prefer a Web UI, a TUI (Terminal User Interface), or a CLI, we have you covered.

---

## ⚠️ Compatibility Warning

* **OS**: This project is optimized for **Linux** distributions (Arch, Debian, Fedora, etc.).
* **Architecture**: The Docker builds and binaries are targeted for **x86_64**.
* **MacOS Users**: If you are on Apple Silicon (M1/M2/M3), please switch to the **`mac_os_arm_64`** branch for ARM-compatible builds.

---

## 🛠️ Installation & Setup Guide

We believe in flexibility. Choose the deployment method that fits your workflow.

### Prerequisites
* **Git** (`sudo pacman -S git` or `sudo apt install git`)
* **Docker Engine** (For Docker methods)
* **Python 3.11+** (For manual/script methods)

---

### Method 1: Docker Compose (⭐⭐⭐⭐⭐ Recommended)
*Best for: Users who want a "one-click" deployment with zero configuration.*

This method orchestrates the AI model (Ollama), the Data Pipeline, and the Dashboard in isolated containers.

1.  **Clone the repository**:
    ```bash
    git clone [https://github.com/vatsalj17/cyber-news.git](https://github.com/vatsalj17/cyber-news.git)
    cd cyber-news
    ```

2.  **Launch the Stack**:
    ```bash
    docker-compose up
    ```

    > **Note:** The first launch will take a few minutes as it automatically pulls the `Phi-3` LLM model and builds the scraper container.

3.  **Access the Dashboard**:
    * **Web UI**: Open [http://localhost:5001](http://localhost:5001) in your browser.
    * **CLI**: The terminal window will attach to the CLI dashboard automatically.

---

### Method 2: Dockerfile Build
*Best for: Users who want to build the image manually or debug the container internals.*

1.  **Build the Image**:
    ```bash
    docker build -t cyber-news:latest .
    ```

2.  **Run the Container**:
    Since the app needs to talk to a local Ollama instance or manage its own networking, the easiest way on Linux is to use the host network driver:
    
    ```bash
    docker run --network host -it cyber-news:latest
    ```

---

### Method 3: Automated Setup Script
*Best for: Linux users running natively who want the environment set up for them.*

We have provided a robust bash script that handles Python virtual environments, dependencies, and model fetching.

1.  **Run the Setup Script**:
    ```bash
    ./setup.sh
    ```
    *This script will:*
    * Create a hidden `.venv` (Virtual Environment).
    * Install all Python dependencies.
    * Install Playwright browsers (for scraping dynamic JS sites).
    * Check for `ollama` and pull the `phi3` model.

2.  **Start the Platform**:
    ```bash
    ./start.sh
    ```

---

### Method 4: Manual "Hacker" Setup
*Best for: Enthusiasts who want to understand every moving part.*

If you prefer full control over the installation, follow these steps:

**1. System Dependencies**
Ensure you have the necessary system libraries for document processing:
```bash
# Arch Linux
sudo pacman -S python-pip tesseract poppler

# Ubuntu/Debian
sudo apt-get install python3-pip tesseract-ocr poppler-utils
````

**2. Python Environment**
Create and activate a virtual environment to keep your system clean:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

**3. Install Libraries**
Install the Python requirements:

```bash
pip install -r requirements.txt
```

**4. Install Headless Browser**
The scraper uses Playwright to render JavaScript-heavy security blogs:

```bash
playwright install chromium
```

**5. Setup the AI Model**
You must have [Ollama](https://ollama.com/) installed and running.

```bash
# In a separate terminal
ollama serve

# Pull the specific model used by our config
ollama pull phi3
```

**6. Launch Services**
You need to run the components in this specific order:

1.  **Producer** (Scrapes data)
2.  **Pipeline** (Processes data & Vector Store)
3.  **Web Dashboard** (Flask Server)
4.  **CLI/TUI** (User Interface)

You can use the provided orchestrator to do this in one go:

```bash
./start.sh
```

-----

## 🔮 Future Scope

This project is just the beginning of autonomous cyber-intelligence.

1.  **Kubernetes Scaling**: Migrating the Docker Compose setup to a K8s Helm Chart for high-availability deployment.
2.  **Dark Web Scrapers**: Integrating Tor proxy support to scrape .onion sites for leak data.
3.  **Fine-tuned Models**: Replacing the generic `phi3` with a Llama-3 version fine-tuned specifically on CVE databases and exploit logs.
4.  **Agentic Capabilities**: Allowing the AI to not just *read* news, but proactively scan local logs based on new threat intel.

-----

## 🤝 Contributing

We welcome fellow engineers and hackers\!

  * **Add Sources**: Check `producer.py` to add new RSS feeds or URL targets.
  * **Optimize Pipeline**: Help us refine the `pipeline.py` Pathway logic for lower latency.
  * **UI Polish**: The Web Dashboard (`dashboard_web.py`) could use a React frontend.

**To Contribute:**

1.  Fork the repo.
2.  Create your feature branch (`git checkout -b feature/AmazingFeature`).
3.  Commit your changes.
4.  Push to the branch.
5.  Open a Pull Request.

-----
