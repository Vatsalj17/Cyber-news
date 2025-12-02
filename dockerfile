FROM python:3.11.7

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
# - iproute2: Required for 'ss' command in start.sh (Port check)
# - procps: Required for 'pkill' command in start.sh (Cleanup)
# - libgl1/libglib: Required for OpenCV/Headless Browsers
# - poppler/tesseract: Required for pdf2image/unstructured
# - tini: For proper process signal handling (Ctrl+C support)

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    LLM_MODEL="phi3"

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

RUN playwright install --with-deps chromium

COPY . .

RUN chmod +x start.sh setup.sh

ENTRYPOINT ["/usr/bin/tini", "--"]
CMD ["./start.sh"]
