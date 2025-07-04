# 1. Base image
FROM python:3.11-slim

# 2. Set working dir
WORKDIR /app

# 3. Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. Copy code
COPY app.py .
COPY forecast_service.py .

# 5. Expose Flask’s default port
EXPOSE 5000

# 6. Use gunicorn for production
CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:5000", "--workers", "3"]
