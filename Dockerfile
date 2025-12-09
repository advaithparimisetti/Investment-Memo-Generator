FROM python:3.11-slim

WORKDIR /app

# Install dependencies
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 1. Create the non-root user
RUN useradd -m appuser

# 2. Copy the files (They will be owned by root initially)
COPY . .

# 3. Change ownership of the /app directory to the new user
# This allows the app to write the database file yfinance.cache.sqlite
RUN chown -R appuser:appuser /app

# 4. Switch to the non-root user
USER appuser

EXPOSE 8000
CMD ["uvicorn", "backend:app", "--host", "0.0.0.0", "--port", "8000"]
