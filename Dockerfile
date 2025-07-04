# Dockerfile

# 1) Base image
FROM python:3.9-slim

# 2) Set working dir
WORKDIR /app

# 3) Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4) Copy all your code
COPY . .

# 5) Expose the port your Flask app listens on
EXPOSE 5000

# 6) Use Gunicorn for production‑grade serving
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]
