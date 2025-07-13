# Indonesian Mental Health Support Bot - Docker Configuration
# Based on Python 3.10 slim image for optimal performance

FROM python:3.10-slim

# Set environment variables for optimal container operation
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV DEBIAN_FRONTEND=noninteractive
# Audio optimization for container environment
ENV ALSA_CARD=-1
ENV ALSA_DEVICE=0
# Mental health bot specific settings
ENV TZ=Asia/Jakarta
ENV LANG=C.UTF-8

# Set work directory
WORKDIR /app

# Install system dependencies for audio processing and Indonesian language support
# Install PyAudio via system packages to avoid compilation issues
RUN apt-get update && apt-get install -y \
    portaudio19-dev \
    python3-pyaudio \
    gcc \
    g++ \
    make \
    libasound2-dev \
    libportaudio2 \
    libportaudiocpp0 \
    ffmpeg \
    curl \
    build-essential \
    python3-dev \
    pkg-config \
    alsa-utils \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better Docker layer caching
COPY requirements.txt .

# Install Python dependencies with better error handling and dependency resolution
RUN python -m pip install --no-cache-dir --upgrade pip setuptools wheel

# Install core dependencies first to resolve conflicts
RUN pip install --no-cache-dir \
    typing-extensions==4.8.0 \
    pydantic==2.5.0 \
    httpx==0.25.2 \
    requests \
    sniffio \
    anyio \
    distro \
    tqdm

# Install PyAudio using system packages
RUN pip install --no-cache-dir --no-build-isolation pyaudio==0.2.14

# Install remaining dependencies
RUN pip install --no-cache-dir \
    fastapi==0.104.1 \
    uvicorn[standard]==0.24.0 \
    python-multipart==0.0.6 \
    jinja2==3.1.2 \
    aiofiles==23.2.1 \
    openai==1.91.0 \
    anthropic==0.40.0 \
    pygame==2.5.2 \
    python-dotenv==1.0.0 \
    pydub==0.25.1 \
    numpy \
    pandas \
    pathlib2

# Copy application files (including .env file if it exists)
COPY . .

# Ensure .env file exists with proper permissions
# If no .env file is found, create one from env.template as a fallback
RUN if [ ! -f .env ] && [ -f env.template ]; then \
        echo "No .env file found, creating from template..."; \
        cp env.template .env; \
        echo "Warning: Using template .env file. Please update with your actual API key."; \
    fi

# Create necessary directories for the mental health bot
RUN mkdir -p static templates __pycache__ && \
    chmod 755 static templates

# Create a non-root user for security (mental health data protection)
RUN useradd -m -u 1000 mentalhealthbot && \
    chown -R mentalhealthbot:mentalhealthbot /app && \
    chmod +x test_mental_health_bot.py deploy.sh docker-check.sh 2>/dev/null || true
USER mentalhealthbot

# Expose port for the mental health support interface
EXPOSE 8000

# Health check for mental health bot service
HEALTHCHECK --interval=30s --timeout=15s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Set labels for the Indonesian Mental Health Support Bot
LABEL maintainer="Indonesian Mental Health Support Team"
LABEL description="Kak Indira - Indonesian Mental Health Support Chatbot"
LABEL version="1.0.0"
LABEL app="indonesian-mental-health-bot"

# Default command to start the mental health support bot
CMD ["python", "app.py"] 