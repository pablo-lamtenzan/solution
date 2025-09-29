# Use Python 3.11 slim image as base
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv for fast Python package management
RUN pip install uv

# Copy the entire project first (needed for local package build)
COPY . .

# Install Python dependencies using uv
RUN uv sync --frozen

# Create a non-root user for security
RUN useradd --create-home --shell /bin/bash app \
    && chown -R app:app /app
USER app

# Expose the port your application runs on (customize as needed)
EXPOSE 8000

# Health check (customize the endpoint for your application)
# HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
#     CMD curl -f http://localhost:8000/health || exit 1

# Default command (customize for your application)
# Examples:
# CMD ["uv", "run", "python", "-m", "your_package.server"]
# CMD ["uv", "run", "uvicorn", "your_package.main:app", "--host", "0.0.0.0", "--port", "8000"]
# CMD ["uv", "run", "streamlit", "run", "app.py", "--server.address", "0.0.0.0", "--server.port", "8000"]
CMD ["uv", "run", "python", "-c", "print('Configure your application command in Dockerfile')"]
