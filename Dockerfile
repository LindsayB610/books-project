# Dockerfile for Books API
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (for better caching)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Set environment variable (can be overridden)
ENV BOOKS_DATASET=datasets/lindsay

# Expose port
EXPOSE 8000

# Run the application
CMD ["uvicorn", "api.server:app", "--host", "0.0.0.0", "--port", "8000"]

