# Dockerfile

# 1. Pick a lightweight base image
FROM python:3.11-slim

# 2. Set a working directory
WORKDIR /app

# 3. Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. Copy your application code
COPY app.py .
COPY forecast_service.py .         # or forecast_service.py, whichever you use

# 5. Expose the port your Flask app listens on
EXPOSE 5000

# 6. Launch via Gunicorn
CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:5000", "--workers", "3"]
