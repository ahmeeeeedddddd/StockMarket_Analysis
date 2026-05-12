FROM python:3.11-slim

WORKDIR /app

# Copy the backend requirements file from the root context
COPY backend/requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend and shared folders
COPY backend/ ./backend/
COPY shared/ ./shared/

# Set Python path so it can import from dashboard and shared
ENV PYTHONPATH=/app

EXPOSE 8000

# Start the FastAPI server via Uvicorn
CMD ["uvicorn", "backend.api:app", "--host", "0.0.0.0", "--port", "8000"]
