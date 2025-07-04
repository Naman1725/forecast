# Dockerfile

# 1. Pick a lightweight base image
FROM python:3.11-slim

# 2. Set a working directory
WORKDIR /app

# 3. Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. Copy your application code
COPY forecast_service.py .
COPY main.py .

# 5. Expose the port your FastAPI app will run on
EXPOSE 8000

# 6. Start the server with Uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
