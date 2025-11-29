FROM python:3.11.7

# 1. Install System Tools
# - iproute2: Required for 'ss' command in start.sh (Port check)
# - procps: Required for 'pkill' command in start.sh (Cleanup)
# - libgl1/libglib: Required for OpenCV/Headless Browsers
# - poppler/tesseract: Required for pdf2image/unstructured
# - tini: For proper process signal handling (Ctrl+C support)
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    iproute2 \
    procps \
    libgl1 \
    libglib2.0-0 \
    poppler-utils \
    tesseract-ocr \
    tini \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 2. Config
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    LLM_MODEL="phi3"

# 3. Copy requirements file
COPY requirements.txt .

# 4. Install Python Deps
RUN pip install --no-cache-dir -r requirements.txt

# 5. Install Browsers (Chromium for the Scraper)
RUN playwright install --with-deps chromium

# 6. Copy Code
COPY . .

# 7. Permissions
RUN chmod +x start.sh setup.sh

# 8. Entrypoint
ENTRYPOINT ["/usr/bin/tini", "--"]
CMD ["./start.sh"]
