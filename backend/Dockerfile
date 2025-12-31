# 1. Base Image: Use a lightweight, official Python runtime
# 'slim' means it has no extra bloatware, making it smaller and faster.
FROM python:3.10-slim

# 2. Setup: Set the working directory inside the container
WORKDIR /app

# 3. Optimization: Copy ONLY requirements first
# This allows Docker to "cache" the installation step. 
# If you change your code but not your libraries, Docker won't re-install everything.
COPY requirements.txt .

# 4. Install: Install dependencies
# --no-cache-dir keeps the image small
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copy Code: Copy the rest of your application code
COPY . .

# 6. Network: Tell Docker we are listening on port 8000
EXPOSE 8000

# 7. Run: The command to start the server
# host 0.0.0.0 is CRITICAL in Docker (unlike 127.0.0.1 locally)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]