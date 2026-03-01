# Use Python 3.11 as the base image
FROM python:3.11-slim

# Install system dependencies required for Chromium/Puppeteer (used by Browser Use)
RUN apt-get update && apt-get install -y \
    chromium \
    chromium-driver \
    libglib2.0-0 \
    libnss3 \
    libexpat1 \
    libfontconfig1 \
    libuuid1 \
    wget \
    gnupg \
    && rm -rf /var/lib/apt/lists/*

# Set environment variables for Chromium
ENV CHROME_BIN=/usr/bin/chromium
ENV PUPPETEER_SKIP_CHROMIUM_DOWNLOAD=true

# Set working directory
WORKDIR /app

# Copy requirement files first for efficient caching
COPY logic_agent/requirements.txt /app/logic_agent_requirements.txt
COPY fixer/requirements.txt /app/fixer_requirements.txt

# Install dependencies for both Logic/UI Agents and Fixer API
RUN pip install --no-cache-dir -r /app/logic_agent_requirements.txt \
    && pip install --no-cache-dir -r /app/fixer_requirements.txt \
    && pip install playwright \
    && playwright install --with-deps chromium

# Copy the rest of the application files
COPY logic_agent /app/logic_agent
COPY ui_agent /app/ui_agent
COPY fixer /app/fixer
COPY agent /app/agent
COPY .env /app/.env

# The default command will be overridden by render.yaml for each service
CMD ["python", "logic_agent/api.py"]
