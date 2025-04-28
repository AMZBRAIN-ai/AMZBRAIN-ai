# 1) Start from Playwright’s official Python image
FROM mcr.microsoft.com/playwright/python:latest

# 2) Set working directory
WORKDIR /app

# 3) Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 4) Copy your FastAPI app code
COPY . .

# 5) Install Playwright dependencies and Chromium browser
RUN playwright install-deps && playwright install chromium

# 6) Expose the app port
EXPOSE 3000

# 7) Start the FastAPI server
CMD uvicorn main:app --host 0.0.0.0 --port 3000
