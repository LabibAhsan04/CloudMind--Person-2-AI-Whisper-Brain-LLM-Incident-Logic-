# ---------------------------
# Dockerfile for CloudMind (Person 2)
# ---------------------------

# Base lightweight Python image
FROM python:3.11-slim

# Set the working directory inside the container
WORKDIR /app

# Copy dependency list and install requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all source files (main.py, etc.)
COPY . .

# Expose FastAPI port
EXPOSE 8000

# Start your FastAPI app
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
