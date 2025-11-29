# KERNEL PANIC - Cyber Security Intelligence Platform

This project is a comprehensive cyber security intelligence platform that scrapes data from various sources, processes it in real-time, and provides a multi-interface dashboard for threat analysis.

## Features

- **Real-time Scraping**: A producer script (`producer.py`) continuously scrapes high-value security websites and feeds the data into the system.
- **Real-time Analytics**: A Pathway ML pipeline (`pipeline.py`) processes the raw text, filters for security-specific keywords, and calculates real-time threat statistics.
- **RAG-based Q&A**: The Pathway pipeline also serves a Retrieval-Augmented Generation (RAG) API, allowing users to ask natural language questions about the ingested data.
- **Multiple Frontends**:
    - **Web Dashboard (`dashboard_web.py`)**: A Flask-based web interface for monitoring threats and chatting with the AI.
    - **CLI Dashboard (`dashboard_cli.py`)**: A lightweight, terminal-based interface for interacting with the system.
    - **TUI Dashboard (`dashboard.py`)**: The original Textual-based user interface.

## Docker Usage (Recommended)

This setup uses Docker Compose to orchestrate all the necessary services, including the Ollama LLM, the data pipeline, and the user interfaces. The application image is available on Docker Hub.

### Prerequisites

- Docker installed and running.
- Docker Compose installed.

### How to Run

1.  **Clone the Repository**:
    If you haven't already, clone this repository to get the `docker-compose.yml` and `README.md` files.
    ```bash
    git clone <repository-url>
    cd cyber-news
    ```

2.  **Start the Services**:
    Open a terminal in the project's root directory and run:
    ```bash
    docker-compose up
    ```
    - This command will:
        - Pull the official `ollama` image.
        - Pull the `imajaygiri/cyber-news:latest` application image from Docker Hub.
        - Run a helper container to download the `phi3` LLM model (this can take several minutes the first time).
        - Start all services and connect them on an internal Docker network.

3.  **Access the Dashboards**:
    - Once the services are running, you will see the output from the **CLI Dashboard** directly in your terminal. You can start typing commands here immediately.
    - To access the **Web Dashboard**, open your browser and navigate to:
      [**http://localhost:5001**](http://localhost:5001)

4.  **Interacting with the CLI**:
    - The `docker-compose up` command will attach your terminal to the running container's CLI.
    - Simply type queries and press Enter.
    - To see a list of available commands in the CLI, type `/help`.

5.  **Stopping the Application**:
    - To stop all services, press `Ctrl+C` in the terminal where `docker-compose up` is running.
    - To clean up and remove the containers and network, run:
    ```bash
    docker-compose down
    ```

### Port Mapping

- **Web UI**: `5001` (Host) -> `5001` (Container)
- **RAG API**: `9000` (Host) -> `9000` (Container)
- **Ollama API**: `11434` (Host) -> `11434` (Container)
